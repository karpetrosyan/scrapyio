import asyncio
import inspect
import typing
from warnings import warn

from scrapyio import Request
from scrapyio.downloader import BaseDownloader
from scrapyio.downloader import Downloader
from scrapyio.http import clean_up_response
from scrapyio.item_loaders import BaseLoader
from scrapyio.items import ItemManager
from scrapyio.settings import load_settings
from scrapyio.spider import BaseSpider
from scrapyio.spider import Item
from scrapyio.types import CLEANUP_WITH_RESPONSE

from .utils import first_not_none


class Engine:
    downloader_class: typing.ClassVar[typing.Type[BaseDownloader]] = Downloader
    items_manager_class: typing.ClassVar[
        typing.Optional[typing.Type[ItemManager]]
    ] = None
    loader_class: typing.ClassVar[typing.Optional[typing.Type[BaseLoader]]] = None

    def __init__(
        self,
        spider_class: typing.Type[BaseSpider],
        downloader_class: typing.Optional[typing.Type[BaseDownloader]] = None,
        items_manager_class: typing.Optional[typing.Type[ItemManager]] = None,
        enable_settings: bool = True,
    ):
        if enable_settings:
            load_settings()  # pragma: no cover
        downloader_class = first_not_none(downloader_class, self.downloader_class)
        items_manager_class = first_not_none(
            items_manager_class, self.items_manager_class
        )

        self.downloader: BaseDownloader = downloader_class()
        self.spider = spider_class()
        self.items_manager: typing.Optional[ItemManager] = (
            items_manager_class() if items_manager_class else None
        )

        if self.items_manager is None:
            warn(
                "Because no `items_manager` was specified, all items"
                " yielded by the 'parse' method will be ignored.",
                RuntimeWarning,
            )

    async def _send_single_request_to_downloader(
        self, request: Request
    ) -> typing.Optional[CLEANUP_WITH_RESPONSE]:
        return await self.downloader.handle_request(request=request)

    async def _send_all_requests_to_downloader(
        self,
    ) -> typing.List[CLEANUP_WITH_RESPONSE]:
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
        if not inspect.isasyncgenfunction(self.spider.parse):
            raise TypeError(
                "Spider's `parse` must be an asynchronous generator function"
            )
        clean_up_generator, response = response_and_generator
        try:
            gen = self.spider.parse(response=response)
            async for yielded_value in gen:
                if isinstance(yielded_value, Request):
                    self.spider.requests.append(yielded_value)
                elif isinstance(yielded_value, Item):
                    self.spider.items.append(yielded_value)  # pragma: no cover
                elif yielded_value is None:
                    ...
                else:
                    raise TypeError(
                        "Invalid type yielded, expected `Request` or `Item` got `%s`"
                        % yielded_value.__class__.__name__
                    )
        finally:
            await clean_up_response(clean_up_generator)

    async def _handle_responses(
        self, responses: typing.List[CLEANUP_WITH_RESPONSE]
    ) -> None:
        tasks = [
            asyncio.create_task(self._handle_single_response(response))
            for response in responses
        ]
        await asyncio.gather(*tasks)

    async def run_once(self):
        responses = await self._send_all_requests_to_downloader()
        await self._handle_responses(responses=responses)
        if self.items_manager:
            await self.items_manager.process_items(self.spider.items)

        self.spider.items.clear()

    async def run(self):
        while self.spider.requests:
            await self.run_once()
