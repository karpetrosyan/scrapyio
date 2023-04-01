from scrapyio.downloader import BaseDownloader
from scrapyio.middlewares import BaseMiddleWare
from scrapyio.utils import load_module
from scrapyio.utils import random_filename


def test_object_loading():
    assert BaseMiddleWare == load_module("scrapyio.middlewares.BaseMiddleWare")
    assert BaseDownloader == load_module("scrapyio.downloader.BaseDownloader")
    assert load_module == load_module("scrapyio.utils.load_module")


def test_random_filename():
    filename = random_filename()
    assert filename.startswith("dump_")
    assert len(filename.split("_")[1]) == 4

    filename = random_filename(random_suffix_length=6)
    assert filename.startswith("dump_")
    assert len(filename.split("_")[1]) == 6
