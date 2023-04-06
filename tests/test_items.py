import builtins
import tempfile

from scrapyio import items
from scrapyio.items import build_items_middlewares_chain
from scrapyio.items import orjson_dumps_wrapper
from scrapyio.settings import CONFIGS
from pydantic import BaseModel
from scrapyio.items import ItemManager
from scrapyio.item_middlewares import BaseItemMiddleWare
from scrapyio.item_loaders import JSONLoader
from scrapyio.item_loaders import ProxyLoader
import importlib
from scrapyio.exceptions import IgnoreItemError
from scrapyio.items import Item
import orjson
import pytest

class TestItem(BaseModel):
    num: int

class TestMiddleWare:
    ...

class TestItemMiddleWare(BaseItemMiddleWare):

    async def process_item(self, item: Item):
        ...

class TestIgnoreItemMiddleWare(BaseItemMiddleWare):

    async def process_item(self, item: Item):
        raise IgnoreItemError()

def test_build_items_middleware(monkeypatch):
    monkeypatch.setattr(CONFIGS, "ITEM_MIDDLEWARES", ["tests.test_items.TestMiddleWare",
                                                      "tests.test_items.TestMiddleWare"])
    middlewares =build_items_middlewares_chain()

    assert len(middlewares) == 2
    m1, m2 = middlewares
    assert isinstance(m1, TestMiddleWare)
    assert isinstance(m2, TestMiddleWare)

def test_orjson_dumping():
    expected_string = '\n'.join([
        "{",
        '  "test": "test"',
        "}"
    ])
    actual_string = orjson_dumps_wrapper({"test": "test"})
    assert actual_string == expected_string


def test_orjson_dumping_with_option():
    expected_string = '\n'.join([
        "{",
        '  "test": "test"',
        "}\n"
    ])
    actual_string = orjson_dumps_wrapper({"test": "test"}, option=orjson.OPT_APPEND_NEWLINE)
    assert actual_string == expected_string


def test_item_without_orjson(monkeypatch):
    original_import = builtins.__import__
    def mocked_import(name, *args, **kwargs):
        if name == 'orjson':
            raise ImportError
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", mocked_import)
    importlib.reload(items)


@pytest.mark.anyio
async def test_item_manager_send_single_item():
    manager = ItemManager()
    await manager._send_single_item_via_middlewares(item=TestItem(num=5))

@pytest.mark.anyio
async def test_item_manager_success_callback():
    successes = []

    async def success_callback(item):
        successes.append(item)
    manager = ItemManager(success_callback=success_callback)
    await manager._send_single_item_via_middlewares(item=TestItem(num=5))
    assert len(successes)
    assert isinstance(successes[0], TestItem)

@pytest.mark.anyio
async def test_item_manager_middlewares(monkeypatch):
    monkeypatch.setattr(CONFIGS, "ITEM_MIDDLEWARES", ["tests.test_items.TestItemMiddleWare"])
    manager = ItemManager()
    item = await manager._send_single_item_via_middlewares(item=TestItem(num=5))
    assert item

@pytest.mark.anyio
async def test_item_manager_middlewares_ignoring(monkeypatch):
    monkeypatch.setattr(CONFIGS, "ITEM_MIDDLEWARES", ["tests.test_items.TestIgnoreItemMiddleWare"])
    manager = ItemManager()
    item = await manager._send_single_item_via_middlewares(item=TestItem(num=5))
    assert item is None

@pytest.mark.anyio
async def test_item_manager_middlewares_ignoring_callback(monkeypatch):
    monkeypatch.setattr(CONFIGS, "ITEM_MIDDLEWARES", ["tests.test_items.TestIgnoreItemMiddleWare"])
    failed = []
    async def ignoring_callback(item, md):
        failed.append((item, md))
    manager = ItemManager(ignoring_callback=ignoring_callback)
    item = await manager._send_single_item_via_middlewares(item=TestItem(num=5))
    assert item is None
    assert len(failed) == 1
    assert isinstance(failed[0][0], TestItem)
    assert isinstance(failed[0][1], TestIgnoreItemMiddleWare)

@pytest.mark.anyio
async def test_item_manager_with_loaders():
    manager = ItemManager(loaders=[JSONLoader(), JSONLoader()])
    assert len(manager.loaders) == 2
    l1, l2 = manager.loaders
    assert isinstance(l1, ProxyLoader)
    assert isinstance(l2, ProxyLoader)


@pytest.mark.anyio
async def test_item_manager_items_sending():
    f1, f2 = tempfile.mktemp(), tempfile.mktemp()
    items = [TestItem(num=2), TestItem(num=2)]
    manager = ItemManager(loaders=[JSONLoader(filename=f1), JSONLoader(filename=f2)])
    clean_items = await manager._send_items_via_middlewares(items)
    assert len(clean_items) == 2

@pytest.mark.anyio
async def test_item_manager_handling():
    f1, f2 = tempfile.mktemp(), tempfile.mktemp()
    items = [TestItem(num=2), TestItem(num=2)]
    manager = ItemManager(loaders=[JSONLoader(filename=f1), JSONLoader(filename=f2)])
    await manager.process_items(items)
