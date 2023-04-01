import asyncio
import typing
from abc import ABC
from abc import abstractmethod

from pydantic import BaseModel

from . import default_configs
from .exceptions import IgnoreItemError
from .item_loaders import BaseLoader
from .item_loaders import LoaderState
from .types import ITEM_ADDED_CALLBACK_TYPE
from .types import ITEM_IGNORING_CALLBACK_TYPE
from .utils import load_module

if typing.TYPE_CHECKING:
    from .item_middlewares import BaseItemMiddleWare


def build_items_middlewares_chain() -> typing.Sequence["BaseItemMiddleWare"]:
    return [
        typing.cast("BaseItemMiddleWare", load_module(middleware)())
        for middleware in default_configs.ITEM_MIDDLEWARES
    ]


def orjson_dumps_wrapper(*args, **kwargs) -> str:
    import orjson

    return orjson.dumps(*args, **kwargs).decode(encoding="utf-8")


class BaseItem(BaseModel):
    class Config:
        try:
            import orjson

            json_dumps = orjson_dumps_wrapper
            json_loads = orjson.loads
        except ImportError:
            ...


class Item(BaseItem):
    ...


class BaseItemsManager(ABC):
    def __init__(
        self,
        ignoring_callback: typing.Optional[ITEM_IGNORING_CALLBACK_TYPE] = None,
        success_callback: typing.Optional[ITEM_ADDED_CALLBACK_TYPE] = None,
        loader: typing.Optional[BaseLoader] = None,
    ):
        self.middlewares = build_items_middlewares_chain()
        self.ignoring_callback = ignoring_callback
        self.success_callback = success_callback
        self.loader = loader

    async def _send_single_item_via_middlewares(
        self, item: Item
    ) -> typing.Optional[Item]:
        for middleware in self.middlewares:
            try:
                await middleware.process_item(item=item)
            except IgnoreItemError:
                if self.ignoring_callback:
                    await self.ignoring_callback(item, middleware)
                return None
        if self.success_callback:
            await self.success_callback(item)

        return item

    async def _send_items_via_middlewares(
        self, items: typing.Sequence[Item]
    ) -> typing.Sequence[Item]:
        tasks = [
            asyncio.create_task(self._send_single_item_via_middlewares(item))
            for item in items
        ]

        filtered_items = [
            added_item for added_item in await asyncio.gather(*tasks) if added_item
        ]

        if self.loader:
            if self.loader.state == LoaderState.CREATED:
                await self.loader.open()
            loading_tasks = [
                asyncio.create_task(self.loader.dump(item_to_load))
                for item_to_load in filtered_items
            ]
            await asyncio.gather(
                *loading_tasks,
            )

        return typing.cast(typing.List[Item], filtered_items)

    @abstractmethod
    async def process_items(self, items: typing.Sequence[Item]) -> None:
        ...


class ItemManager(BaseItemsManager):
    async def process_items(self, items: typing.Sequence[Item]) -> None:
        await self._send_items_via_middlewares(items=items)
        return None
