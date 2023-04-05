from scrapyio.middlewares import build_middlewares_chain
from scrapyio.settings import CONFIGS
from scrapyio.middlewares import ProxyMiddleWare
from httpx._exceptions import HTTPStatusError
import pytest


def do_not_raise_status(*a, **kw):
    ...


def do_raise_status(*a, **kw):
    raise HTTPStatusError("Test error", request=..., response=...)


def test_build_middleware_chain(monkeypatch):
    new_middlewares = [
        "scrapyio.middlewares.ProxyMiddleWare",
        "scrapyio.middlewares.ProxyMiddleWare"
    ]
    monkeypatch.setattr(CONFIGS, "MIDDLEWARES", new_middlewares)
    middleware_chain = build_middlewares_chain()
    assert len(middleware_chain) == 2
    assert middleware_chain[0] == ProxyMiddleWare
    assert middleware_chain[1] == ProxyMiddleWare


@pytest.mark.anyio
async def test_proxy_middleware_request_processing_without_proxy(mocked_request):
    req = mocked_request(url="/")
    proxy = ProxyMiddleWare()
    await proxy.process_request(request=req)
    assert proxy.last_request == req
    assert proxy.next_middleware_index == 1
    assert req.proxies is None


@pytest.mark.anyio
async def test_proxy_middleware_request_processing_with_proxy(mocked_request,
                                                              monkeypatch):
    req = mocked_request(url="/")
    monkeypatch.setattr(CONFIGS, "PROXY_CHAIN", ["https://scrapyio-example.com"])
    proxy = ProxyMiddleWare()
    await proxy.process_request(request=req)
    assert proxy.last_request == req
    assert proxy.next_middleware_index == 1
    assert req.proxies == {"all": "https://scrapyio-example.com"}


@pytest.mark.anyio
async def test_proxy_middleware_exception_response_processing():
    proxy = ProxyMiddleWare()

    response = type('test', (), {"raise_for_status": do_not_raise_status})

    assert await proxy.process_response(response=response) is None


@pytest.mark.anyio
async def test_proxy_middleware_success_response_processing_without_proxy():
    proxy = ProxyMiddleWare()

    response = type('test', (), {"raise_for_status": do_raise_status})
    assert await proxy.process_response(response=response) is None


@pytest.mark.anyio
async def test_proxy_middleware_success_response_processing_with_proxy(mocked_request,
                                                                       monkeypatch):
    req = mocked_request(url="/")
    monkeypatch.setattr(CONFIGS, "PROXY_CHAIN", ["https://scrapyio-example.com", "https://scrapyio-example.com"])
    proxy = ProxyMiddleWare()

    response = type('test', (), {"raise_for_status": do_raise_status})

    with pytest.raises(AssertionError):
        assert await proxy.process_response(response=response) is None

    await proxy.process_request(request=req)
    next_request = await proxy.process_response(response=response)
    assert next_request
