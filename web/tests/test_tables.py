"""Test web/table.

run with::

   poetry run pytest tests/test_tables.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest tests/test_tables.py::test_admin_online \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings


"""

import json

from pytest import fixture

from web import db
from web.model import Task

from .conftest import create_demo_task


def test_table_project_mine(client_fixture: fixture) -> None:
    page = client_fixture.get("/table/project/mine")
    assert page.status_code == 200
    # check json is usable
    assert len(json.loads(page.get_data(as_text=True)))

    # create a project
    _, t_id = create_demo_task(db.session)
    page = client_fixture.get("/table/project/1")
    assert page.status_code == 200
    # check json is usable
    assert len(json.loads(page.get_data(as_text=True)))

    # change task status
    Task.query.filter_by(id=t_id).status_id = 1
    db.session.commit()

    page = client_fixture.get("/table/project/all")
    assert page.status_code == 200
    # check json is usable
    assert len(json.loads(page.get_data(as_text=True)))

    # change task status
    Task.query.filter_by(id=t_id).status_id = 2
    db.session.commit()

    page = client_fixture.get("/table/project/all")
    assert page.status_code == 200
    # check json is usable
    assert len(json.loads(page.get_data(as_text=True)))

    # change task status
    Task.query.filter_by(id=t_id).enabled = 1
    db.session.commit()

    page = client_fixture.get("/table/project/all")
    assert page.status_code == 200
    # check json is usable
    assert len(json.loads(page.get_data(as_text=True)))


def test_table_project_all(client_fixture: fixture) -> None:
    assert client_fixture.get("/table/project/all").status_code == 200


def test_table_tasklog_userevents(client_fixture: fixture) -> None:
    assert client_fixture.get("/table/tasklog/userevents").status_code == 200


def test_table_user_auth(client_fixture: fixture) -> None:
    assert client_fixture.get("/table/user/auth").status_code == 200


def test_table_connection_tasks(client_fixture: fixture) -> None:
    assert client_fixture.get("/table/connection/1/tasks").status_code == 200


def test_table_job_orphans(client_fixture: fixture) -> None:
    assert client_fixture.get("/table/jobs/orphans").status_code == 200


def test_table_tasks_active(client_fixture: fixture) -> None:
    assert client_fixture.get("/table/tasks/active").status_code == 200


def test_table_tasks_errored(client_fixture: fixture) -> None:
    assert client_fixture.get("/table/tasks/errored").status_code == 200


def test_table_tasks_scheduled(client_fixture: fixture) -> None:
    assert client_fixture.get("/table/tasks/scheduled").status_code == 200


def test_table_my_tasks_list(client_fixture: fixture) -> None:
    assert client_fixture.get("/table/tasks/mine/list").status_code == 200


def test_table_all_tasks_list(client_fixture: fixture) -> None:
    assert client_fixture.get("/table/tasks/all/list").status_code == 200


def test_table_project_tasks(client_fixture: fixture) -> None:
    assert client_fixture.get("/table/project/1/task").status_code == 200


def test_table_project_tasklog(client_fixture: fixture) -> None:
    assert client_fixture.get("/table/project/1/tasklog").status_code == 200


def test_table_task_log(client_fixture: fixture) -> None:
    assert client_fixture.get("/table/task/1/log").status_code == 200


def test_table_all_tasks_log(client_fixture: fixture) -> None:
    assert client_fixture.get("/table/tasks/log").status_code == 200


def test_table_tasks_error_log(client_fixture: fixture) -> None:
    assert client_fixture.get("/table/tasks/errorLog").status_code == 200


def test_table_tasks_files(client_fixture: fixture) -> None:
    from web.model import Task

    task = Task.query.first()
    if task:
        assert client_fixture.get("/table/task/" + str(task.id) + "/files").status_code == 200
