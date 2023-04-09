import sys
from logging import config, getLogger

from scrapyio.settings import CONFIGS

from .downloader import Downloader, SessionDownloader
from .exceptions import IgnoreRequestError
from .item_loaders import JSONLoader
from .items import Item, ItemManager
from .spider import BaseSpider, Request, Response

config.dictConfig(CONFIGS.DEFAULT_LOGGING_CONFIG)
logger = getLogger("scrapyio")
