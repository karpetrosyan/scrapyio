import logging
import typing
from dataclasses import dataclass
from dataclasses import field
from itertools import count

from httpx import Response
from httpx._config import Timeout
from httpx._types import AuthTypes
from httpx._types import CertTypes
from httpx._types import CookieTypes
from httpx._types import HeaderTypes
from httpx._types import ProxiesTypes
from httpx._types import QueryParamTypes
from httpx._types import RequestContent
from httpx._types import RequestData
from httpx._types import RequestFiles
from httpx._types import TimeoutTypes
from httpx._types import URLTypes
from httpx._types import VerifyTypes

from .settings import CONFIGS

log = logging.getLogger("scrapyio")


@dataclass
class Request:
    url: str
    method: str
    id: int = field(default_factory=count().__next__)
    auth: typing.Optional[AuthTypes] = field(
        default_factory=lambda: CONFIGS.DEFAULT_AUTH
    )
    params: typing.Optional[QueryParamTypes] = field(
        default_factory=lambda: CONFIGS.DEFAULT_PARAMS
    )
    headers: typing.Optional[HeaderTypes] = field(
        default_factory=lambda: CONFIGS.DEFAULT_HEADERS
    )
    cookies: typing.Optional[CookieTypes] = field(
        default_factory=lambda: CONFIGS.DEFAULT_COOKIES
    )
    verify: VerifyTypes = field(default_factory=lambda: CONFIGS.DEFAULT_VERIFY_SSL)
    cert: typing.Optional[CertTypes] = field(
        default_factory=lambda: CONFIGS.DEFAULT_CERTS
    )
    http1: bool = CONFIGS.HTTP_1
    http2: bool = CONFIGS.HTTP_2
    proxies: typing.Optional[ProxiesTypes] = field(
        default_factory=lambda: CONFIGS.DEFAULT_PROXIES
    )
    follow_redirects: bool = CONFIGS.FOLLOW_REDIRECTS
    timeout: TimeoutTypes = field(
        default_factory=lambda: Timeout(CONFIGS.REQUEST_TIMEOUT)
    )
    trust_env: bool = CONFIGS.DEFAULT_TRUST_ENV
    content: typing.Optional[RequestContent] = None
    data: typing.Optional[RequestData] = None
    files: typing.Optional[RequestFiles] = None
    json: typing.Optional[typing.Any] = None
    stream: bool = CONFIGS.ENABLE_STREAM_BY_DEFAULT
    app: typing.Optional[typing.Callable[..., typing.Any]] = None
    base_url: URLTypes = ""

    def __post_init__(self):
        log.debug(f"New `Request` instance was created: {self=} was created")


async def clean_up_response(response_gen: typing.AsyncGenerator[Response, None]):
    try:
        await response_gen.__anext__()  # Must raise an exception
        log.error(
            "Response clean up doesnt raise " "the `StopAsyncIteration` exception"
        )  # pragma: no cover
        assert False, "StopAsyncIteration was expected"  # pragma: no cover
    except StopAsyncIteration:
        ...
