from pathlib import Path

import click

from scrapyio import default_configs
from scrapyio.settings import SETTINGS_FILE_NAME


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


@main.command()
def run(test):
    print("main")
