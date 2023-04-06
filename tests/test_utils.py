from scrapyio.utils import first_not_none
from scrapyio.utils import load_module
from scrapyio.utils import random_filename


def test_object_loading():
    assert (
        load_module("scrapyio.middlewares.BaseMiddleWare").__name__ == "BaseMiddleWare"
    )
    assert (
        load_module("scrapyio.downloader.BaseDownloader").__name__ == "BaseDownloader"
    )
    assert load_module("scrapyio.utils.load_module").__name__ == "load_module"


def test_random_filename():
    filename = random_filename()
    assert filename.startswith("dump_")
    assert len(filename.split("_")[1]) == 4

    filename = random_filename(random_suffix_length=6)
    assert filename.startswith("dump_")
    assert len(filename.split("_")[1]) == 6


def test_first_not_none():
    assert first_not_none(1, None) == 1
    assert first_not_none(None, None) is None
    assert first_not_none(3, 1)
