from bs4 import BeautifulSoup

from scrapyio import BaseSpider, Item


class Proxy(Item):
    country: str
    ip: str
    port: int
    type: str


class Spider(BaseSpider):
    start_requests = ["https://proxylist.to/http/"]

    async def parse(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        all_rows = soup.select("tr")[1:]
        for row in all_rows:
            country = row.select_one(".country>span").text
            ip = row.select_one(".t_ip").text
            port = row.select_one(".t_port").text
            type = row.select_one(".t_type").text
            yield Proxy(country=country, ip=ip, port=port, type=type)
