"""
This module contains unit tests for the Scrapyio
"downloader". These checks ensure that request
downloading and HTTP requests work properly.
"""
import inspect
from contextlib import suppress
from functools import partial

import httpx
import pytest
from httpx import Response
from httpx._exceptions import ResponseNotRead

from scrapyio import Request
from scrapyio.downloader import Downloader
from scrapyio.downloader import SessionDownloader
from scrapyio.downloader import create_default_session
from scrapyio.downloader import send_request
from scrapyio.downloader import send_request_with_session
from scrapyio.exceptions import IgnoreRequestError
from scrapyio.middlewares import BaseMiddleWare
from scrapyio.settings import CONFIGS


class CustomMiddleWare(BaseMiddleWare):
    def __init__(self, new_url: str):
        self.new_url = new_url

    async def process_request(self, request):
        request.url = self.new_url

    async def process_response(self, middlewares):
        ...  # pragma: no cover


class StreamReadMiddleWare(BaseMiddleWare):
    async def process_response(self, response):
        await response.aread()

    async def process_request(self, request):
        ...  # pragma: no cover


class ExplicitReturnMiddleWare(BaseMiddleWare):
    REQUEST_GENERATION_LIMIT = 2

    def __init__(self, mocked_request):
        self.mocked_request = mocked_request

    async def process_request(self, request):
        req = self.mocked_request(url="/")
        response_gen = send_request(request=req)
        return response_gen, await response_gen.__anext__()

    async def process_response(self, response):
        cls = type(self)
        if cls.REQUEST_GENERATION_LIMIT != 0:
            cls.REQUEST_GENERATION_LIMIT -= 1
        else:
            return
        return self.mocked_request(url="/")


class ExplicitResponseMiddleWare(ExplicitReturnMiddleWare):
    async def process_request(self, request):
        ...

    async def process_response(self, response):
        return await super().process_response(response)


class InvalidExplicitReturnMiddleWare(BaseMiddleWare):
    def __init__(self, mocked_request):
        self.mocked_request = mocked_request

    async def process_response(self, response):
        return object()

    async def process_request(self, request):
        return object()


class ExceptionMiddleWare(BaseMiddleWare):
    async def process_response(self, response):
        raise NotImplementedError

    async def process_request(self, request):
        raise NotImplementedError


class IgnoreMiddleWare(BaseMiddleWare):
    async def process_response(self, response):
        raise NotImplementedError

    async def process_request(self, request):
        raise IgnoreRequestError()


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
        base_url="",
        cookies=None,
        proxies=None,
        verify=None,
        cert=None,
        http1=None,
        http2=None,
        timeout=None,
        trust_env=None,
    )

    assert isinstance(session, httpx.AsyncClient)


@pytest.mark.anyio
def test_default_session_creation_configs(monkeypatch):
    monkeypatch.setattr(CONFIGS, "DEFAULT_COOKIES", {"...": "..."})
    monkeypatch.setattr(CONFIGS, "DEFAULT_TRUST_ENV", False)
    session = create_default_session(
        app=None,
        base_url="",
        cookies=None,
        proxies=None,
        verify=None,
        cert=None,
        http1=None,
        http2=None,
        timeout=None,
        trust_env=None,
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


@pytest.mark.anyio
async def test_request_changing_in_middlewares(mocked_request):
    req = mocked_request(url="/")
    downloader = Downloader()
    first_url = "/changed"
    second_url = "/second-changed"
    await downloader._send_request_via_middlewares(
        request=req,
        middlewares=[
            CustomMiddleWare(new_url=first_url),
            CustomMiddleWare(new_url=second_url),
        ],
    )
    assert req.url == "/second-changed"


@pytest.mark.anyio
async def test_response_changing_in_middlewares(mocked_request):
    req = mocked_request(url="/")
    downloader = Downloader()
    gen = send_request(req)
    try:
        response = await gen.__anext__()
        await downloader._send_response_via_middlewares(
            response=response,
            middlewares=[StreamReadMiddleWare()],
        )
        assert response.text
    finally:
        with suppress(StopAsyncIteration):
            await gen.__anext__()


@pytest.mark.anyio
async def test_explicit_return_by_response_middleware(mocked_request):
    md = ExplicitReturnMiddleWare(mocked_request)
    downloader = Downloader()
    response = object()
    next_request = await downloader._send_response_via_middlewares(
        response=response, middlewares=[ExceptionMiddleWare(), md]
    )
    assert isinstance(next_request, Request)


@pytest.mark.anyio
async def test_explicit_return_by_request_middleware(mocked_request):
    md = ExplicitReturnMiddleWare(mocked_request)
    req = mocked_request(url="/")
    downloader = Downloader()
    next_request = await downloader._send_request_via_middlewares(
        request=req, middlewares=[md, ExceptionMiddleWare()]
    )
    assert isinstance(next_request, tuple)


@pytest.mark.anyio
async def test_invalid_explicit_return(mocked_request):
    md = InvalidExplicitReturnMiddleWare(mocked_request)
    req = mocked_request(url="/")
    downloader = Downloader()

    with pytest.raises(TypeError):
        await downloader._send_request_via_middlewares(request=req, middlewares=[md])

    with pytest.raises(TypeError):
        await downloader._send_response_via_middlewares(
            response=object(), middlewares=[md]
        )


@pytest.mark.anyio
async def test_stream_request_with_session(app):
    req = Request(url="/", method="GET", stream=True)
    async with httpx.AsyncClient(
        base_url="https://scrapyio-example.com", app=app
    ) as client:
        gen = send_request_with_session(client, req)
        try:
            resp = await gen.__anext__()
            await resp.aread()
            assert resp.text
        finally:
            with suppress(StopAsyncIteration):
                await gen.__anext__()


@pytest.mark.anyio
async def test_standard_request_with_session(app):
    req = Request(url="/", method="GET")
    async with httpx.AsyncClient(
        base_url="https://scrapyio-example.com", app=app
    ) as client:
        gen = send_request_with_session(client, req)
        try:
            resp = await gen.__anext__()
            assert resp.text
        finally:
            with suppress(StopAsyncIteration):
                await gen.__anext__()


@pytest.mark.anyio
async def test_standard_downloader_request_handling(mocked_request):
    req = mocked_request(url="/")
    downloader = Downloader()
    clean_up_and_response = await downloader.handle_request(request=req)
    clean_up = clean_up_and_response[0]
    response = clean_up_and_response[1]

    try:
        assert response.text
    finally:
        with suppress(StopAsyncIteration):
            await clean_up.__anext__()


@pytest.mark.anyio
async def test_session_downloader_request_handling(mocked_request, app):
    req = Request(url="/", method="GET")
    downloader = SessionDownloader(app=app, base_url="https://scrapyio-example.com")
    clean_up_and_response = await downloader.handle_request(request=req)
    clean_up = clean_up_and_response[0]
    response = clean_up_and_response[1]

    try:
        assert response.text
    finally:
        with suppress(StopAsyncIteration):
            await clean_up.__anext__()


@pytest.mark.anyio
async def test_downloader_request_processing(mocked_request):
    req = mocked_request(url="/")
    downloader = Downloader()
    clean_up, resp = await downloader._process_request_with_middlewares(request=req)
    with suppress(StopAsyncIteration):
        await clean_up.__anext__()


@pytest.mark.anyio
async def test_downloader_request_processing_with_explicit_request(
    mocked_request, monkeypatch
):
    req = mocked_request(url="/")
    downloader = Downloader()
    mocked_md = partial(ExplicitReturnMiddleWare, mocked_request)
    downloader.middleware_classes.append(mocked_md)
    clean_up, resp = await downloader._process_request_with_middlewares(request=req)
    assert isinstance(resp, Response)
    with suppress(StopAsyncIteration):
        await clean_up.__anext__()


@pytest.mark.anyio
async def test_downloader_request_processing_with_explicit_response(
    mocked_request, monkeypatch
):
    req = mocked_request(url="/")
    downloader = Downloader()
    mocked_md = partial(ExplicitResponseMiddleWare, mocked_request)
    downloader.middleware_classes.append(mocked_md)
    clean_up, resp = await downloader._process_request_with_middlewares(request=req)
    assert resp.text
    with suppress(StopAsyncIteration):
        await clean_up.__anext__()


@pytest.mark.anyio
async def test_downloader_request_processing_ignore_request(mocked_request):
    req = mocked_request(url="/")

    downloader = Downloader()
    downloader.middleware_classes.append(IgnoreMiddleWare)
    resp = await downloader._process_request_with_middlewares(request=req)
    assert resp is None
