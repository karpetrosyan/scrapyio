import asyncio
import logging
import typing

import click

log = logging.getLogger("scrapyio")


@click.group()
def cli():
    ...


@cli.command()
@click.argument("name")
def new(name):
    from pathlib import Path

    from scrapyio.settings import SETTINGS_FILE_NAME
    from scrapyio.settings import SPIDERS_FILE_NAME
    from scrapyio.templates import configuration_template
    from scrapyio.templates import spider_file_template

    path = Path.cwd()
    dir_path = path / name
    dir_path.mkdir()
    settings_file = dir_path / SETTINGS_FILE_NAME
    settings_file.touch()
    settings_file.write_text(open(configuration_template.__file__).read())
    spiders_file = dir_path / SPIDERS_FILE_NAME
    spiders_file.write_text(open(spider_file_template.__file__).read())


@cli.command()
@click.argument("spider")
@click.option("-j", "--json", type=str)
@click.option("-c", "--csv", type=str)
@click.option("-s", "--sql", type=str)
def run(
    spider: str,
    json: typing.Optional[str],
    csv: typing.Optional[str],
    sql: typing.Optional[str],
):
    from scrapyio.engines import Engine
    from scrapyio.exceptions import SpiderNotFound
    from scrapyio.item_loaders import BaseLoader
    from scrapyio.item_loaders import CSVLoader
    from scrapyio.item_loaders import JSONLoader
    from scrapyio.item_loaders import SQLAlchemyLoader
    from scrapyio.items import ItemManager

    log.info("Running the spider")


    try:
        log.debug("Trying to import spiders file")
        import spiders  # type: ignore[import]

        log.debug("Spiders file was imported")
    except ImportError:
        log.debug("When attempting to import the spiders file, an exception was raised")
        raise SpiderNotFound(
            "File `spiders.py` was not found, make sure you're "
            "calling scrapyio from the directory scrapyio created."
        )

    spider_class = getattr(spiders, spider, None)

    if spider_class is None:
        raise SpiderNotFound("Spider `%s` was not found in the `spiders.py` file")

    loaders: typing.List[BaseLoader] = []
    loader: BaseLoader

    if json is not None:
        log.debug("Creating the JSON loader")
        loader = JSONLoader(filename=json)
        loaders.append(loader)

    if csv is not None:
        log.debug("Creating the CSV loader")
        loader = CSVLoader(filename=csv)
        loaders.append(loader)

    if sql is not None:
        log.debug("Creating the SQL loader")
        loader = SQLAlchemyLoader(url=sql)
        loaders.append(loader)

    item_manager = ItemManager(loaders=loaders)
    log.debug("Creating the Engine instance")
    engine = Engine(spider_class=spider_class, items_manager=item_manager)
    log.info("Running engine")
    asyncio.run(engine.run())
