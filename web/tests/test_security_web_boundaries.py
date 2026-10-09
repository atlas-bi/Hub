"""Regression tests for web security compatibility boundaries."""

import json
import zipfile
from unittest.mock import Mock

import pytest
from bs4 import BeautifulSoup
from pytest import fixture

from web import db
from web.model import ConnectionDatabase, TaskFile

from .conftest import create_demo_task


@pytest.mark.parametrize("kind", ["ssh", "database", "sftp", "ftp", "smb"])
def test_missing_connection_status_does_not_call_runner(
    client_fixture: fixture, monkeypatch: fixture, kind: str
) -> None:
    """Unknown connection IDs stop at the web boundary."""
    runner_get = Mock(return_value=Mock(text="unexpected runner response"))
    monkeypatch.setattr("web.web.connection.requests.get", runner_get)

    response = client_fixture.get(f"/connection/{kind}/999999/status")

    assert response.status_code == 200
    assert "Connection not found" in response.get_data(as_text=True)
    runner_get.assert_not_called()


def test_connection_status_escapes_runner_exception(
    client_fixture: fixture, monkeypatch: fixture
) -> None:
    """Runner errors cannot inject markup into status tooltips."""
    connection = ConnectionDatabase(name="Hospital Database")
    db.session.add(connection)
    db.session.commit()
    runner_get = Mock(side_effect=RuntimeError('"><script>alert(1)</script>'))
    monkeypatch.setattr("web.web.connection.requests.get", runner_get)

    response = client_fixture.get(f"/connection/database/{connection.id}/status")
    body = response.get_data(as_text=True)
    parsed = BeautifulSoup(body, features="html.parser")

    assert response.status_code == 200
    assert parsed.find("script") is None
    assert parsed.find("span")["data-tooltip"] == '"><script>alert(1)</script>'


def test_zip_download_uses_flask3_filename_api(
    client_fixture: fixture, tmp_path, monkeypatch: fixture
) -> None:
    """Archived task output downloads with its stored filename on Flask 3."""
    _, task_id = create_demo_task(db.session)
    task_file = TaskFile(
        task_id=task_id,
        job_id="run-1",
        name="patient-export.zip",
        path="backup/patient-export.zip",
    )
    db.session.add(task_file)
    db.session.commit()
    archive = tmp_path / "runner-output.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("patients.csv", "patient_id,status\n")
    runner_response = Mock(text=json.dumps({"message": str(archive)}))
    monkeypatch.setattr("web.web.task_files.requests.get", Mock(return_value=runner_response))

    response = client_fixture.get(f"/file/{task_file.id}")

    assert response.status_code == 200
    assert "patient-export.zip" in response.headers["Content-Disposition"]
    response.close()
