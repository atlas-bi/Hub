"""Scheduler maintenance regression tests."""

import os
import time
from pathlib import Path

from pytest import fixture

from scheduler.extensions import atlas_scheduler
from scheduler.maintenance import temp_clean


def test_temp_clean_uses_configured_runner_path(
    client_fixture: fixture, tmp_path: Path, monkeypatch: fixture
) -> None:
    """Expired run directories are removed from RUNNER_TEMP_PATH."""
    run_path = tmp_path / "Hospital Reports" / "Patient Export" / "run-1"
    run_path.mkdir(parents=True)
    (run_path / "report.csv").write_text("patient_id,status\n", encoding="utf8")
    old_time = time.time() - 7201
    os.utime(run_path, (old_time, old_time))
    monkeypatch.setitem(atlas_scheduler.app.config, "RUNNER_TEMP_PATH", str(tmp_path))

    temp_clean()

    assert not run_path.exists()
