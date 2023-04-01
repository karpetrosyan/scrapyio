import typing
from abc import ABC
from abc import abstractmethod

from scrapyio.items import Item


class BaseItemMiddleWare(ABC):
    @abstractmethod
    async def process_item(self, item: Item) -> typing.Union[Item, None]:
        ...
