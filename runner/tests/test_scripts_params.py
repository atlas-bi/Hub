"""Test params.

run with::

   poetry run pytest runner/tests/test_scripts_params.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest runner/tests/test_scripts_params.py::test_date_parsing \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings

"""

from pytest import fixture

from runner.extensions import db
from runner.model import ProjectParam, Task, TaskParam
from runner.scripts.em_params import ParamLoader

from .conftest import create_demo_task


def test_date_parsing(client_fixture: fixture) -> None:
    _, t_id = create_demo_task()
    task = Task.query.filter_by(id=t_id).first()

    assert ParamLoader(task, None).project_params == {}

    task.source_query_type_id = 4
    task.source_query = "declare @stuff nvarchar(max) = 'asdf'"

    db.session.add(TaskParam(task_id=task.id, key="@stuff", value="1234"))
    db.session.commit()

    assert ParamLoader(task, None).project_params == {}
    assert ParamLoader(task, None).task_params == {"@stuff": "1234"}

    db.session.add(ProjectParam(project_id=task.project.id, key="@stuff", value="2345"))
    db.session.commit()

    assert ParamLoader(task, None).project_params == {"@stuff": "2345"}
    assert ParamLoader(task, None).task_params == {"@stuff": "1234"}
