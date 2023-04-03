import typing
from types import ModuleType

from . import default_configs

LOADED = False

SETTINGS_FILE_NAME = "settings.py"
SETTINGS_FILE_NAME_FOR_IMPORT = "settings"

SPIDERS_FILE_NAME = "spiders.py"
SPIDERS_FILE_NAME_FOR_IMPORT = "spiders"

CONFIGS_TO_LOAD = (
    "PROXY_CHAIN",
    "ITEM_MIDDLEWARES",
    "MIDDLEWARES",
    "REQUEST_TIMEOUT",
    "DEFAULT_HEADERS",
    "DEFAULT_COOKIES",
    "DEFAULT_PARAMS",
    "DEFAULT_AUTH",
    "DEFAULT_VERIFY_SSL",
    "DEFAULT_CERTS",
    "HTTP_1",
    "HTTP_2",
    "DEFAULT_PROXIES",
    "FOLLOW_REDIRECTS",
    "DEFAULT_TRUST_ENV",
    "ENABLE_STREAM_BY_DEFAULT",
)


def load_settings(path: typing.Optional[str] = None):
    global LOADED
    if LOADED:
        return
    custom_configs: typing.Union[ModuleType, object]
    try:
        custom_configs = __import__(path or SETTINGS_FILE_NAME_FOR_IMPORT)
    except ModuleNotFoundError:
        custom_configs = object()

    for attr in CONFIGS_TO_LOAD:
        value = getattr(custom_configs, attr, None)
        if value:
            setattr(default_configs, attr, value)
    LOADED = True
