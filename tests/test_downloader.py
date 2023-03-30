import inspect

import pytest

from scrapyio import Downloader
from scrapyio import Request
from scrapyio import Response
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
    req = Request(url="/", method="GET", app=app, base_url="https://example.am")
    cleanup_gen, response = await downloader.send_request(req)
    assert inspect.isasyncgen(cleanup_gen)
    assert isinstance(response, Response)
