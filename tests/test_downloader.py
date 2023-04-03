import inspect

import pytest

from scrapyio import Downloader
from scrapyio import IgnoreRequestError
from scrapyio import Request
from scrapyio import Response
from scrapyio import SessionDownloader
from scrapyio.downloader import send_request
from scrapyio.middlewares import BaseMiddleWare


@pytest.mark.anyio
async def test_send_request(app):
    req = Request(url="/", method="GET", app=app, base_url="https://example.am")
    gen = send_request(req)
    response = await gen.__anext__()
    assert response.status_code == 200
    assert response.text == '"Root"'
    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()


@pytest.mark.anyio
async def test_downloader_send_request(app):
    downloader = Downloader()
    req = Request(url="/", method="GET", app=app, base_url="http://example.com")
    cleanup_gen, response = await downloader._process_request_with_middlewares(req)
    assert inspect.isasyncgen(cleanup_gen)
    assert isinstance(response, Response)


@pytest.mark.anyio
async def test_session_downloader_cookies(app):
    downloader = SessionDownloader(app=app, base_url="https://example.com")
    req = Request(url="/cookies", method="GET")
    cleanup_gen, response = await downloader._process_request_with_middlewares(
        request=req
    )
    assert response.status_code == 200
    assert len(downloader.session.cookies) == 1
    cleanup_gen, response = await downloader._process_request_with_middlewares(
        request=req
    )
    assert response.json() == {"test": "test"}


@pytest.mark.anyio
async def test_ignoring_requests(app):
    class CustomMiddleWare(BaseMiddleWare):
        async def process_response(self, response):
            raise IgnoreRequestError()

        async def process_request(self, request):
            ...

    downloader = Downloader()
    downloader.middleware_classes.append(CustomMiddleWare)

    resp = await downloader.handle_request(
        Request(
            url="",
            base_url="https://example.com",
            method="GET",
            app=app,
        )
    )
    assert resp is None


@pytest.mark.anyio
async def test_session_downloader_configs(app):
    downloader = SessionDownloader(
        cookies={"test": "test"}, app=app, base_url="https://example.com"
    )
    gen = await downloader.handle_request(Request(url="/cookies", method="GET"))
    assert gen
    _, response = gen
    assert "test" in response.json()


@pytest.mark.anyio
async def test_session_stream_request(app):
    downloader = SessionDownloader(app=app, base_url="https://example.com")
    gen = await downloader.handle_request(Request(url="/", method="GET", stream=True))
    assert gen
    _, response = gen
    await response.aread()


@pytest.mark.anyio
async def test_stream_request(app):
    downloader = Downloader()
    gen = await downloader.handle_request(
        Request(
            url="/", method="GET", stream=True, app=app, base_url="https://example.com"
        )
    )
    assert gen
    _, response = gen
    await response.aread()
