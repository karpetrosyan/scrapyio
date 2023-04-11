from scrapyio.item_middlewares import BaseItemMiddleWare
from scrapyio.exceptions import IgnoreItemError
import httpx


class ProxyCheckMiddleWare(BaseItemMiddleWare):

    async def process_item(self, item) -> None:
        scheme = item.type.lower()
        uri = f"{scheme}://{item.ip}:{item.port}"
        async with httpx.AsyncClient(proxies={"all:///": uri}) as cl:
            try:
                response = await cl.get("http://google.com")
                if not response.is_success:
                    raise IgnoreItemError
            except:
                raise IgnoreItemError