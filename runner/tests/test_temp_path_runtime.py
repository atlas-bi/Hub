"""Regression tests for the configurable runner temp directory."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from flask import Flask

from runner.web import web as runner_web


@pytest.mark.parametrize(
    ("operation", "args"),
    [
        ("send_ftp", (12, 34, 56)),
        ("send_sftp", (34, 56)),
        ("send_smb", (34, 56)),
        ("send_email", (34, 56)),
        ("get_task_file_download", (56,)),
    ],
)
def test_file_routes_use_configured_temp_path(tmp_path, monkeypatch, operation, args) -> None:
    """Manual file operations stage data below RUNNER_TEMP_PATH."""
    task = SimpleNamespace(
        name="Patient Export",
        project=SimpleNamespace(name="Hospital Reports"),
        destination_ftp_conn=object(),
        destination_sftp_conn=object(),
        destination_smb_conn=object(),
        email_completion_recipients="ops@example.test",
    )
    task_file = SimpleNamespace(
        task=task,
        job_id="run-1",
        path="archive/report.csv",
        name="report.csv",
    )
    task_query = Mock()
    task_query.filter_by.return_value.first.return_value = task
    file_query = Mock()
    file_query.filter_by.return_value.first.return_value = task_file
    monkeypatch.setattr(runner_web, "Task", SimpleNamespace(query=task_query))
    monkeypatch.setattr(runner_web, "TaskFile", SimpleNamespace(query=file_query))

    smb = Mock()
    smb.return_value.read.return_value = [SimpleNamespace(name="report.csv")]
    monkeypatch.setattr(runner_web, "Smb", smb)
    monkeypatch.setattr(runner_web, "Ftp", Mock())
    monkeypatch.setattr(runner_web, "Sftp", Mock())
    monkeypatch.setattr(runner_web, "Smtp", Mock())

    app = Flask(__name__)
    app.config.update(RUNNER_TEMP_PATH=str(tmp_path), ORG_NAME="Hospital")
    with app.app_context():
        getattr(runner_web, operation)(*args)

    expected = tmp_path / "Hospital Reports" / "Patient Export" / "run-1"
    assert smb.call_args.kwargs["directory"] == expected
    assert expected.is_dir()
