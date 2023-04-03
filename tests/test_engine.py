import tempfile
import typing
from pathlib import Path
from warnings import catch_warnings

import pytest

from scrapyio import Request
from scrapyio import Response
from scrapyio.downloader import Downloader
from scrapyio.downloader import SessionDownloader
from scrapyio.engines import Engine
from scrapyio.item_loaders import JSONLoader
from scrapyio.item_loaders import LoaderState
from scrapyio.items import Item
from scrapyio.items import ItemManager
from scrapyio.spider import BaseSpider


@pytest.mark.anyio
async def test_engine_request_handling(app):
    class Spider(BaseSpider):
        start_requests = [
            Request(url="/", base_url="https://example.com", method="GET", app=app)
        ]

        async def parse(self, response):
            raise NotImplementedError

    engine = Engine(spider_class=Spider, enable_settings=False)
    response_with_cleanup = await engine._send_single_request_to_downloader(
        Request(url="/", base_url="https://example.com", method="GET", app=app)
    )
    assert response_with_cleanup
    _, response = response_with_cleanup
    assert response.status_code == 200
    assert len(engine.spider.requests) == 1
    responses_with_clean_ups = await engine._send_all_requests_to_downloader()
    assert len(responses_with_clean_ups) == 1
    _, response = responses_with_clean_ups[0]
    assert response.status_code == 200


@pytest.mark.anyio
async def test_engine_response_handling(app):
    test_list = []

    class Spider(BaseSpider):
        start_requests = [
            Request(url="/", base_url="https://example.com", method="GET", app=app)
        ]

        async def parse(self, response):
            test_list.append(response.text)
            yield None

    engine = Engine(spider_class=Spider, enable_settings=False)
    responses = await engine._send_all_requests_to_downloader()
    await engine._handle_responses(responses=responses)
    assert len(test_list) == 1


@pytest.mark.anyio
async def test_engine_sync_parser_error(app):
    class Spider(BaseSpider):
        start_requests = [
            Request(url="/", base_url="https://example.com", method="GET", app=app)
        ]

        def parse(self, response):
            raise NotImplementedError

    engine = Engine(spider_class=Spider, enable_settings=False)
    with pytest.raises(TypeError, match="Spider's `parse`.*"):
        await engine.run()


@pytest.mark.anyio
async def test_engine_parser_invalid_yield_value(app):
    class Spider(BaseSpider):
        start_requests = [
            Request(url="/", base_url="https://example.com", method="GET", app=app)
        ]

        async def parse(self, response):
            yield 5

    engine = Engine(spider_class=Spider, enable_settings=False)
    with pytest.raises(TypeError, match="Invalid type yielded,.*"):
        await engine.run()


@pytest.mark.anyio
async def test_engine_parser_yield_request(app):
    class Spider(BaseSpider):
        start_requests = [
            Request(url="/", base_url="https://example.com", method="GET", app=app)
        ]

        async def parse(self, response):
            yield Request(
                url="/", base_url="https://example.com", method="GET", app=app
            )

    engine = Engine(spider_class=Spider, enable_settings=False)
    responses = await engine._send_all_requests_to_downloader()
    assert engine.spider.requests == []
    await engine._handle_responses(responses)
    assert len(engine.spider.requests) == 1


def test_engine_configs():
    class FakeSpider:
        ...

    class MyEngine(Engine):
        items_manager_class = ItemManager
        downloader_class = SessionDownloader

    session_engine = MyEngine(spider_class=FakeSpider, enable_settings=False)
    assert isinstance(session_engine.downloader, SessionDownloader)
    engine = MyEngine(
        spider_class=FakeSpider, enable_settings=False, downloader=Downloader()
    )
    assert isinstance(engine.downloader, Downloader)


@pytest.mark.anyio
async def test_engine_item_processing(app):
    class MyItem(Item):
        best_scraping_library: str

    class Spider(BaseSpider):
        start_requests = [
            Request(
                url="/best_scraping_library",
                method="GET",
                base_url="https://example.com",
                app=app,
            )
        ]

        async def parse(
            self, response: Response
        ) -> typing.AsyncGenerator[typing.Union[Request, Item], None]:
            yield MyItem(best_scraping_library=response.text)
            yield MyItem(best_scraping_library=response.text)
            yield Request(
                url="/best_scraping_library",
                method="GET",
                base_url="https://example.com",
                app=app,
            )

    engine = Engine(spider_class=Spider, enable_settings=False)
    await engine.run_once()
    assert len(engine.spider.requests) == 1
    assert engine.spider.items == []


@pytest.mark.filterwarnings("once::RuntimeWarning")
@pytest.mark.anyio
def test_engine_without_items_manager_warning():
    with catch_warnings(record=True) as w:
        Engine(spider_class=lambda: 0, enable_settings=False)
        assert w
        assert len(w) == 1
        (warning,) = w
        assert warning.category == RuntimeWarning


@pytest.mark.anyio
async def test_engine_with_item_manager(app):
    class Spider(BaseSpider):
        start_requests = [
            Request(
                url="/best_scraping_library",
                method="GET",
                base_url="https://example.com",
                app=app,
            )
        ]

        async def parse(
            self, response: Response
        ) -> typing.AsyncGenerator[typing.Union[Request, Item, None], None]:
            yield None

    engine = Engine(
        spider_class=Spider, items_manager=ItemManager(), enable_settings=False
    )
    await engine.run_once()
    assert engine.spider.requests == []


@pytest.mark.anyio
async def test_engine_clean_up(monkeypatch, app):
    with tempfile.TemporaryDirectory() as tempdir:

        class Spider(BaseSpider):
            start_requests = [
                Request(
                    url="/best_scraping_library",
                    method="GET",
                    base_url="https://example.com",
                    app=app,
                )
            ]

            async def parse(
                self, response: Response
            ) -> typing.AsyncGenerator[typing.Union[Request, Item, None], None]:
                yield Item()

        item_manager = ItemManager(
            loaders=[JSONLoader(filename=Path(tempdir) / "test")]
        )
        engine = Engine(
            spider_class=Spider, items_manager=item_manager, enable_settings=False
        )
        await engine.run()
        loader = engine.items_manager.loaders[0]
        assert loader.state == LoaderState.CLOSED


def test_spider_string_start_requests():
    class Spider(BaseSpider):
        start_requests = ["https://example.com", "http://example.com"]

        async def parse(
            self, response: Response
        ) -> typing.AsyncGenerator[typing.Union[Request, Item, None], None]:
            yield None  # pragma: no cover

    spider = Spider()
    assert len(spider.requests) == 2
    assert isinstance(spider.requests[0], Request) and isinstance(
        spider.requests[1], Request
    )
    assert spider.requests[0].url == "https://example.com"
    assert spider.requests[0].method == "GET"
