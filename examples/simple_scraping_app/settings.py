import typing

from httpx._types import AuthTypes
from httpx._types import CertTypes
from httpx._types import CookieTypes
from httpx._types import HeaderTypes
from httpx._types import ProxiesTypes
from httpx._types import QueryParamTypes
from httpx._types import VerifyTypes

ITEM_MIDDLEWARES: typing.List[str] = []

# Middlewares
#   path to the middlewares
#   example: 'scrapyio.middlewares.BaseMiddleWare'
MIDDLEWARES: typing.List[str] = []

# Timeout for httpx request
REQUEST_TIMEOUT: int = 5

# Default headers for httpx request
DEFAULT_HEADERS: typing.Optional[HeaderTypes] = None

# Default cookies for httpx request
DEFAULT_COOKIES: typing.Optional[CookieTypes] = {}

# Default query parameters for httpx request
DEFAULT_PARAMS: typing.Optional[QueryParamTypes] = None

# Default auth for httpx request
DEFAULT_AUTH: typing.Optional[AuthTypes] = None

# Default for SSL verify mode
DEFAULT_VERIFY_SSL: VerifyTypes = True

# Default certs for httpx request
DEFAULT_CERTS: typing.Optional[CertTypes] = None

# Default HTTP version
HTTP_1: bool = True
HTTP_2: bool = False

# Default HTTP proxies
DEFAULT_PROXIES: typing.Optional[ProxiesTypes] = None

# Follow redirects for HTTP request
FOLLOW_REDIRECTS: bool = False

# Trust env for httpx request
DEFAULT_TRUST_ENV: bool = False

# Enable stream by default
ENABLE_STREAM_BY_DEFAULT: bool = False
