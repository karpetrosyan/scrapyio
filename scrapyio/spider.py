import asyncio
import typing
from abc import ABC
from abc import abstractmethod

from httpx._client import Response

from .downloader import BaseDownloader
from .downloader import Downloader
from .http import Request
from .http import clean_up_response
from .settings import load_settings
from .types import CLEANUP_WITH_RESPONSE


class Item:
    ...


class BaseSpider(ABC):
    start_requests: typing.ClassVar[typing.List[Request]] = []

    def __init__(self):
        self.requests = self.start_requests  # pragma: no cover
        self.items: typing.List[Item] = []  # pragma: no cover

    @abstractmethod
    async def parse(
        self, response: Response
    ) -> typing.AsyncGenerator[typing.Union[Request, Item], None]:
        if False:
            yield Request()


class Engine:
    downloader_class: typing.ClassVar[typing.Type[BaseDownloader]] = Downloader

    def __init__(self, spider_class: typing.Type[BaseSpider]):
        load_settings()
        self.downloader: BaseDownloader = self.downloader_class()
        self.spider = spider_class()

    async def _send_single_request_to_downloader(
        self, request: Request
    ) -> typing.Optional[CLEANUP_WITH_RESPONSE]:
        return await self.downloader.handle_request(request=request)

    async def _send_all_requests_to_downloader(
        self,
    ) -> typing.Iterable[CLEANUP_WITH_RESPONSE]:
        request_tasks: typing.List[typing.Awaitable] = []
        for request in self.spider.requests:
            request_tasks.append(
                asyncio.create_task(
                    self._send_single_request_to_downloader(request=request)
                )
            )
        self.spider.requests.clear()
        responses: typing.Iterable[
            typing.Optional[CLEANUP_WITH_RESPONSE]
        ] = await asyncio.gather(
            *request_tasks
        )  # type: ignore
        return [response for response in responses if response]

    async def _handle_single_response(
        self, response_and_generator: CLEANUP_WITH_RESPONSE
    ) -> None:
        clean_up_generator, response = response_and_generator
        try:
            gen = self.spider.parse(response=response)
            async for yielded_value in gen:
                if isinstance(yielded_value, Request):
                    self.spider.requests.append(yielded_value)
                elif isinstance(yielded_value, Item):
                    self.spider.items.append(yielded_value)
                else:
                    raise TypeError(
                        "Invalid type yielded, expected `Request` or `Item` got `%s`"
                        % yielded_value.__class__.__name__
                    )
        finally:
            await clean_up_response(clean_up_generator)

    async def _handle_responses(
        self, responses: typing.Iterable[CLEANUP_WITH_RESPONSE]
    ) -> None:
        tasks = [
            asyncio.create_task(self._handle_single_response(response))
            for response in responses
        ]
        await asyncio.gather(*tasks)

    async def run(self):
        while self.spider.requests:
            responses = await self._send_all_requests_to_downloader()
            await self._handle_responses(responses=responses)
