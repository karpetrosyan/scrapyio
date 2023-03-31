import inspect

import pytest

from scrapyio import Downloader
from scrapyio import Request
from scrapyio import Response
from scrapyio import SessionDownloader
from scrapyio.downloader import send_request


@pytest.mark.anyio
async def test_send_request(app):
    req = Request(url="/", method="GET", app=app, base_url="https://example.am")
    gen = send_request(req)
    response = await anext(gen)
    assert response.status_code == 200
    assert response.text == '"Root"'
    with pytest.raises(StopAsyncIteration):
        await anext(gen)


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
