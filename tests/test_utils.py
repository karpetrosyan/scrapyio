from scrapyio.downloader import BaseDownloader
from scrapyio.middlewares import BaseMiddleWare
from scrapyio.utils import load_module


def test_object_loading():
    assert BaseMiddleWare == load_module("scrapyio.middlewares.BaseMiddleWare")
    assert BaseDownloader == load_module("scrapyio.downloader.BaseDownloader")
    assert load_module == load_module("scrapyio.utils.load_module")
