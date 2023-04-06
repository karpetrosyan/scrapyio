import builtins

from scrapyio import items
from scrapyio.items import build_items_middlewares_chain
from scrapyio.items import orjson_dumps_wrapper
from scrapyio.settings import CONFIGS
from pydantic import BaseModel
import importlib
from scrapyio.items import Item
import orjson

class TestItem(BaseModel):
    num: int

class TestMiddleWare:
    ...

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
