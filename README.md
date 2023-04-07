Scrapyio is a web scraping framework that is asynchronous, fast, and easy to use.

---

Install `scrapyio` using pip:

```shell 
$ pip install scrapyio
```

Let's begin with the most basic examples.

```python
from scrapyio import BaseSpider

class Spider(BaseSpider):
    start_requests = ["https://scrapyio-example.com"]

    async def parse(self, response):
        print("I have received the response!!", response)
        yield None

```

First, create your `BaseSpider` subclass and name it (in this case, **Spider**).
You must instruct scrapyio on where to begin the requests, i.e. the urls to be scraped.

**Things to keep in mind**
- `start_requests` is a class variable that instructs scrapyio to scrape these urls during the first `iteration`.
- `parse` is an asynchronous generator method with a single argument, `response`, which is an HTTP response object containing the page content to be scraped.
- `iteration` Scrapyio is an asynchronous framework, so if you populate the start requests variable with a thousand URLs, they will be handled concurrently by the Python asyncio framework. So let's call the url sending process an `iteration`.

## Requests

As you know, you can pass the url string in start requests to tell `Scrapyio` which content you want to download; however, some websites require additional **headers** to function properly; therefore, we can pass `Request` objects explicitly rather than only strings.

so we can replace
```python
start_requests = ["https://scrapyio-example.com"]
```

with

```python
start_requests = [Request(url="https://scrapyio-example.com", method="GET", headers={"custom-header": "test"})]
```

If we use the `Request` object directly, we can specify many request-specific parameters such as `proxies`, `authorization`, `headers`, `cookies`, whether to `follow-redirect` or not, and so on.

There is more complex `Request` object.
```python
from scrapyio import Request
start_request = [
    Request(
        url="https://scrapyio-example.com",
        headers={"custom-key": "custom-value"},
        proxies={"http": "...", "https": "..."},
        cookies={"cookie-key": "cookie-value"},
        follow_redirects=True,
        verify=False
    )
]
```

## Parsing

After you've built your `Request` with all of the necessary headers, data, and so on, you should write your parsing logic; every response that is successfully installed will call your spider's parse method, which will return the response that was downloaded.

```python
class Spider(BaseSpider):
    start_requests = ["https://www.scrapethissite.com/pages/simple/"]

    async def parse(self, response):
        print("I have received the response!!", response)
        yield None
```

`Scrapyio` is a parser free framework and let's you use any parser you want, in our case, we will use `beautifulsoup` library

```python
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
```

It's natural to be confused if you've never used `beautifulsoup` before, but the parsing process isn't particularly important; you can parse however you want, using python `regex`, parsers, or any other tool.

In this case, we're using Python's **yield** syntax to tell `Scrapyio` which Item to process and possibly save in the future.

So we get a `Country` instance, which is also a `pydantic` subclass.
Scrapyio validates and serializes the data parsed from the website using `Pydantic`.

```python
from scrapyio import Item
class Country(Item):
    name: str
    population: int
    capital: str
    area: float
```
**ANDDDDD..... THAT'S ALL**.

## Running

Now you can run scrapyio and tell him to save the items as `JSON`, `CSV`, or in any `SQLAlchemy`-supported database.
For this, you can use the scrapyio command line tool.

```shell
$ scrapyio run --help
Usage: scrapyio run [OPTIONS] SPIDER

Options:
  -j, --json TEXT  Json file path
  -c, --csv TEXT   Csv file path
  -s, --sql TEXT   SQL URI supported by SQLAlchemy
  --help           Show this message and exit.
```

Let's run `scrapyio` and export data in `JSON` and `CSV` formats.
```shell
$ scrapyio run Spider --json data.json --csv data.csv
```

data.json
```json
[
{
  "name": "Andorra",
  "population": 84000,
  "capital": "Andorra la Vella",
  "area": 468.0
},
{
  "name": "United Arab Emirates",
  "population": 4975593,
  "capital": "Abu Dhabi",
  "area": 82880.0
},
...
]
```

data.csv
```csv
name,population,capital,area
Andorra,84000,Andorra la Vella,468.0
United Arab Emirates,4975593,Abu Dhabi,82880.0
Afghanistan,29121286,Kabul,647500.0
Antigua and Barbuda,86754,St. John's,443.0
Anguilla,13254,The Valley,102.0
```

Alternatively, we can save the data to a PostgreSQL database.
```shell
$ scrapyio run Spider --sql postgresql+asyncpg://test:test@127.0.0.1:5432/postgres
```

Then select it in the psql command tool.

```
postgres=# select * from "Mytable";
 id  |                     name                     | population |       capital       |   area   
-----+----------------------------------------------+------------+---------------------+----------
   1 | Andorra                                      |      84000 | Andorra la Vella    |      468
   2 | United Arab Emirates                         |    4975593 | Abu Dhabi           |    82880
   3 | Afghanistan                                  |   29121286 | Kabul               |   647500
   4 | Antigua and Barbuda                          |      86754 | St. John's          |      443
   5 | Anguilla                                     |      13254 | The Valley          |      102
   6 | Albania                                      |    2986952 | Tirana              |    28748
   7 | Armenia                                      |    2968000 | Yerevan             |    29800
   8 | Angola                                       |   13068161 | Luanda              |  1246700
   9 | Antarctica                                   |          0 | None                | 14000000
```
