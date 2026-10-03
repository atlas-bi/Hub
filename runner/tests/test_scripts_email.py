"""Regression tests for runner email messages."""

from unittest.mock import Mock

import pytest

from runner.extensions import db
from runner.model import Task
from runner.scripts import em_messages
from runner.scripts.em_messages import RunnerException

from .conftest import create_demo_task


def test_error_email_links_use_configured_web_host(client_fixture, monkeypatch) -> None:
    """Error-email links point to this Hub instance."""
    _, task_id = create_demo_task()
    task = Task.query.filter_by(id=task_id).one()
    task.email_error = 1
    task.email_error_recipients = "ops@example.test"
    db.session.commit()

    send_email = Mock()
    monkeypatch.setattr(em_messages, "Smtp", send_email)
    host = client_fixture.application.config["WEB_HOST"].rstrip("/")

    with pytest.raises(RunnerException):
        RunnerException(task, None, 18, "test failure")

    message = send_email.call_args.kwargs["message"]
    assert f'href="{host}/project/{task.project_id}"' in message
    assert f'href="{host}/task/{task.id}"' in message
