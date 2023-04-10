"""
This module contains the scrapyio 'Request' creation
tests, which ensure that the 'Request' creation and
configuration overriding functions as expected.
"""

import pytest

from scrapyio.http import Request, clean_up_response
from scrapyio.settings import CONFIGS


def test_request_creation():
    with pytest.raises(TypeError):
        Request()
    with pytest.raises(TypeError):
        Request(url="...")


def test_request_default_configs(monkeypatch):
    req = Request(url="...", method="...", proxies={"all": "..."})
    assert req.proxies == {"all": "..."}
    monkeypatch.setattr(CONFIGS, "DEFAULT_PROXIES", {"http": "..."})
    req1 = Request(url="...", method="...")
    assert req1.proxies == {"http": "..."}


@pytest.mark.anyio
async def test_request_clean_up():
    success = False

    async def async_generator():
        nonlocal success
        success = True
        yield None

    gen = async_generator()
    await gen.__anext__()
    assert success
    await clean_up_response(response_gen=gen)


@pytest.mark.anyio
async def test_request_clean_up_invalid_generator():
    async def two_yields_generator():
        yield None
        yield None

    gen = two_yields_generator()
    await gen.__anext__()
    with pytest.raises(AssertionError):
        await clean_up_response(response_gen=gen)
