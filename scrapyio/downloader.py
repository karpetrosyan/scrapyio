import logging
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

from .exceptions import IgnoreRequestError
from .http import Request
from .http import clean_up_response
from .middlewares import BaseMiddleWare
from .middlewares import build_middlewares_chain
from .settings import CONFIGS
from .types import CLEANUP_WITH_RESPONSE

log = logging.getLogger("scrapyio")


class BaseDownloader(ABC):
    def __init__(self) -> None:
        self.middleware_classes: typing.List[
            typing.Type[BaseMiddleWare]
        ] = build_middlewares_chain()

    async def _send_request_via_middlewares(
        self, request: "Request", middlewares: typing.List[BaseMiddleWare]
    ) -> typing.Union[None, CLEANUP_WITH_RESPONSE]:
        log.debug(f"Sending the request via middlewares: {request.id=}")
        for middleware in middlewares:
            log.debug(
                f"Sending the request via middleware"
                f" `{middleware.__class__.__name__}`: {request.id=}"
            )
            resp = await middleware.process_request(request=request)
            log.debug(
                f"`{middleware.__class__.__name__}` middleware "
                f"return value is {resp=!r} for request: {request.id=}`"
            )
            if resp is not None:
                if isinstance(resp, tuple):
                    return resp
                else:
                    log.info(
                        f"Invalid value was returned by request"
                        f" middleware: `{middleware.__class__.__name__}` {request.id=}"
                    )
                    raise TypeError(
                        "Request processing middleware must return "
                        "either `Tuple[CLEANUP_WITH_RESPONSE]` or "
                        "`None` not `%s`" % resp.__class__.__name__
                    )

    async def _send_response_via_middlewares(
        self, response: Response, middlewares: typing.List[BaseMiddleWare]
    ) -> typing.Union[None, Request]:
        log.debug(f"Sending the response via middlewares: {response=}")
        for middleware in reversed(middlewares):
            log.debug(
                f"Sending the response via middleware"
                f" `{middleware.__class__.__name__}`: {response=}"
            )
            request = await middleware.process_response(response=response)
            log.debug(
                f"`{middleware.__class__.__name__}` middleware "
                f"return value is {request=!r} for response: {response=}`"
            )
            if request is not None:
                if isinstance(request, Request):
                    return request
                else:
                    log.info(
                        f"Invalid value was returned by response "
                        f"middleware: `{middleware.__class__.__name__}`"
                    )
                    raise TypeError(
                        "Response processing middleware must return "
                        "either `Request` or `None` not `%s`"
                        % request.__class__.__name__
                    )

    def send_request(self, request: "Request") -> typing.AsyncGenerator[Response, None]:
        log.debug(f"Sending the standard request: {request.id=}")
        return send_request(request=request)

    async def _process_request_with_middlewares(
        self, request: "Request"
    ) -> typing.Optional[CLEANUP_WITH_RESPONSE]:
        log.debug(f"Processing the request: {request.id=}")
        log.debug(f"Building the middlewares: {request.id=}")
        middlewares = [middleware() for middleware in self.middleware_classes]
        log.debug(f"Middlewares: {middlewares}: {request.id=}")
        try:
            cleanup_and_response = await self._send_request_via_middlewares(
                request=request, middlewares=middlewares
            )
            log.debug(f"Request middlewares was processed for request: {request.id=}")
            if cleanup_and_response is None:
                clean_up = self.send_request(request=request)
                response = await clean_up.__anext__()
            else:
                log.debug(
                    f"Request middlewares was explicit "
                    f"returned the response: {request.id=}"
                )
                clean_up, response = cleanup_and_response
            log.debug(
                f"Sending the response through the "
                f"middlewares: {response=} {request.id=}"
            )
            next_request = await self._send_response_via_middlewares(
                response=response, middlewares=middlewares
            )
            log.debug(f"Response middlewares was processed for request: {request.id=}")
            if next_request is not None:
                log.debug("Response middlewares was explicit returned the new request")
                log.debug(f"Processing the new request explicit: {request.id=}")
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
        log.debug(f"Sending the request with the session: {request=} {self.session=}")
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
        cookies=first_not_none(cookies, CONFIGS.DEFAULT_COOKIES),
        proxies=first_not_none(proxies, CONFIGS.DEFAULT_PROXIES),
        cert=first_not_none(cert, CONFIGS.DEFAULT_CERTS),
        verify=first_not_none(verify, CONFIGS.DEFAULT_VERIFY_SSL),
        timeout=first_not_none(timeout, CONFIGS.REQUEST_TIMEOUT),
        trust_env=first_not_none(trust_env, CONFIGS.DEFAULT_TRUST_ENV),
        http1=first_not_none(http1, CONFIGS.HTTP_1),
        http2=first_not_none(http2, CONFIGS.HTTP_2),
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
            auth=request.auth or USE_CLIENT_DEFAULT,
            follow_redirects=request.follow_redirects,
        ) as response:
            yield response
    else:
        response = await session.request(
            method=request.method,
            url=request.url,
            content=request.content,
            data=request.data,
            files=request.files,
            json=request.json,
            params=request.params,
            headers=request.headers,
            auth=request.auth or USE_CLIENT_DEFAULT,
            follow_redirects=request.follow_redirects,
        )
        yield response


async def send_request(request: "Request") -> typing.AsyncGenerator[Response, None]:
    log.debug(f"Creating the AsyncClient for the request: {request.id=}")
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
        log.debug(f"Async client was created: AsyncClient={session}")
        if request.stream:
            log.debug(f"Sending the stream request: {request=}")
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
                log.debug("Stream response received, yielding the response")
                yield response
            log.debug(f"Tear down streaming response for request: {request=}")
        else:
            log.debug(f"Sending the standard request: {request.id=}")
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
            log.debug("Standard response received, yielding the response")
            yield response
