import typing
import warnings
from abc import ABC
from abc import abstractmethod
from asyncio import Lock
from datetime import datetime
from enum import Enum
from enum import auto

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import insert
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine

from .utils import random_filename

if typing.TYPE_CHECKING:
    from scrapyio.items import Item

import csv
import logging

log = logging.getLogger("scrapyio")


class LoaderState(Enum):
    CREATED = auto()
    OPENED = auto()
    DUMPING = auto()
    CLOSED = auto()


class BaseLoader(ABC):
    @abstractmethod
    async def open(self) -> None:
        ...

    @abstractmethod
    async def dump(self, item: "Item") -> None:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...


class ProxyLoader:
    def __init__(self, loader: BaseLoader):
        self.state: LoaderState = LoaderState.CREATED
        self.loader = loader

    async def open(self) -> None:
        if self.state == LoaderState.OPENED:
            raise RuntimeError("Cannot open a loader that has already been opened.")
        elif self.state == LoaderState.CLOSED:
            raise RuntimeError(
                "It is not possible to reopen a loader that has already been closed."
            )
        elif self.state == LoaderState.DUMPING:
            raise RuntimeError(
                "Cannot open a loader that is already in the dumping state."
            )
        elif self.state == LoaderState.CREATED:
            log.info(f"Setting up the `{self.__class__.__name__}`")
            self.state = LoaderState.OPENED
            await self.loader.open()

    async def dump(self, item: "Item") -> None:
        if self.state == LoaderState.CLOSED:
            raise RuntimeError(
                "It is not possible to dump a pydantic "
                "object after the loader has been closed."
            )
        elif self.state == LoaderState.CREATED:
            raise RuntimeError(
                "The newly created loader cannot dump an object; it must be opened."
            )
        else:
            self.state = LoaderState.DUMPING
            await self.loader.dump(item=item)

    async def close(self) -> None:
        if self.state == LoaderState.CLOSED:
            raise RuntimeError("Loader cannot be closed because it is already closed.")
        elif self.state == LoaderState.CREATED:
            raise RuntimeError(
                "The loader cannot be closed because it has not yet been opened."
            )
        elif self.state == LoaderState.OPENED:
            msg = "Closing the loader without dumping items"
            log.warning("Closing the loader without dumping items")
            warnings.warn(category=RuntimeWarning, message=msg)
        log.info(f"Closing the `{self.__class__.__name__}`")
        await self.loader.close()
        self.state = LoaderState.CLOSED


class JSONLoader(BaseLoader):
    def __init__(self, filename: typing.Optional[str] = None):
        super().__init__()
        self.filename = filename or random_filename()
        self.file: typing.Optional[typing.TextIO] = None
        self.first_item: bool = True

    async def open(self) -> None:
        self.file = open(self.filename, mode="w", encoding="utf-8")
        self.file.write("[\n")

    async def dump(self, item: "Item") -> None:
        assert self.file
        serialized_item = item.json()
        if not self.first_item:
            self.file.write(",\n" + serialized_item)
        else:
            self.file.write(serialized_item)
            self.first_item = False

    async def close(self) -> None:
        assert self.file
        self.file.write("\n]")
        self.file.close()


class CSVLoader(BaseLoader):
    def __init__(self, filename: typing.Optional[str] = None):
        super().__init__()
        self.filename = filename or random_filename()
        self.file: typing.Optional[typing.TextIO] = None
        self.first_item: bool = True
        self.writer: typing.Optional[csv.DictWriter] = None

    async def open(self) -> None:
        self.file = open(self.filename, "w", encoding="utf-8")

    async def dump(self, item: "Item") -> None:
        assert self.file
        if self.first_item:
            self.first_item = False
            fieldnames = list(item.__class__.schema()["properties"].keys())
            writer = csv.DictWriter(self.file, fieldnames=fieldnames)
            self.writer = writer
            writer.writeheader()
        assert self.writer, "Trying to use csv.DictWriter which is None"
        self.writer.writerow(item.dict())

    async def close(self) -> None:
        assert self.file
        self.file.close()


class SQLAlchemyLoader(BaseLoader):
    mapped_fields = {int: Integer, str: String, float: Float, datetime: DateTime}

    def __init__(self, url: typing.Union[URL, str]):
        super().__init__()
        self.url = url
        self.engine: typing.Optional[AsyncEngine] = None
        self.lock = Lock()
        self.meta = MetaData()
        self.existing_tables: typing.Dict[str, Table] = {}
        self.conn: typing.Optional[AsyncConnection] = None
        log.debug(f"`{self.__class__.__name__}` instance was created")

    async def _create_table_from_item(self, item: "Item") -> None:
        table = Table(
            item.__class__.__name__,
            self.meta,
            Column("id", Integer, primary_key=True),
            *(await self._get_mapped_fields(item=item)),
            extend_existing=True,
        )
        assert self.engine
        async with self.engine.connect() as conn:
            await conn.run_sync(self.meta.create_all)
        self.existing_tables[item.__class__.__name__] = table

    async def _get_mapped_fields(self, item: "Item") -> typing.List[Column]:
        model: typing.Type["Item"] = item.__class__
        fields = model.__fields__.items()
        columns: typing.List[Column] = []

        for field_name, model_field in fields:
            field_type = model_field.type_
            sqlalchemy_type = self.mapped_fields[field_type]
            # TODO: handle not supported types
            new_column: Column = Column(field_name, sqlalchemy_type)
            columns.append(new_column)

        return columns

    async def open(self) -> None:
        log.debug("Creating sqlalchemy async engine")
        self.engine = create_async_engine(url=self.url)
        self.conn = await self.engine.connect()

    async def dump(self, item: "Item") -> None:
        pydantic_model_name = item.__class__.__name__
        async with self.lock:
            if pydantic_model_name not in self.existing_tables:
                log.debug(f"`Creating the {pydantic_model_name} Table`")
                await self._create_table_from_item(item=item)
                log.debug(f"`{pydantic_model_name} Table was created`")
        table = self.existing_tables[pydantic_model_name]
        stmt = insert(table=table).values(item.dict())
        assert self.conn
        await self.conn.execute(stmt)

    async def close(self) -> None:
        assert self.conn
        await self.conn.commit()
        await self.conn.close()
        assert self.engine
        await self.engine.dispose()


# TODO: Implement MONGOLoader
