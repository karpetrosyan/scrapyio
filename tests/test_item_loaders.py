import builtins
import datetime
import importlib
import json
import os
import tempfile
import types
import typing
from pathlib import Path

import pytest

from scrapyio import items
from scrapyio.item_loaders import CSVLoader
from scrapyio.item_loaders import JSONLoader
from scrapyio.item_loaders import SQLAlchemyLoader
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


@pytest.mark.anyio
async def test_csv_loader():
    class MyItem(Item):
        library_name: str

    filename = tempfile.mktemp()
    loader = CSVLoader(filename=filename)
    manager = ItemManager(loaders=[loader])
    try:
        await manager.process_items(
            [MyItem(library_name="scrapyio"), MyItem(library_name="scrapyio")]
        )
    finally:
        loader = manager.loaders[0]
        await loader.close()
        with open(filename, mode="r", encoding="utf-8") as f:
            assert f.readline() == "library_name\n"
            assert f.readline() == "scrapyio\n"
            assert f.readline() == "scrapyio\n"
        os.remove(filename)


@pytest.mark.anyio
async def test_sqlalchemy_fields_mapper():
    class MyItem(Item):
        a: int
        b: float
        c: str
        d: datetime.datetime

    item = MyItem(a=1, b=1.1, c="1.1", d=datetime.datetime.now())
    mapped_fields = await SQLAlchemyLoader._get_mapped_fields(
        SQLAlchemyLoader, item=item
    )
    mapped_a, mapped_b, mapped_c, mapped_d = mapped_fields
    from sqlalchemy import DateTime
    from sqlalchemy import Float
    from sqlalchemy import Integer
    from sqlalchemy import String

    assert mapped_a.type.__class__ == Integer
    assert mapped_b.type.__class__ == Float
    assert mapped_c.type.__class__ == String
    assert mapped_d.type.__class__ == DateTime


@pytest.mark.anyio
async def test_sqlalchemy_table_creation(monkeypatch):
    from sqlalchemy import Table

    with tempfile.TemporaryDirectory() as path:
        monkeypatch.syspath_prepend(path=path)
        loader = SQLAlchemyLoader(
            url="sqlite+aiosqlite:///" + str(Path(path) / "data.db")
        )
        try:
            await loader.open()

            class MyItem(Item):
                a: int

            await loader._create_table_from_item(MyItem(a=1))
            assert len(loader.existing_tables) == 1
            assert isinstance(loader.existing_tables["MyItem"], Table)
        finally:
            await loader.close()


@pytest.mark.anyio
async def test_sqlalchemy_loader(monkeypatch):
    class MyItem(Item):
        a: int
        b: str

    with tempfile.TemporaryDirectory() as path:
        monkeypatch.syspath_prepend(path=path)

        loader = SQLAlchemyLoader(
            url="sqlite+aiosqlite:///" + str(Path(path) / "data.db")
        )
        item_manager = ItemManager(loaders=[loader])
        try:
            await item_manager.process_items([MyItem(a=1, b="2")])
        finally:
            for loader in item_manager.loaders:
                await loader.close()
        import sqlite3

        conn = sqlite3.connect(database=str(Path(path) / "data.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM MyItem;")
        assert cursor.fetchone() == (1, 1, "2")
