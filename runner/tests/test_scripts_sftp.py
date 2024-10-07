"""Test sftp.

run with::

   poetry run pytest runner/tests/test_scripts_sftp.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest runner/tests/test_scripts_sftp.py::test_valid_connection \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings

"""

import sys
import tempfile
from pathlib import Path

import pytest
from pytest import fixture

from runner.extensions import db
from runner.model import Connection, ConnectionSftp, Task
from runner.scripts.em_messages import RunnerException
from runner.scripts.em_sftp import Sftp

from .conftest import create_demo_task

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from crypto import em_encrypt


def test_connection_failure(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    # make a db connection
    conn = Connection(name="demo")
    db.session.add(conn)
    db.session.commit()

    sftp = ConnectionSftp(
        name="demo sql",
        address="nowhere",
        port=99,
        username="asdf",
        password=em_encrypt("nothing", client_fixture.application.config["PASS_KEY"]),
        connection_id=conn.id,
    )

    task = Task.query.filter_by(id=t_id).first()
    task.source_sftp_conn = sftp

    db.session.commit()

    temp_dir = Path(Path(__file__).parent.parent / "temp" / "tests" / "postgres")
    temp_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(RunnerException) as e:
        sftp_server = Sftp(task, None, task.source_sftp_conn, temp_dir)
        assert "nodename nor servname provided, or not known" in e
        assert "SFTP connection failed." in e

    # test with bad key
    sftp.key = sftp.password
    db.session.commit()

    task = Task.query.filter_by(id=t_id).first()
    with pytest.raises(RunnerException) as e:
        sftp_server = Sftp(task, None, task.source_sftp_conn, temp_dir)
        assert "nodename nor servname provided, or not known" in e
        assert "SFTP connection failed." in e


# def test_valid_connection(client_fixture: fixture) -> None:
#     p_id, t_id = create_demo_task()

#     # make a db connection
#     conn = Connection(name="demo")
#     db.session.add(conn)
#     db.session.commit()

#     sftp = ConnectionSftp(
#         name="demo sql",
#         address="127.0.0.1",
#         path="/sftp/",
#         port=23,
#         username=client_fixture.application.config["SFTP_SERVER_USER"],
#         password=em_encrypt(
#             client_fixture.application.config["SFTP_SERVER_PASS"],
#             client_fixture.application.config["PASS_KEY"],
#         ),
#         connection_id=conn.id,
#     )

#     task = Task.query.filter_by(id=t_id).first()
#     task.source_sftp_conn = sftp

#     db.session.commit()

#     # save and a file
#     with tempfile.NamedTemporaryFile(mode="w+", encoding="utf8") as temp_file:
#         temp_file.write("Hello")
#         temp_file.seek(0)
#         print(temp_file.name)
#         print(str(Path(temp_file.name).parent))
#         sftp_server = Sftp(
#             task, None, task.source_sftp_conn, Path(temp_file.name).parent
#         )
#         sftp_server.save(1, temp_file.name.split("/")[-1])

#         # start a new connection
#         sftp_server = Sftp(
#             task, None, task.source_sftp_conn, Path(temp_file.name).parent
#         )
#         data_files = sftp_server.read(temp_file.name.split("/")[-1])

#         assert len(data_files) == 1
#         assert Path(data_files[0].name).read_text("utf8") == "Hello"
