"""Shared test fixtures: isolate config and prompts dirs in tmp_path."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture(autouse=True)
def isolated_dirs(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    prompts_dir = tmp_path / "prompts"
    monkeypatch.setenv("PROMPT_JAR_CONFIG_DIR", str(config_dir))
    import prompt_jar.config as config_module

    config_module.CONFIG_DIR = config_dir
    config_module.PROMPTS_DIR = prompts_dir
    config_module.CONFIG_FILE = config_dir / "config.yaml"
