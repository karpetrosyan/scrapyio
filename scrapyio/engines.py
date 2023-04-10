import asyncio
import inspect
import logging
import typing
from warnings import warn

from scrapyio import Request
from scrapyio.downloader import BaseDownloader
from scrapyio.downloader import Downloader
from scrapyio.http import clean_up_response
from scrapyio.items import ItemManager
from scrapyio.spider import BaseSpider
from scrapyio.spider import Item
from scrapyio.types import CLEANUP_WITH_RESPONSE
from scrapyio.types import DOWNLOADER_EXCEPTION_CALLBACK

log = logging.getLogger("scrapyio")


class Engine:
    downloader_class: typing.ClassVar[typing.Type[BaseDownloader]] = Downloader

    def __init__(
        self,
        spider: BaseSpider,
        downloader: typing.Optional[BaseDownloader] = None,
        items_manager: typing.Optional[ItemManager] = None,
        loop_delay: int = 0,
        downloader_exception_callback: typing.Optional[
            DOWNLOADER_EXCEPTION_CALLBACK
        ] = None,
    ):
        self.spider = spider
        self.loop_delay = loop_delay

        self.downloader: BaseDownloader
        if downloader is None:
            self.downloader = self.downloader_class()
        else:
            self.downloader = downloader

        self.downloader_exception_callback = downloader_exception_callback
        self.items_manager = items_manager
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
        async with asyncio.TaskGroup() as tg:
            for request in self.spider.requests:
                request_tasks.append(tg.create_task(
                    self._send_single_request_to_downloader(request=request)
                ))
        self.spider.requests.clear()
        return [
            request_task.result() for request_task in request_tasks
        ]

    async def _handle_single_response(
        self, response_and_generator: CLEANUP_WITH_RESPONSE
    ) -> None:
        if not inspect.isasyncgenfunction(self.spider.parse):
            raise TypeError(
                "Spider's `parse` must be an asynchronous generator function"
            )
        clean_up_generator, response = response_and_generator
        gen = self.spider.parse(response=response)
        async for yielded_value in gen:
            if isinstance(yielded_value, Request):
                self.spider.requests.append(yielded_value)
            elif isinstance(yielded_value, Item):
                self.spider.items.append(yielded_value)  # pragma: no cover
            elif yielded_value is None:  # pragma: no cover
                ...  # pragma: no cover
            else:
                raise TypeError(
                    "Invalid type yielded, expected `Request` or `Item` got `%s`"
                    % yielded_value.__class__.__name__
                )

    async def _handle_responses(
        self, responses: typing.List[CLEANUP_WITH_RESPONSE]
    ) -> None:
        tasks = []
        async with asyncio.TaskGroup() as tg:
            for response in responses:
                tasks.append(
                    tg.create_task(
                        self._handle_single_response(response_and_generator=response)
                    )
                )

    async def _run_once(self) -> None:
        log.debug("Running engine once")
        responses = await self._send_all_requests_to_downloader()
        try:
            log.debug("Handling the responses")
            await self._handle_responses(responses=responses)
            if self.items_manager:
                log.debug("Processing the items")
                await self.items_manager.process_items(self.spider.items)
            log.debug("Clear spider items after processing")
            self.spider.items.clear()
        finally:
            for gen, response in responses:
                log.debug("Cleaning up the responses")
                await clean_up_response(gen)

    async def _tear_down(self) -> None:
        log.debug("Tear down was called")
        if self.items_manager:
            log.info(f"Closing the opened loaders: {self.items_manager.loaders=}")
            await self.items_manager.tear_down_loaders()

    async def run(self) -> None:
        try:
            while self.spider.requests:
                await self._run_once()
                await asyncio.sleep(self.loop_delay)
        finally:
            log.info("Calling tear down on engine")
            await self._tear_down()
