from types import ModuleType

SETTINGS_FILE_NAME = "settings.py"
SETTINGS_FILE_NAME_FOR_IMPORT = "settings"

SPIDERS_FILE_NAME = "spiders.py"
SPIDERS_FILE_NAME_FOR_IMPORT = "spiders"

try:
    import sys

    sys.path.append("")
    CONFIGS: ModuleType = __import__(SETTINGS_FILE_NAME_FOR_IMPORT)
except ModuleNotFoundError:
    from scrapyio.templates import configuration_template
    CONFIGS = configuration_template
