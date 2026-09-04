"""Configuration tests."""

from importlib import reload
from pathlib import Path

import config


def test_runner_temp_path_defaults_to_runner_temp() -> None:
    """Use the existing runner temp directory by default."""
    assert Path(config.Config.RUNNER_TEMP_PATH) == Path(__file__).parents[2] / "runner" / "temp"


def test_runner_temp_path_can_be_overridden(monkeypatch, tmp_path) -> None:
    """Read the runner temp directory from the environment."""
    monkeypatch.setenv("RUNNER_TEMP_PATH", str(tmp_path))
    reload(config)

    assert str(tmp_path) == config.Config.RUNNER_TEMP_PATH
    monkeypatch.delenv("RUNNER_TEMP_PATH")
    reload(config)
