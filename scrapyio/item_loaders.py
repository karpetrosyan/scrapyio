import typing
from abc import ABC
from abc import abstractmethod
from enum import Enum
from enum import auto

from .utils import random_filename

if typing.TYPE_CHECKING:
    from scrapyio.items import Item


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


class JSONLoader(BaseLoader):
    def __init__(self, filename: typing.Optional[str] = None):
        super().__init__()
        self.filename = filename or random_filename()
        self.file: typing.Optional[typing.TextIO] = None
        self.first_item: bool = True

    async def open(self) -> None:
        self.state = LoaderState.OPENED
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
        self.state = LoaderState.CLOSED


# TODO: Implement CSVLoader
# TODO: Implement MONGOLoader
# TODO: Implement SQLiteLoader
