import typing

import pytest

from scrapyio.exceptions import IgnoreItemError
from scrapyio.item_middlewares import BaseItemMiddleWare
from scrapyio.items import Item
from scrapyio.items import ItemManager


@pytest.mark.anyio
async def test_item_manager():
    class MyItem(Item):
        library_name: str

    items: typing.List[Item] = [MyItem(library_name="scrapyio")]
    manager = ItemManager()
    await manager.process_items(items)


@pytest.mark.anyio
async def test_item_manager_callbacks():
    class MyItem(Item):
        library_name: str

    class MyMiddleWare(BaseItemMiddleWare):
        async def process_item(self, item: Item) -> typing.Union[Item, None]:
            raise IgnoreItemError()

    async def my_success_callback(item: MyItem):
        SUCCESS.append(item.library_name)

    async def my_failed_loading_callback(item: MyItem, middleware: MyMiddleWare):
        FAILED.append((item.library_name, middleware))

    SUCCESS: typing.List[str] = []
    FAILED: typing.List[typing.Tuple[str, MyMiddleWare]] = []

    items: typing.List[Item] = [MyItem(library_name="scrapyio")]
    manager = ItemManager(success_callback=my_success_callback)
    await manager.process_items(items)
    assert SUCCESS == ["scrapyio"]
    manager.middlewares.append(MyMiddleWare())
    manager.ignoring_callback = my_failed_loading_callback
    await manager.process_items(items)
    assert len(SUCCESS) == 1
    assert len(FAILED) == 1
    assert FAILED[0][0] == "scrapyio"
    assert FAILED[0][1] == manager.middlewares[-1]


@pytest.mark.anyio
async def test_items_filtering():
    class MyItem(Item):
        library_name: str

    class MyMiddleWare(BaseItemMiddleWare):
        async def process_item(self, item: Item) -> typing.Union[Item, None]:
            item = typing.cast(MyItem, item)
            if item.library_name != "scrapyio":
                raise IgnoreItemError()
            return item

    async def succes_callback(item: MyItem):
        SUCCESS.append(item)

    SUCCESS: typing.List[MyItem] = []

    manager = ItemManager(success_callback=succes_callback)
    manager.middlewares.append(MyMiddleWare())
    items: typing.List[Item] = [
        MyItem(library_name="scrapyio"),
        MyItem(library_name="scrapy"),
    ]
    await manager.process_items(items=items)
    assert len(SUCCESS) == 1
    assert SUCCESS[0].library_name == "scrapyio"
    item_added = await manager._send_single_item_via_middlewares(
        MyItem(library_name="scrapy")
    )
    assert not item_added
