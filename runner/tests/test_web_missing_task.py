"""Database-free tests for requests that reference unknown tasks."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from flask import Flask

from runner.scripts import task_runner
from runner.web import web


@pytest.mark.parametrize("path", ["/api/999999", "/api/run?task_id=999999"])
def test_missing_task_api_returns_404_json(monkeypatch, path: str) -> None:
    """Unknown task IDs return a 404 without queueing runner work."""
    task_query = Mock()
    task_query.filter_by.return_value.first.return_value = None
    submit = Mock()
    monkeypatch.setattr(web, "Task", SimpleNamespace(query=task_query))
    monkeypatch.setattr(web, "executor", SimpleNamespace(submit=submit))
    app = Flask(__name__)
    app.register_blueprint(web.web_bp)

    response = app.test_client().get(path)

    assert response.status_code == 404
    assert response.get_json() == {"error": "Task 999999 not found."}
    task_query.filter_by.assert_called_once_with(id=999999)
    submit.assert_not_called()


def test_runner_rejects_missing_task_before_side_effects(monkeypatch) -> None:
    """Runner raises a clear error before touching a missing task."""
    task_query = Mock()
    task_query.filter_by.return_value.first.return_value = None
    monkeypatch.setattr(task_runner, "Task", SimpleNamespace(query=task_query))

    with pytest.raises(ValueError, match="Task 999999 not found"):
        task_runner.Runner(999999)

    task_query.filter_by.assert_called_once_with(id=999999)
