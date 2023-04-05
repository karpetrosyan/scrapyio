from scrapyio import BaseSpider


class Spider(BaseSpider):
    start_requests = []

    async def parse(self, response):
        yield None
