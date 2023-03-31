import pytest

from scrapyio import Request
from scrapyio.engines import Engine
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
