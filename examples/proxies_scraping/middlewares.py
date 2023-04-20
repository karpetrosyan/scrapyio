import httpx

from scrapyio.exceptions import IgnoreItemException
from scrapyio.item_middlewares import BaseItemMiddleWare


class ProxyCheckMiddleWare(BaseItemMiddleWare):
    async def process_item(self, item) -> None:
        scheme = item.type.lower()
        uri = f"{scheme}://{item.ip}:{item.port}"
        async with httpx.AsyncClient(proxies={"all:///": uri}) as cl:
            try:
                response = await cl.get("http://google.com")
                if not response.is_success:
                    raise IgnoreItemException
            except BaseException:
                raise IgnoreItemException
