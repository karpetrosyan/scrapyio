import typing

from httpx._client import Response

RESPONSE_GENERATOR = typing.AsyncGenerator[Response, None]
CLEANUP_WITH_RESPONSE = typing.Tuple[RESPONSE_GENERATOR, Response]
