"""Regression tests for recovering from transient SQLAlchemy failures."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import OperationalError, PendingRollbackError

import config
from runner import create_app
from runner.scripts import task_runner


def _operational_error() -> OperationalError:
    return OperationalError("SELECT 1", {}, Exception("connection lost"))


def _pending_rollback_error() -> PendingRollbackError:
    return PendingRollbackError("transaction is inactive")


def test_database_pool_checks_and_recycles_connections() -> None:
    """Database pools validate connections and recycle old ones."""
    assert config.Config.SQLALCHEMY_ENGINE_OPTIONS["pool_pre_ping"] is True
    assert config.Config.SQLALCHEMY_ENGINE_OPTIONS["pool_recycle"] == 1800


@pytest.mark.parametrize(
    "error_factory", [_operational_error, _pending_rollback_error], ids=["operational", "pending"]
)
def test_runner_retries_task_lookup_after_rolling_back(monkeypatch, tmp_path, error_factory) -> None:
    """A transient task lookup error is rolled back and retried once."""
    task = SimpleNamespace(
        id=42,
        status_id=0,
        last_run_job_id=None,
        last_run=None,
        project=SimpleNamespace(name="Project"),
        name="Task",
        processing_type_id=None,
    )
    app = create_app()
    app.config["RUNNER_TEMP_PATH"] = str(tmp_path)

    class RetryQuery:
        calls = 0

        def filter_by(self, **_kwargs):
            return self

        def first(self):
            self.calls += 1
            if self.calls == 1:
                raise error_factory()
            return task

    class StopAtParameterLoad(Exception):
        pass

    def stop_before_database_use(*_args):
        raise StopAtParameterLoad

    with app.app_context():
        query = RetryQuery()
        monkeypatch.setattr(task_runner.Task, "query", query, raising=False)
        rollback = Mock()
        monkeypatch.setattr(task_runner.db.session, "rollback", rollback)
        monkeypatch.setattr(task_runner.db.session, "commit", lambda: None)
        monkeypatch.setattr(task_runner, "RunnerLog", lambda *args: None)
        monkeypatch.setattr(task_runner, "system_monitor", lambda: None)
        monkeypatch.setattr(task_runner, "ParamLoader", stop_before_database_use)

        with pytest.raises(StopAtParameterLoad):
            task_runner.Runner(42)

        assert query.calls == 2
        rollback.assert_called_once_with()
        assert len(list(Path(tmp_path, "Project", "Task").iterdir())) == 1
