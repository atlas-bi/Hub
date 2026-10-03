"""Database-free tests for scheduler-to-runner API dispatch."""

import logging
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from runner import create_app, db
from runner.scripts.task_runner import Runner
from runner.web import web as runner_web


def test_query_route_queues_numeric_task_id(monkeypatch) -> None:
    """The scheduler query route dispatches the integer task ID."""
    app = create_app()
    task = SimpleNamespace(id=42, status_id=0)
    query = Mock()

    def filtered_query(**filters):
        return SimpleNamespace(first=lambda: task if filters.get("id") == 42 else None)

    query.filter_by.side_effect = filtered_query
    future = SimpleNamespace(add_done_callback=Mock())
    submit = Mock(return_value=future)

    with app.app_context():
        monkeypatch.setattr(runner_web.Task, "query", query, raising=False)
        monkeypatch.setattr(db.session, "add", Mock())
        monkeypatch.setattr(db.session, "commit", Mock())
        monkeypatch.setattr(runner_web, "executor", SimpleNamespace(submit=submit))

        response = app.test_client().get("/api/run?task_id=42")

    assert response.status_code == 200
    assert response.json == {"message": "runner completed."}
    query.filter_by.assert_called_once_with(id=42)
    submit.assert_called_once_with(Runner, 42)
    future.add_done_callback.assert_called_once()


@pytest.mark.parametrize(
    ("path", "task_id"),
    [("/api/run?task_id=invalid", "invalid"), ("/api/invalid", "invalid")],
)
def test_run_routes_reject_non_numeric_task_ids(monkeypatch, path, task_id) -> None:
    """Both runner entry points reject invalid IDs before querying the DB."""
    app = create_app()
    query = Mock()
    query.filter_by.side_effect = lambda **filters: SimpleNamespace(first=lambda: None)

    with app.app_context():
        monkeypatch.setattr(runner_web.Task, "query", query, raising=False)
        monkeypatch.setattr(db.session, "add", Mock())
        monkeypatch.setattr(db.session, "commit", Mock())
        monkeypatch.setattr(
            runner_web,
            "executor",
            SimpleNamespace(submit=Mock(return_value=SimpleNamespace(add_done_callback=Mock()))),
        )
        response = app.test_client().get(path)

    assert response.json == {"error": f"Invalid task id {task_id}."}
    query.filter_by.assert_not_called()


def test_future_exception_is_logged(caplog) -> None:
    """Exceptions from queued runner futures are logged with the task ID."""
    future = SimpleNamespace(exception=lambda: RuntimeError("runner failed"))

    with caplog.at_level(logging.ERROR):
        runner_web._log_runner_future_exception(42, future)

    assert "Runner task 42 failed after queueing." in caplog.text


def test_future_exception_probe_does_not_swallow_keyboard_interrupt() -> None:
    """Future inspection does not suppress process-control exceptions."""
    future = SimpleNamespace(exception=Mock(side_effect=KeyboardInterrupt))

    with pytest.raises(KeyboardInterrupt):
        runner_web._log_runner_future_exception(42, future)
