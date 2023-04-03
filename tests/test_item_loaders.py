import builtins
import importlib
import json
import os
import tempfile
import types
import typing

import pytest

from scrapyio import items
from scrapyio.item_loaders import JSONLoader
from scrapyio.items import Item
from scrapyio.items import ItemManager


@pytest.mark.anyio
async def test_loader_set_up():
    class MyItem(Item):
        library_name: str

    filename = tempfile.mktemp()
    loader = JSONLoader(filename=filename)
    manager = ItemManager(loaders=[loader])
    try:
        await manager.process_items([MyItem(library_name="scrapyio")])
    finally:
        loader = manager.loaders[0]
        await loader.close()
        os.remove(filename)


@pytest.mark.anyio
async def test_json_loader_without_orjson(monkeypatch):
    old_import = builtins.__import__

    def fake_import(name: str, *args, **kwargs) -> types.ModuleType:
        if name == "orjson":
            raise ImportError()
        return typing.cast(types.ModuleType, old_import(name, *args, **kwargs))

    monkeypatch.setattr(builtins, "__import__", fake_import)
    importlib.reload(items)
    monkeypatch.setattr(builtins, "__import__", old_import)

    class MyItem(Item):
        library_name: str

    filename = tempfile.mktemp()
    loader = JSONLoader(filename=filename)
    manager = ItemManager(loaders=[loader])
    try:
        await manager.process_items([MyItem(library_name="scrapyio")])
    finally:
        loader = manager.loaders[0]
        await loader.close()
        with open(filename, mode="r", encoding="utf-8") as f:
            dumped = json.loads(f.read())
            assert len(dumped) == 1
            assert dumped[0]["library_name"] == "scrapyio"
        os.remove(filename)


@pytest.mark.anyio
async def test_json_loader():
    pytest.importorskip("orjson")

    class MyItem(Item):
        library_name: str

    filename = tempfile.mktemp()
    loader = JSONLoader(filename=filename)
    manager = ItemManager(loaders=[loader])
    try:
        await manager.process_items(
            [MyItem(library_name="scrapyio"), MyItem(library_name="scrapyio")]
        )
    finally:
        loader = manager.loaders[0]
        await loader.close()
        with open(filename, mode="r", encoding="utf-8") as f:
            content = f.read()
            dumped = json.loads(content)
            assert len(dumped) == 2
            assert dumped[0]["library_name"] == "scrapyio"
        os.remove(filename)
