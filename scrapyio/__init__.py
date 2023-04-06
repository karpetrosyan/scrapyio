import sys
from logging import config
from logging import getLogger

from scrapyio.settings import CONFIGS

from .downloader import Downloader
from .downloader import SessionDownloader
from .exceptions import IgnoreRequestError
from .item_loaders import JSONLoader
from .items import Item
from .items import ItemManager
from .spider import BaseSpider
from .spider import Request
from .spider import Response

config.dictConfig(CONFIGS.DEFAULT_LOGGING_CONFIG)
logger = getLogger("scrapyio")
