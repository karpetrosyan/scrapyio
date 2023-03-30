import typing
from abc import ABC
from abc import abstractmethod

from httpx._client import Response

from . import default_configs
from .utils import load_module

if typing.TYPE_CHECKING:
    from .spider import Request


def build_middlewares_chain() -> typing.List["BaseMiddleWare"]:
    return [
        typing.cast("BaseMiddleWare", load_module(middleware)())
        for middleware in default_configs.MIDDLEWARES
    ]


class BaseMiddleWare(ABC):
    @abstractmethod
    async def process_request(self, request: "Request") -> None:
        ...

    @abstractmethod
    async def process_response(self, response: Response) -> None:
        ...


class TestMiddleWare(BaseMiddleWare):
    async def process_request(self, request: "Request") -> None:
        ...

    async def process_response(self, response: Response) -> None:
        ...
