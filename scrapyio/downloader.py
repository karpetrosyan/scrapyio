import typing
from abc import ABC
from abc import abstractmethod

import httpx
from httpx._client import USE_CLIENT_DEFAULT
from httpx._client import Response

from .exceptions import IgnoreRequestError
from .middlewares import BaseMiddleWare
from .types import CLEANUP_WITH_RESPONSE

if typing.TYPE_CHECKING:
    from .spider import Request


class BaseDownloader(ABC):
    def __init__(self):
        self.middlewares: typing.List[BaseMiddleWare] = []

    async def _send_request_via_middlewares(self, request: "Request") -> None:
        for middleware in self.middlewares:
            await middleware.process_request(request=request)

    async def _send_response_via_middlewares(self, response: Response) -> None:
        for middleware in reversed(self.middlewares):
            await middleware.process_response(response=response)

    async def send_request(
        self, request: "Request"
    ) -> typing.Optional[CLEANUP_WITH_RESPONSE]:
        try:
            await self._send_request_via_middlewares(request=request)
            response_generator = send_request(request=request)
            response = await anext(response_generator)
            await self._send_response_via_middlewares(response=response)
            return response_generator, response
        except IgnoreRequestError:
            return None

    @abstractmethod
    async def handle_request(
        self, request: "Request"
    ) -> typing.Optional[CLEANUP_WITH_RESPONSE]:
        ...


class Downloader(BaseDownloader):
    async def handle_request(
        self, request: "Request"
    ) -> typing.Optional[CLEANUP_WITH_RESPONSE]:
        response_gen = await self.send_request(request=request)
        return response_gen


async def send_request(request: "Request") -> typing.AsyncGenerator[Response, None]:
    async with httpx.AsyncClient(
        cookies=request.cookies,
        proxies=request.proxies,
        cert=request.cert,
        verify=request.verify,
        timeout=request.timeout,
        trust_env=request.trust_env,
        http1=request.http1,
        http2=request.http2,
        base_url=request.base_url,
        app=request.app,
    ) as client:
        if request.stream:
            async with client.stream(
                method=request.method,
                url=request.url,
                content=request.content,
                data=request.data,
                files=request.files,
                json=request.json,
                params=request.params,
                headers=request.headers,
                auth=USE_CLIENT_DEFAULT,
                follow_redirects=request.follow_redirects,
            ) as response:
                yield response
        response = await client.request(
            method=request.method,
            url=request.url,
            content=request.content,
            data=request.data,
            files=request.files,
            json=request.json,
            params=request.params,
            headers=request.headers,
            auth=USE_CLIENT_DEFAULT,
            follow_redirects=request.follow_redirects,
        )
        yield response
