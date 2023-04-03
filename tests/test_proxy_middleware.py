import pytest
from httpx import HTTPStatusError

from scrapyio import Request
from scrapyio.middlewares import ProxyMiddleWare
from scrapyio.settings import default_configs


@pytest.mark.anyio
async def test_proxy_middleware_request_process(monkeypatch, app):
    monkeypatch.setattr(default_configs, "PROXY_CHAIN", ["https://my_proxy_server.am"])
    middleware = ProxyMiddleWare()
    assert middleware.proxies == ["https://my_proxy_server.am"]
    first_request = Request(
        base_url="https://example.com", url="/", method="GET", app=app
    )
    await middleware.process_request(request=first_request)
    assert first_request.proxies == {"all": "https://my_proxy_server.am"}


@pytest.mark.anyio
async def test_proxy_middleware_with_empty_proxies(monkeypatch, app):
    monkeypatch.setattr(default_configs, "PROXY_CHAIN", [])
    middleware = ProxyMiddleWare()
    assert middleware.proxies == []
    first_request = Request(
        base_url="https://example.com", url="/", method="GET", app=app
    )
    await middleware.process_request(request=first_request)
    assert first_request.proxies is None


@pytest.mark.anyio
async def test_proxy_middleware_response_process(monkeypatch, app):
    monkeypatch.setattr(default_configs, "PROXY_CHAIN", ["https://my_proxy_server.am"])
    middleware = ProxyMiddleWare()
    assert middleware.proxies == ["https://my_proxy_server.am"]
    first_request = Request(
        base_url="https://example.com", url="/", method="GET", app=app
    )
    await middleware.process_request(request=first_request)
    assert first_request.proxies == {"all": "https://my_proxy_server.am"}

    RAISE = False

    def raise_for_status(self):
        if RAISE:
            raise HTTPStatusError("Test", request=..., response=...)

    response = type("", (), {"raise_for_status": raise_for_status})()
    assert await middleware.process_response(response=response) is None

    RAISE = True
    response = type("", (), {"raise_for_status": raise_for_status})()

    assert await middleware.process_response(response=response) is None


@pytest.mark.anyio
async def test_proxy_middleware_proxy_switching(monkeypatch, app):
    monkeypatch.setattr(
        default_configs, "PROXY_CHAIN", [..., ..., "https://my_proxy_server.am"]
    )

    middleware = ProxyMiddleWare()
    middleware.next_middleware_index = 2
    middleware.last_request = Request(url="...", method="...")

    RAISE = True

    def raise_for_status(self):
        if RAISE:
            raise HTTPStatusError("Test", request=..., response=...)

    response = type("", (), {"raise_for_status": raise_for_status})()
    next_request = await middleware.process_response(response=response)
    assert next_request
    assert next_request.proxies
    assert middleware.last_request.proxies["all"]
