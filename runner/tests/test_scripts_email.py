"""Regression tests for runner email messages."""

from types import SimpleNamespace
from unittest.mock import Mock

from flask import Flask

from runner.scripts import em_messages, task_runner
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


def test_completion_email_is_suppressed_for_header_only_csv(monkeypatch, tmp_path) -> None:
    """Do not send a completion email when its CSV contains only a header."""
    task = SimpleNamespace(
        id=12,
        project_id=9,
        project=SimpleNamespace(id=9, name="Clinic"),
        name="Daily import",
        last_run_job_id="run-1",
        email_completion=1,
        email_error=0,
        email_completion_file=1,
        email_completion_file_embed=1,
        email_completion_dont_send_empty_file=1,
        email_completion_recipients="ops@example.test",
        email_completion_subject=None,
        email_completion_message=None,
        email_completion_log=0,
        source_query_include_header=1,
    )
    csv_path = tmp_path / "completion.csv"
    csv_path.write_text("patient_id,status\n")

    task_log = Mock()
    task_log.query.filter_by.return_value.order_by.return_value.all.return_value = []
    monkeypatch.setattr(task_runner, "TaskLog", task_log)
    send_email = Mock()
    monkeypatch.setattr(task_runner, "RunnerLog", Mock())
    monkeypatch.setattr(task_runner, "Smtp", send_email)

    runner = object.__new__(task_runner.Runner)
    runner.task = task
    runner.run_id = None
    runner.output_files = [str(csv_path)]
    runner.param_loader = Mock()

    app = Flask(__name__)
    app.config.update(WEB_HOST="https://hub.example.test", ORG_NAME="Example Org")
    with app.app_context():
        runner._Runner__send_email()

    send_email.assert_not_called()
