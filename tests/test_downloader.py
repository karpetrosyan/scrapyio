import httpx
from scrapyio.downloader import send_request
from httpx import Response
from httpx._exceptions import ResponseNotRead
from contextlib import suppress
import pytest
from scrapyio.downloader import create_default_session
import inspect
from scrapyio.settings import CONFIGS
from scrapyio.downloader import Downloader


@pytest.mark.anyio
async def test_downloader_send_request(mocked_request):
    req = mocked_request(url="/")
    response_generator = send_request(request=req)
    try:
        assert inspect.isasyncgen(response_generator)
        response = await response_generator.__anext__()
        assert isinstance(response, Response)
        assert response.text
    finally:
        with suppress(StopAsyncIteration):
            await response_generator.__anext__()


@pytest.mark.anyio
async def test_downloader_send_request_stream(mocked_request):
    req = mocked_request(url="/", stream=True)
    response_generator = send_request(request=req)
    try:
        assert inspect.isasyncgen(response_generator)
        response = await response_generator.__anext__()
        assert isinstance(response, Response)

        with pytest.raises(ResponseNotRead):
            assert response.text
    finally:
        with suppress(StopAsyncIteration):
            await response_generator.__anext__()


@pytest.mark.anyio
def test_default_session_creation():
    session = create_default_session(
        app=None,
        base_url='',
        cookies=None,
        proxies=None,
        verify=None,
        cert=None,
        http1=None,
        http2=None,
        timeout=None,
        trust_env=None
    )

    assert isinstance(session, httpx.AsyncClient)


@pytest.mark.anyio
def test_default_session_creation_configs(monkeypatch):
    monkeypatch.setattr(CONFIGS, "DEFAULT_COOKIES", {"...": "..."})
    monkeypatch.setattr(CONFIGS, "DEFAULT_TRUST_ENV", False)
    session = create_default_session(
        app=None,
        base_url='',
        cookies=None,
        proxies=None,
        verify=None,
        cert=None,
        http1=None,
        http2=None,
        timeout=None,
        trust_env=None
    )
    assert session.cookies == {"...": "..."}
    assert not session.trust_env


@pytest.mark.anyio
async def test_request_sending_via_middlewares(mocked_request):
    req = mocked_request(url="/")
    downloader = Downloader()
    await downloader._send_request_via_middlewares(request=req, middlewares=[])


@pytest.mark.anyio
async def test_response_sending_via_middlewares(mocked_request):
    downloader = Downloader()
    await downloader._send_response_via_middlewares(response=..., middlewares=[])
