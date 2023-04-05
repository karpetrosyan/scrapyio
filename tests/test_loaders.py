import pytest

from scrapyio.item_loaders import BaseLoader
from scrapyio.item_loaders import LoaderState
from scrapyio.item_loaders import ProxyLoader
from scrapyio.items import Item


class EmptyLoader(BaseLoader):
    async def open(self) -> None:
        ...

    async def dump(self, item: "Item") -> None:
        ...

    async def close(self) -> None:
        ...


@pytest.mark.anyio
async def test_proxy_loader_closing_not_opened():
    proxy_loader = ProxyLoader(loader=EmptyLoader())
    assert proxy_loader.state == LoaderState.CREATED

    with pytest.raises(
        RuntimeError,
        match=r"The loader cannot be closed because it has not yet been opened.",
    ):
        await proxy_loader.close()
