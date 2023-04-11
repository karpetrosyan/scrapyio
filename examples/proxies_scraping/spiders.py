from scrapyio import BaseSpider, Item, Request


class Proxy(Item):
    country: str
    ip: str
    port: int
    type: str


class Spider(BaseSpider):
    start_requests = [Request("https://proxylist.to/http/", method="GET", stream=False)]

    async def parse(self, response):
        all_rows = response.soup.select("tr")[1:]
        for row in all_rows:
            country = row.select_one(".country>span").text
            ip = row.select_one(".t_ip").text
            port = row.select_one(".t_port").text
            type = row.select_one(".t_type").text
            yield Proxy(country=country, ip=ip, port=port, type=type)
