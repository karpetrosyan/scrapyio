import asyncio

from bs4 import BeautifulSoup

from scrapyio import Request
from scrapyio.engines import Engine
from scrapyio.item_loaders import JSONLoader
from scrapyio.items import Item
from scrapyio.items import ItemManager
from scrapyio.spider import BaseSpider


class Country(Item):
    name: str
    population: int
    capital: str
    area: float


class Spider(BaseSpider):
    start_requests = [
        Request(url="https://www.scrapethissite.com/pages/simple/", method="GET")
    ]

    async def parse(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        countries = soup.select(".country")

        for country in countries:
            country_name = country.select_one(".country-name").text.strip()
            country_population = int(
                country.select_one(".country-population").text.strip()
            )
            country_capital = country.select_one(".country-capital").text.strip()
            country_area = float(country.select_one(".country-area").text.strip())

            yield Country(
                name=country_name,
                population=country_population,
                capital=country_capital,
                area=country_area,
            )


if __name__ == "__main__":
    item_manager = ItemManager(loader=JSONLoader(filename="data.json"))
    engine = Engine(items_manager=item_manager, spider_class=Spider)
    asyncio.run(engine.run())
