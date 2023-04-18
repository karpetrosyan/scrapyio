# * ScrapyioException
# +   EngineException
# +   DownloaderException
# -       IgnoreRequestException
# -       DownloadFailedException
# +   ItemManagerException
# -       IgnoreItemException
# +   SpiderException
# -       InvalidParseMethodException
# -       InvalidYieldValueException
# -       ParseFailedException
# +   SpiderNotFoundException


class ScrapyioException(Exception):
    ...


class EngineException(ScrapyioException):
    ...


class DownloaderException(ScrapyioException):
    ...


class IgnoreRequestException(DownloaderException):
    ...


class DownloadFailedException(DownloaderException):
    ...


class ItemManagerException(ScrapyioException):
    ...


class IgnoreItemException(ItemManagerException):
    ...


class SpiderException(ScrapyioException):
    ...


class InvalidParseMethodException(SpiderException):
    ...


class InvalidYieldValueException(SpiderException):
    ...


class ParseFailedException(SpiderException):
    ...


class SpiderNotFoundException(ScrapyioException):
    ...
