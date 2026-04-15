"""Test postgres.

run with::

   poetry run pytest runner/tests/test_scripts_postgres.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest runner/tests/test_scripts_postgres.py::test_valid_connection \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings

"""

from pathlib import Path

import pytest
from pytest import fixture

from runner.extensions import db
from runner.model import Connection, ConnectionDatabase, Task
from runner.scripts.em_postgres import Postgres

from .conftest import create_demo_task


def test_connection_failure(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    # make a db connection
    conn = Connection(name="demo")
    db.session.add(conn)
    db.session.commit()

    database = ConnectionDatabase(
        name="demo pg", type_id=1, connection_string="asdf", connection_id=conn.id
    )

    db.session.add(database)
    db.session.commit()

    task = Task.query.filter_by(id=t_id).first()
    task.source_type_id = 1
    task.source_database_conn = database

    db.session.commit()

    temp_dir = Path(Path(__file__).parent.parent / "temp" / "tests" / "postgres")
    temp_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError) as e:
        pg = Postgres(task, None, str(task.source_database_conn.connection_string), 90, temp_dir)
        assert "Failed to connect to database" in e
        assert 'missing "=" after "asdf"' in e


def test_valid_connection(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    # make a db connection
    conn = Connection(name="demo")
    db.session.add(conn)
    db.session.commit()

    database = ConnectionDatabase(
        name="demo sql",
        type_id=1,
        connection_string=client_fixture.application.config["PG_SERVER_CONN"],
        connection_id=conn.id,
    )

    db.session.add(database)
    db.session.commit()

    task = Task.query.filter_by(id=t_id).first()
    task.source_type_id = 1
    task.source_database_conn = database

    db.session.commit()

    temp_dir = Path(Path(__file__).parent.parent / "temp" / "tests" / "postgres")
    temp_dir.mkdir(parents=True, exist_ok=True)

    sql_instance = Postgres(
        task, None, str(task.source_database_conn.connection_string), 90, temp_dir
    )

    # run a valid query
    data_file = sql_instance.run("SELECT * FROM pg_database ;")

    assert len(data_file) == 2

    # check with query headers
    task.source_query_include_header = 1
    db.session.commit()

    sql_instance = Postgres(
        task, None, str(task.source_database_conn.connection_string), 90, temp_dir
    )

    # run a valid query
    data_file = sql_instance.run("SELECT * FROM pg_database ;")

    assert len(data_file) == 2

    # check for error on reusing a connection
    with pytest.raises(BaseException) as e:
        data_file = sql_instance.run("SELECT * FROM pg_database ;")
        assert "The cursor's connection has been closed." in e

    # test a query with no output
    sql_instance = Postgres(
        task, None, str(task.source_database_conn.connection_string), 90, temp_dir
    )
    data_file = sql_instance.run("SELECT * FROM pg_database where 1=2;")
    assert len(data_file) == 2
