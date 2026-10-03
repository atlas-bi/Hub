"""Regression tests for runner email messages."""

from types import SimpleNamespace
from unittest.mock import Mock

from flask import Flask

from runner.scripts import em_messages
from runner.scripts.em_messages import RunnerException


def test_error_email_links_use_configured_web_host(monkeypatch) -> None:
    """Error-email links point to this Hub instance."""
    task = SimpleNamespace(
        id=12,
        project_id=34,
        project=SimpleNamespace(id=34, name="Example Project"),
        name="Example Task",
        last_run_job_id=None,
        email_error=1,
        email_error_recipients="ops@example.test",
        email_error_subject=None,
        email_error_message=None,
        email_completion_message=None,
        email_completion_log=0,
    )

    task_log = Mock()
    task_log.query.filter_by.return_value.order_by.return_value.all.return_value = []
    monkeypatch.setattr(em_messages, "TaskLog", task_log)
    monkeypatch.setattr(em_messages, "RunnerLog", Mock())
    monkeypatch.setattr(em_messages.db, "session", Mock())
    send_email = Mock()
    monkeypatch.setattr(em_messages, "Smtp", send_email)

    app = Flask(__name__)
    app.config.update(WEB_HOST="https://hub.example.test", ORG_NAME="Example Org")
    with app.app_context():
        RunnerException(task, None, 18, "test failure")

    message = send_email.call_args.kwargs["message"]
    assert 'href="https://hub.example.test/project/34"' in message
    assert 'href="https://hub.example.test/task/12"' in message
