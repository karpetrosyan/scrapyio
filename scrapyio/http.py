import typing
from dataclasses import dataclass
from dataclasses import field

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

from . import default_configs


@dataclass
class Request:
    url: str
    method: str
    auth: typing.Optional[AuthTypes] = field(
        default_factory=lambda: default_configs.DEFAULT_AUTH
    )
    params: typing.Optional[QueryParamTypes] = field(
        default_factory=lambda: default_configs.DEFAULT_PARAMS
    )
    headers: typing.Optional[HeaderTypes] = field(
        default_factory=lambda: default_configs.DEFAULT_HEADERS
    )
    cookies: typing.Optional[CookieTypes] = field(
        default_factory=lambda: default_configs.DEFAULT_COOKIES
    )
    verify: VerifyTypes = field(
        default_factory=lambda: default_configs.DEFAULT_VERIFY_SSL
    )
    cert: typing.Optional[CertTypes] = field(
        default_factory=lambda: default_configs.DEFAULT_CERTS
    )
    http1: bool = default_configs.HTTP_1
    http2: bool = default_configs.HTTP_2
    proxies: typing.Optional[ProxiesTypes] = field(
        default_factory=lambda: default_configs.DEFAULT_PROXIES
    )
    follow_redirects: bool = default_configs.FOLLOW_REDIRECTS
    timeout: TimeoutTypes = field(
        default_factory=lambda: Timeout(default_configs.REQUEST_TIMEOUT)
    )
    trust_env: bool = default_configs.DEFAULT_TRUST_ENV
    content: typing.Optional[RequestContent] = None
    data: typing.Optional[RequestData] = None
    files: typing.Optional[RequestFiles] = None
    json: typing.Optional[typing.Any] = None
    stream: bool = default_configs.ENABLE_STREAM_BY_DEFAULT
    app: typing.Optional[typing.Callable[..., typing.Any]] = None
    base_url: URLTypes = ""


async def clean_up_response(response_gen: typing.AsyncGenerator[Response, None]):
    try:
        await response_gen.__anext__()  # Must raise an exception
        assert True, "StopAsyncIteration was expected"  # pragma: no cover
    except StopAsyncIteration:
        ...
