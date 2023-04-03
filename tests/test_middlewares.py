from abc import ABC

import pytest

from scrapyio import Request
from scrapyio.downloader import Downloader
from scrapyio.middlewares import BaseMiddleWare


@pytest.mark.anyio
async def test_request_middleware(app):
    class CustomMiddleWare(BaseMiddleWare, ABC):
        async def process_response(self, response):
            ...

        async def process_request(self, request):
            request.headers["test"] = "test"

    downloader = Downloader()
    downloader.middleware_classes.append(CustomMiddleWare)
    gen = await downloader.handle_request(
        request=Request(
            url="/headers",
            app=app,
            headers={"test": "test"},
            base_url="http://example.com",
            method="GET",
        )
    )
    assert gen
    _, response = gen[0], gen[1]
    assert response.status_code == 200
    assert "test" in response.json()


@pytest.mark.anyio
async def test_response_middleware(app):
    class CustomMiddleWare(BaseMiddleWare):
        async def process_response(self, response):
            response.headers["test"] = "test"

        async def process_request(self, request):
            ...

    downloader = Downloader()
    downloader.middleware_classes.append(CustomMiddleWare)
    gen = await downloader.handle_request(
        request=Request(
            url="/",
            app=app,
            headers={"test": "test"},
            base_url="http://example.com",
            method="GET",
        )
    )
    assert gen
    _, response = gen[0], gen[1]
    assert response.status_code == 200
    assert "test" in response.headers


@pytest.mark.anyio
async def test_explicit_response_return_middleware(app):
    class CustomMiddleWare(BaseMiddleWare):
        async def process_response(self, response):
            ...

        async def process_request(self, request):
            async def do_request():
                import httpx

                async with httpx.AsyncClient(app=app) as session:
                    response = await session.get(url="https://replaced.com")
                    yield response

            gen = do_request()
            response = await gen.__anext__()
            return gen, response

    downloader = Downloader()
    downloader.middleware_classes.append(CustomMiddleWare)
    gen = await downloader.handle_request(
        request=Request(url="http://example.com", method="GET", app=app)
    )
    assert gen
    _, response = gen[0], gen[1]
    assert response.status_code == 200
    assert response.request.url.scheme == "https"
    assert response.request.url.host == "replaced.com"


@pytest.mark.anyio
async def test_explicit_request_return_middleware(app):
    class CustomMiddleWare(BaseMiddleWare):
        USED = True

        async def process_response(self, response):
            if CustomMiddleWare.USED:  # to prevent recursion
                CustomMiddleWare.USED = False
                return Request(
                    url="/for_moving",
                    app=app,
                    method="GET",
                    base_url="https://example.com",
                )

        async def process_request(self, request):
            ...

    downloader = Downloader()
    downloader.middleware_classes.append(CustomMiddleWare)
    gen = await downloader.handle_request(
        request=Request(url="http://example.com/", method="GET", app=app)
    )
    assert gen
    _, response = gen[0], gen[1]
    assert response.status_code == 200
    assert response.request.url.path == "/for_moving"  # moved


@pytest.mark.anyio
async def test_invalid_middlewares_returns(app):
    class CustomMiddleWare(BaseMiddleWare):
        async def process_response(self, response):
            return 5

        async def process_request(self, request):
            ...

    downloader = Downloader()
    downloader.middleware_classes.append(CustomMiddleWare)
    with pytest.raises(TypeError, match="Response processing middleware must return.*"):
        await downloader.handle_request(
            request=Request(url="http://example.com", method="GET", app=app)
        )

    class CustomMiddleWare(BaseMiddleWare):
        async def process_response(self, response):
            raise NotImplementedError

        async def process_request(self, request):
            return 5

    downloader.middleware_classes[-1] = CustomMiddleWare
    with pytest.raises(TypeError, match="Request processing middleware must return"):
        await downloader.handle_request(
            request=Request(url="http://example.com", method="GET", app=app)
        )
