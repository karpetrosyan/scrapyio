import typing
from abc import ABC
from abc import abstractmethod

from httpx import HTTPStatusError

from . import default_configs
from .http import Request
from .http import Response
from .types import CLEANUP_WITH_RESPONSE
from .utils import load_module


def build_middlewares_chain() -> typing.List[typing.Type["BaseMiddleWare"]]:
    from . import default_configs

    return [
        typing.cast(typing.Type["BaseMiddleWare"], load_module(middleware))
        for middleware in default_configs.MIDDLEWARES
    ]


class BaseMiddleWare(ABC):
    @abstractmethod
    async def process_request(
        self, request: "Request"
    ) -> typing.Union[None, CLEANUP_WITH_RESPONSE]:
        ...

    @abstractmethod
    async def process_response(self, response: Response) -> typing.Union[None, Request]:
        ...


class ProxyMiddleWare(BaseMiddleWare):
    def __init__(self):
        self.next_middleware_index = 0
        self.proxies = default_configs.PROXY_CHAIN[:]
        self.last_request: typing.Optional[Request] = None

    async def process_request(
        self, request: "Request"
    ) -> typing.Union[None, CLEANUP_WITH_RESPONSE]:
        if self.proxies:
            request.proxies = {"all": self.proxies[self.next_middleware_index]}
        self.last_request = request
        self.next_middleware_index = 1
        return None

    async def process_response(self, response: Response) -> typing.Union[None, Request]:
        try:
            response.raise_for_status()
        except HTTPStatusError:
            if self.next_middleware_index < len(self.proxies):
                new_request = self.last_request
                assert new_request
                new_request.proxies = {"all": self.proxies[self.next_middleware_index]}
                self.last_request = new_request
                self.next_middleware_index += 1
                return new_request
        return None
