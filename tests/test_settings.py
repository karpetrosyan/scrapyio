import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from scrapyio import default_configs
from scrapyio import settings
from scrapyio.settings import load_settings


def test_load_settings(monkeypatch):
    monkeypatch.setattr(settings, "LOADED", False)
    saved_defaults = open(default_configs.__file__).read()

    with NamedTemporaryFile(mode="w+", suffix=".py", dir=".", delete=False) as file:
        path = Path(file.name)
        import_name = path.name[:-3]  # without .py suffix
        monkeypatch.syspath_prepend(path=path.parent)
        file.write(saved_defaults)
        file.flush()
    try:
        module = __import__(import_name)
        module.REQUEST_TIMEOUT = 10
        module.MIDDLEWARES = ["NOT A PATH"]
        load_settings(import_name)
        assert default_configs.REQUEST_TIMEOUT == 10
        assert default_configs.MIDDLEWARES == ["NOT A PATH"]
        module.REQUEST_TIMEOUT = 5
        load_settings(import_name)
        assert default_configs.REQUEST_TIMEOUT != 5
    finally:
        os.remove(path)


def test_load_settings_without_file(monkeypatch):
    assert not settings.LOADED
    UNEXISTING_FILE_NAME = "NOTEXISTS"
    UNEXISTING_FILE_NAME_FOR_IMPORT = "NOTEXISTS.py"
    monkeypatch.setattr(settings, "SETTINGS_FILE_NAME", UNEXISTING_FILE_NAME)
    monkeypatch.setattr(
        settings, "SETTINGS_FILE_NAME_FOR_IMPORT", UNEXISTING_FILE_NAME_FOR_IMPORT
    )
    load_settings()
