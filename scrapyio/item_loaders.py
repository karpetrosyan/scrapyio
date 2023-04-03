import typing
from abc import ABC
from abc import abstractmethod
from enum import Enum
from enum import auto

from .utils import random_filename

if typing.TYPE_CHECKING:
    from scrapyio.items import Item

import csv


class LoaderState(Enum):
    CREATED = auto()
    OPENED = auto()
    CLOSED = auto()


class BaseLoader(ABC):
    def __init__(self):
        self.state: LoaderState = LoaderState.CREATED

    @abstractmethod
    async def open(self) -> None:
        ...

    @abstractmethod
    async def dump(self, item: "Item") -> None:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...

    async def _open(self, *args, **kwargs) -> None:
        self.state = LoaderState.OPENED
        await self.open(*args, **kwargs)

    async def _close(self, *args, **kwargs) -> None:
        await self.close(*args, **kwargs)
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
        assert self.file, "Loader's `dump` was called before `open` method"
        serialized_item = item.json()
        if not self.first_item:
            self.file.write(",\n" + serialized_item)
        else:
            self.file.write(serialized_item)
            self.first_item = False

    async def close(self) -> None:
        assert self.file, "Loader's `close` was called before `open` method"
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
        assert self.file, "Loader's `dump` was called before `open` method"
        if self.first_item:
            self.first_item = False
            fieldnames = list(item.__class__.schema()["properties"].keys())
            writer = csv.DictWriter(self.file, fieldnames=fieldnames)
            self.writer = writer
            writer.writeheader()
        assert self.writer, "Trying to use csv.DictWriter which is None"
        self.writer.writerow(item.dict())

    async def close(self) -> None:
        assert self.file, "Loader's `close` was called before `open` method"
        self.file.close()


# TODO: Implement MONGOLoader
# TODO: Implement SQLiteLoader
