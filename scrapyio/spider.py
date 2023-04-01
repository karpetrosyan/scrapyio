import typing
from abc import ABC
from abc import abstractmethod

from httpx._client import Response

from .http import Request
from .items import Item


class BaseSpider(ABC):
    start_requests: typing.ClassVar[typing.List[Request]] = []

    def __init__(self):
        self.requests = self.start_requests  # pragma: no cover
        self.items: typing.List[Item] = []  # pragma: no cover

    @abstractmethod
    async def parse(
        self, response: Response
    ) -> typing.AsyncGenerator[typing.Union[Request, Item, None], None]:
        if False:
            yield Request()
