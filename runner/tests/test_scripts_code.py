"""Test postgres.

run with::

   poetry run pytest runner/tests/test_scripts_code.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest runner/tests/test_scripts_code.py::test_source \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings

"""

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
