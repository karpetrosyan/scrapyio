import sys
import typing

import pytest

from scrapyio.http import Request

P = typing.ParamSpec("P")


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def clear_sys_modules():
    names_to_del = set()
    for key in sys.modules:
        if key.startswith("scrapyio"):
            names_to_del.add(key)
    for name in names_to_del:
        del sys.modules[name]


@pytest.fixture(scope="session")
def app():
    from tests.server import app

    return app


@pytest.fixture(scope="session")
def mocked_request(app):
    def _inner_decorator(*args, **kwargs) -> Request:
        kwargs["base_url"] = "https://scrapyio-example.com"
        kwargs["app"] = app

        if "method" not in kwargs:
            kwargs["method"] = "GET"
        return Request(*args, **kwargs)

    return _inner_decorator
