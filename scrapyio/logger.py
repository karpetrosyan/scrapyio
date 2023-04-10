from logging import config, getLogger

from scrapyio.settings import CONFIGS

config.dictConfig(CONFIGS.DEFAULT_LOGGING_CONFIG)
first_logger_name = CONFIGS.DEFAULT_LOGGING_CONFIG["loggers"].keys()[0]
logger = getLogger(first_logger_name)
