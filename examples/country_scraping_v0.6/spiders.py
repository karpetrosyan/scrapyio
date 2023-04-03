from bs4 import BeautifulSoup

from scrapyio import BaseSpider
from scrapyio import Item


class Country(Item):
    name: str
    population: int
    capital: str
    area: float


class Spider(BaseSpider):
    start_requests = ["https://www.scrapethissite.com/pages/simple/"]

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
