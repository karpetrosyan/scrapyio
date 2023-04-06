"""
This module contains the scrapyio 'cli' unit tests.
These tests ensure that the cli commands work as expected.
"""
import os
import tempfile
from pathlib import Path

from click.testing import CliRunner

from scrapyio.cli import cli
from scrapyio.templates import configuration_template
from scrapyio.templates import spider_file_template


def test_scrapyio_new_command():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as temp_dir:
        with runner.isolated_filesystem(temp_dir=temp_dir):
            result = runner.invoke(cli, ["new", "testproject"])
            assert not result.exception
        path = Path(temp_dir)

        for i in path.iterdir():
            path = i

        project = path / "testproject"
        assert project.is_dir()
        settings_file = project / "settings.py"
        assert settings_file.is_file()
        template_settings = open(
            configuration_template.__file__, encoding="utf-8"
        ).read()
        assert settings_file.read_text(encoding="utf-8") == template_settings
        template_spiders = open(spider_file_template.__file__, encoding="utf-8").read()
        spiders_file = project / "spiders.py"
        assert spiders_file.is_file()
        assert spiders_file.read_text(encoding="utf-8") == template_spiders


def test_scrapyio_new_command_without_name():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as temp_dir:
        with runner.isolated_filesystem(temp_dir=temp_dir):
            result = runner.invoke(cli, ["new"])
            assert result.exception

# TODO: add integration tests for scrapyio run command