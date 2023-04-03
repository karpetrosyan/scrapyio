import asyncio
import typing
from pathlib import Path

import click

from scrapyio import default_configs
from scrapyio import spider_file_template
from scrapyio.engines import Engine
from scrapyio.exceptions import SpiderNotFound
from scrapyio.item_loaders import BaseLoader
from scrapyio.item_loaders import JSONLoader
from scrapyio.items import ItemManager
from scrapyio.settings import SETTINGS_FILE_NAME
from scrapyio.settings import SPIDERS_FILE_NAME


@click.group()
def main():
    ...


@main.command()
@click.argument("name")
def new(name):
    path = Path.cwd()
    dir_path = path / name
    dir_path.mkdir()
    settings_file = dir_path / SETTINGS_FILE_NAME
    settings_file.touch()
    settings_file.write_text(open(default_configs.__file__).read())
    spiders_file = dir_path / SPIDERS_FILE_NAME
    spiders_file.write_text(open(spider_file_template.__file__).read())


@main.command()
@click.argument("spider")
@click.option("-j", "--json", type=str)
def run(spider: str, json: typing.Optional[str]):
    import os
    import sys

    sys.path.append(os.getcwd())

    try:
        import spiders  # type: ignore[import]
    except ImportError:
        raise SpiderNotFound(
            "File `spiders.py` was not found, make sure you're "
            "calling scrapyio from the directory scrapyio created."
        )

    spider_class = getattr(spiders, spider, None)

    if spider_class is None:
        raise SpiderNotFound("Spider `%s` was not found in the `spiders.py` file")

    loaders: typing.List[BaseLoader] = []

    if json is not None:
        loader = JSONLoader(filename=json)
        loaders.append(loader)

    item_manager = ItemManager(loaders=loaders)
    engine = Engine(spider_class=spider_class, items_manager=item_manager)
    asyncio.run(engine.run_once())
