"""
This module contains scrapyio "engine" unit tests.
These tests ensure that the `engine` object, which
is in charge of the entire scrapyio lifecycle, performs as expected.
"""

from contextlib import suppress

import pytest

from scrapyio.downloader import SessionDownloader
from scrapyio.engines import Engine
from scrapyio.exceptions import InvalidParseMethodException, InvalidYieldValueException
from scrapyio.http import clean_up_response
from scrapyio.items import Item, ItemManager
from scrapyio.spider import BaseSpider


class TestSpider(BaseSpider):
    start_requests = []

    async def parse(self, response):
        yield None

    def handle_parse_exception(self, exc):
        ...  # pragma: no cover


def test_engine_downloader_explicit_setting(monkeypatch):
    engine = Engine(TestSpider(), downloader=SessionDownloader())
    assert isinstance(engine.downloader, SessionDownloader)


@pytest.mark.anyio
async def test_engine_single_request_handling(mocked_request):
    req = mocked_request(url="/")
    engine = Engine(spider=TestSpider())
    try:
        clean_up, response = await engine._send_single_request_to_downloader(
            request=req
        )
        assert response.is_success
    finally:
        with suppress(StopAsyncIteration):
            await clean_up.__anext__()


@pytest.mark.anyio
async def test_invalid_response_parsing_exception(mocked_response, monkeypatch):
    monkeypatch.setattr(TestSpider, "parse", lambda: ...)
    engine = Engine(spider=TestSpider())
    with pytest.raises(
        InvalidParseMethodException,
        match="Spider's `parse` must be " "an asynchronous generator function",
    ):
        await engine._handle_single_response(response_and_generator=mocked_response)


@pytest.mark.anyio
async def test_engine_response_parse_request_yielding(
    mocked_response, mocked_request, monkeypatch
):
    req = mocked_request(url="/")

    async def parse(self, response):
        yield req

    monkeypatch.setattr(TestSpider, "parse", parse)
    engine = Engine(spider=TestSpider())
    await engine._handle_single_response(response_and_generator=mocked_response)
    assert len(engine.spider.requests) == 1
    assert engine.spider.requests[0] == req


@pytest.mark.anyio
async def test_engine_response_parse_invalid_yielding(
    mocked_response, mocked_request, monkeypatch
):
    async def parse(self, response):
        yield 2

    monkeypatch.setattr(TestSpider, "parse", parse)
    engine = Engine(spider=TestSpider())
    with pytest.raises(
        InvalidYieldValueException,
        match=r"Invalid type yielded, expected " r"`Request` or `Item` got `int`",
    ):
        await engine._handle_single_response(response_and_generator=mocked_response)


@pytest.mark.anyio
async def test_engine_response_parse_item_yielding(mocked_response, monkeypatch):
    async def parse(self, response):
        yield Item()

    monkeypatch.setattr(TestSpider, "parse", parse)
    engine = Engine(spider=TestSpider())
    await engine._handle_single_response(response_and_generator=mocked_response)
    assert len(engine.spider.items) == 1


@pytest.mark.anyio
async def test_engine_responses_handling(mocked_response, mocked_response1):
    engine = Engine(spider=TestSpider())
    resp1 = mocked_response
    resp2 = mocked_response
    ret = await engine._handle_responses([resp1, resp2])
    assert ret is None


@pytest.mark.integtest
@pytest.mark.anyio
async def test_engine_requests_handling(mocked_request):
    req = mocked_request(url="/")
    engine = Engine(spider=TestSpider())
    engine.spider.requests.append(req)
    engine.spider.requests.append(req)
    responses = await engine._send_all_requests_to_downloader()
    try:
        assert len(responses) == 2
        r1, r2 = responses
        assert r1[1].is_success
        assert r2[1].is_success
    finally:
        for clean_up, response in responses:
            await clean_up_response(clean_up)
    assert engine.spider.requests == []


@pytest.mark.integtest
@pytest.mark.anyio
async def test_engine_running_once(mocked_request, monkeypatch):
    req = mocked_request(url="/")
    engine = Engine(spider=TestSpider(), items_manager=ItemManager())
    engine.spider.requests.append(req)
    await engine._run_once()


@pytest.mark.integtest
@pytest.mark.anyio
async def test_engine_run(mocked_request, monkeypatch):
    monkeypatch.setattr(TestSpider, "start_requests", [mocked_request(url="/")])

    engine = Engine(spider=TestSpider())
    await engine.run()


@pytest.mark.integtest
@pytest.mark.anyio
async def test_engine_tear_down(mocked_request, monkeypatch):
    engine = Engine(spider=TestSpider(), items_manager=ItemManager())
    await engine._tear_down()
