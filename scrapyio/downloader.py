import typing
from abc import ABC
from abc import abstractmethod

import httpx
from httpx._client import USE_CLIENT_DEFAULT
from httpx._client import Response
from httpx._types import CertTypes
from httpx._types import CookieTypes
from httpx._types import ProxiesTypes
from httpx._types import TimeoutTypes
from httpx._types import URLTypes
from httpx._types import VerifyTypes

from scrapyio.utils import first_not_none

from . import default_configs
from .exceptions import IgnoreRequestError
from .http import Request
from .http import clean_up_response
from .middlewares import BaseMiddleWare
from .middlewares import build_middlewares_chain
from .types import CLEANUP_WITH_RESPONSE


class BaseDownloader(ABC):
    def __init__(self):
        self.middleware_classes: typing.List[
            typing.Type[BaseMiddleWare]
        ] = build_middlewares_chain()

    async def _send_request_via_middlewares(
        self, request: "Request", middlewares: typing.List[BaseMiddleWare]
    ) -> typing.Union[None, CLEANUP_WITH_RESPONSE]:
        for middleware in middlewares:
            resp = await middleware.process_request(request=request)
            if resp is not None:
                if isinstance(resp, tuple):
                    return resp
                else:
                    raise TypeError(
                        "Request processing middleware must return "
                        "either `Tuple[CLEANUP_WITH_RESPONSE]` or "
                        "`None` not `%s`" % resp.__class__.__name__
                    )

    async def _send_response_via_middlewares(
        self, response: Response, middlewares: typing.List[BaseMiddleWare]
    ) -> typing.Union[None, Request]:
        for middleware in reversed(middlewares):
            request = await middleware.process_response(response=response)
            if request is not None:
                if isinstance(request, Request):
                    return request
                else:
                    raise TypeError(
                        "Response processing middleware must return "
                        "either `Request` or `None` not `%s`"
                        % request.__class__.__name__
                    )

    def send_request(self, request: "Request") -> typing.AsyncGenerator[Response, None]:
        return send_request(request=request)

    async def _process_request_with_middlewares(
        self, request: "Request"
    ) -> typing.Optional[CLEANUP_WITH_RESPONSE]:
        middlewares = [middleware() for middleware in self.middleware_classes]
        try:
            cleanup_and_response = await self._send_request_via_middlewares(
                request=request, middlewares=middlewares
            )
            if cleanup_and_response is None:
                clean_up = self.send_request(request=request)
                response = await clean_up.__anext__()
            else:
                clean_up, response = cleanup_and_response
            next_request = await self._send_response_via_middlewares(
                response=response, middlewares=middlewares
            )
            if next_request is not None:
                await clean_up_response(clean_up)
                return await self._process_request_with_middlewares(
                    request=next_request
                )
            return clean_up, response
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
        response_gen = await self._process_request_with_middlewares(request=request)
        return response_gen


class SessionDownloader(BaseDownloader):
    def __init__(
        self,
        app: typing.Optional[typing.Callable[..., typing.Any]] = None,
        base_url: URLTypes = "",
        cookies: typing.Optional[CookieTypes] = None,
        proxies: typing.Optional[ProxiesTypes] = None,
        verify: typing.Optional[VerifyTypes] = None,
        cert: typing.Optional[CertTypes] = None,
        http1: typing.Optional[bool] = None,
        http2: typing.Optional[bool] = None,
        timeout: typing.Optional[TimeoutTypes] = None,
        trust_env: typing.Optional[bool] = None,
    ):
        super().__init__()
        self.session: httpx.AsyncClient = create_default_session(
            app=app,
            base_url=base_url,
            cookies=cookies,
            proxies=proxies,
            verify=verify,
            cert=cert,
            http1=http1,
            http2=http2,
            timeout=timeout,
            trust_env=trust_env,
        )

    async def handle_request(
        self, request: "Request"
    ) -> typing.Optional[CLEANUP_WITH_RESPONSE]:
        return await self._process_request_with_middlewares(request=request)

    def send_request(self, request: "Request") -> typing.AsyncGenerator[Response, None]:
        return send_request_with_session(session=self.session, request=request)


def create_default_session(
    app: typing.Optional[typing.Callable[..., typing.Any]],
    base_url: URLTypes,
    cookies: typing.Optional[CookieTypes],
    proxies: typing.Optional[ProxiesTypes],
    verify: typing.Optional[VerifyTypes],
    cert: typing.Optional[CertTypes],
    http1: typing.Optional[bool],
    http2: typing.Optional[bool],
    timeout: typing.Optional[TimeoutTypes],
    trust_env: typing.Optional[bool],
) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        app=app,
        base_url=base_url,
        cookies=first_not_none(cookies, default_configs.DEFAULT_COOKIES),
        proxies=first_not_none(proxies, default_configs.DEFAULT_PROXIES),
        cert=first_not_none(cert, default_configs.DEFAULT_CERTS),
        verify=first_not_none(verify, default_configs.DEFAULT_VERIFY_SSL),
        timeout=first_not_none(timeout, default_configs.REQUEST_TIMEOUT),
        trust_env=first_not_none(trust_env, default_configs.DEFAULT_TRUST_ENV),
        http1=first_not_none(http1, default_configs.HTTP_1),
        http2=first_not_none(http2, default_configs.HTTP_2),
    )


async def send_request_with_session(
    session: httpx.AsyncClient, request: "Request"
) -> typing.AsyncGenerator[Response, None]:
    if request.stream:
        async with session.stream(
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
    response = await session.request(
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
    ) as session:
        if request.stream:
            async with session.stream(
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
        response = await session.request(
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
