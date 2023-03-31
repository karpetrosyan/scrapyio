import typing
from abc import ABC
from abc import abstractmethod

from . import default_configs
from .http import Request
from .http import Response
from .types import CLEANUP_WITH_RESPONSE
from .utils import load_module


def build_middlewares_chain() -> typing.List["BaseMiddleWare"]:
    return [
        typing.cast("BaseMiddleWare", load_module(middleware)())
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


class TestMiddleWare(BaseMiddleWare):
    async def process_request(self, request: "Request") -> None:
        ...

    async def process_response(self, response: Response) -> None:
        ...
