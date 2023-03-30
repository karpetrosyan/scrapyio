import pytest

from tests.server import app as _app


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def app():
    return _app
