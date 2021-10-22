"""Test runner/web.

run with::

   poetry run pytest runner/tests/test_web.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest runner/tests/test_web.py::test_resume_with_scheduler \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings


"""

from pytest import fixture

from runner.extensions import db
from runner.model import Project, Task


def test_source_code(client_fixture: fixture) -> None:
    project = Project(name="demo")
    db.session.add(project)
    db.session.commit()

    task = Task(
        name="blah", source_query_type_id=1, source_git=None, project_id=project.id
    )
    db.session.add(task)
    db.session.commit()

    page = client_fixture.get(f"/api/{task.id}/source_code")
    assert b"code" in page.data


def test_alive(client_fixture: fixture) -> None:
    page = client_fixture.get("/api")
    assert page.json == {"status": "alive"}
