"""Test SMB functionality.

Run with:

   poetry run pytest runner/tests/test_scripts_smb.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings

   poetry run pytest runner/tests/test_scripts_smb.py::test_save_file \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings

"""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
from pytest import fixture

from runner.extensions import db
from runner.model import Connection, ConnectionSmb, Task
from runner.scripts.em_messages import RunnerException
from runner.scripts.em_smb import Smb

from .conftest import create_demo_task


@fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@fixture
def smb_connection(client_fixture: fixture) -> None:
    conn = Connection(name="demo_smb")
    db.session.add(conn)
    db.session.commit()

    smb = ConnectionSmb(
        name="demo smb",
        server_name="raynor",
        share_name="int",
        username=client_fixture.application.config["SMB_USERNAME"],
        password=client_fixture.application.config["SMB_PASSWORD"],
        connection=conn,
        path="AtlasHubTest",
    )
    db.session.add(smb)
    db.session.commit()
    return smb


def test_connection_failure(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    # make a db connection
    conn = Connection(name="demo")
    db.session.add(conn)
    db.session.commit()

    smb = ConnectionSmb(
        name="demo smb",
        server_name="server",
        share_name="int",
        username="asdsad",
        password="12345",
        connection=conn,
        path="AtlasHubTest",
    )
    db.session.add(smb)
    db.session.commit()

    task = Task.query.filter_by(id=t_id).first()
    task.source_type_id = 2
    task.source_smb_conn = smb

    db.session.commit()

    temp_dir = Path(Path(__file__).parent.parent / "temp" / "tests" / "smb")
    temp_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError) as excinfo:
        s = Smb(task, None, task.source_smb_conn, temp_dir)

    assert "Failed to connect to" in str(excinfo.value)
    assert "Unexpected error during registration" in str(excinfo.value)


def test_save_file(client_fixture: fixture, temp_dir: Path, smb_connection: ConnectionSmb):
    _, task_id = create_demo_task()
    task = Task.query.get(task_id)
    task.destination_file_name = "testfile.txt"
    db.session.commit()

    # Create dummy file to upload
    test_file = temp_dir / "testfile.txt"
    test_file.write_text("dummy content")

    with mock.patch("runner.scripts.em_smb.copyfile"), mock.patch(
        "runner.scripts.em_smb.getsize", return_value=1234
    ), mock.patch("runner.scripts.em_smb.makedirs"):

        smb = Smb(task, "run1", smb_connection, temp_dir)
        path = smb.save(overwrite=1, file_name="testfile.txt")

        assert path.endswith("testfile.txt")


def test_save_missing_file(client_fixture: fixture, temp_dir: Path, smb_connection: ConnectionSmb):
    _, task_id = create_demo_task()
    task = Task.query.get(task_id)

    with mock.patch("runner.scripts.em_smb.copyfile", side_effect=FileNotFoundError("not found")):
        smb = Smb(task, "run2", smb_connection, temp_dir)

        with pytest.raises(RunnerException) as e:
            smb.save(overwrite=1, file_name="missing.txt")

        assert "Source file not found" in str(e.value)


def test_save_permission_denied(
    client_fixture: fixture, temp_dir: Path, smb_connection: ConnectionSmb
):
    _, task_id = create_demo_task()
    task = Task.query.get(task_id)
    test_file = temp_dir / "testfile.txt"
    test_file.write_text("data")

    with mock.patch("runner.scripts.em_smb.copyfile", side_effect=PermissionError("denied")):
        smb = Smb(task, "run3", smb_connection, temp_dir)

        with pytest.raises(RunnerException) as e:
            smb.save(overwrite=1, file_name="testfile.txt")

        assert "Permission denied" in str(e.value)


def test_read_file(client_fixture: fixture, temp_dir: Path, smb_connection: ConnectionSmb):
    _, task_id = create_demo_task()
    task = Task.query.get(task_id)
    test_file = temp_dir / "readfile.txt"
    test_file.write_text("downloaded")

    def fake_copyfile(src, dst, **kwargs):
        Path(dst).write_text("copied content")

    with mock.patch("runner.scripts.em_smb.copyfile", side_effect=fake_copyfile):
        smb = Smb(task, "run4", smb_connection, temp_dir)
        result = smb.read("readfile.txt")

        assert len(result) == 1
        assert Path(result[0].name).read_text() == "copied content"


def test_read_wildcard(client_fixture: fixture, temp_dir: Path, smb_connection: ConnectionSmb):
    _, task_id = create_demo_task()
    task = Task.query.get(task_id)

    with mock.patch(
        "runner.scripts.em_smb.walk", return_value=[("path", [], ["match1.txt", "match2.txt"])]
    ), mock.patch(
        "runner.scripts.em_smb.copyfile",
        side_effect=lambda src, dst, **kwargs: Path(dst).write_text("content"),
    ):

        smb = Smb(task, "run5", smb_connection, temp_dir)
        results = smb.read("match*.txt")

        assert len(results) == 2
        assert all("content" in Path(f.name).read_text() for f in results)
