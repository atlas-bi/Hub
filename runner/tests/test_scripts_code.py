"""Test postgres.

run with::

   poetry run pytest runner/tests/test_scripts_code.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest runner/tests/test_scripts_code.py::test_source \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings

"""

from types import SimpleNamespace
from unittest.mock import Mock

from pytest import fixture

from runner.extensions import db
from runner.model import Task
from runner.scripts.em_code import SourceCode
from runner.scripts.em_params import ParamLoader

from .conftest import create_demo_task


def test_source(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()
    task.source_code = "test"
    db.session.commit()

    params = ParamLoader(task, None)

    source_code = SourceCode(task, None, params)

    # try to get souce code
    assert source_code.source() == "test"


def test_mssql_cleanup_removes_use_and_go_batches() -> None:
    """SQL Server source cleanup keeps statements the runner can execute."""
    task = SimpleNamespace(source_type_id=1, source_database_conn=None)
    params = Mock()
    params.insert_query_params.side_effect = lambda query: query
    source_code = SourceCode(task, None, params)
    source_code.db_type = "mssql"

    cleaned = source_code.cleanup("USE master;\nGO\nSELECT 1;")

    assert "USE master" not in cleaned
    assert "GO" not in cleaned
    assert "SELECT 1;" in cleaned
