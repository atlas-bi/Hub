"""Test web/tasks.

run with::

   poetry run pytest web/tests/test_tasks.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest web/tests/test_tasks.py::test_tasks_user \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings


"""

from flask import request, url_for
from pytest import fixture

from web.extensions import db
from web.model import Project, Task, TaskLog

from .conftest import create_demo_task


def test_tasks_home(client_fixture: fixture) -> None:
    # check with no tasks
    page = client_fixture.get("/task", follow_redirects=True)
    assert page.status_code == 200
    # no projects exists so go to new project
    assert page.request.path in [
        url_for("project_bp.new_project"),
        url_for("task_bp.all_tasks"),
    ]

    # add a task
    create_demo_task(db.session)
    page = client_fixture.get("/task", follow_redirects=False)
    assert page.status_code == 200


def test_my_tasks(client_fixture: fixture) -> None:
    # remove everyting
    db.session.query(TaskLog).delete(synchronize_session=False)
    db.session.commit()
    db.session.query(Task).delete(synchronize_session=False)
    db.session.commit()
    db.session.query(Project).delete(synchronize_session=False)
    db.session.commit()
    # check with no tasks
    page = client_fixture.get("/task/mine", follow_redirects=True)
    assert page.status_code == 200
    # no projects exists so go to new project
    assert page.request.path == url_for("project_bp.new_project")

    # add a task
    create_demo_task(db.session)
    page = client_fixture.get("/task/mine", follow_redirects=False)
    assert page.status_code == 200


def test_tasks_user(client_fixture: fixture) -> None:
    # remove everyting
    db.session.query(Task).delete(synchronize_session=False)
    db.session.commit()
    db.session.query(Project).delete(synchronize_session=False)
    db.session.commit()
    # check with no tasks
    page = client_fixture.get("/task/user/1", follow_redirects=True)
    assert page.status_code == 200
    # no projects exists so go to new project
    assert page.request.path == url_for("project_bp.new_project")

    # add a task
    create_demo_task(db.session)
    page = client_fixture.get("/task/user/1", follow_redirects=False)
    assert page.status_code == 200

    # bad user
    page = client_fixture.get("/task/user/100", follow_redirects=True)
    assert page.status_code == 200
    assert b"That user does not exist." in page.data


def test_one_task(client_fixture: fixture) -> None:
    # check invalid task
    page = client_fixture.get("/task/99", follow_redirects=True)
    assert page.status_code == 200
    # no projects exists so go to new project
    assert page.request.path == url_for("project_bp.new_project")
    assert "Task does not exist." in page.get_data(as_text=True)

    # check valid task
    _, t_id = create_demo_task(db.session)

    page = client_fixture.get(url_for("task_bp.one_task", task_id=t_id), follow_redirects=False)
    assert page.status_code == 200


def test_urls(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/sftp-dest")
    assert response.status_code == 200

    response = client_fixture.get("/task/gpg-file")
    assert response.status_code == 200

    response = client_fixture.get("/task/sftp-source")
    assert response.status_code == 200

    response = client_fixture.get("/task/ssh-source")
    assert response.status_code == 200

    response = client_fixture.get("/task/sftp-query")
    assert response.status_code == 200

    response = client_fixture.get("/task/sftp-processing")
    assert response.status_code == 200

    response = client_fixture.get("/task/ftp-dest")
    assert response.status_code == 200

    response = client_fixture.get("/task/ftp-source")
    assert response.status_code == 200

    response = client_fixture.get("/task/ftp-processing")
    assert response.status_code == 200

    response = client_fixture.get("/task/ftp-query")
    assert response.status_code == 200

    response = client_fixture.get("/task/smb-source")
    assert response.status_code == 200

    response = client_fixture.get("/task/smb-dest")
    assert response.status_code == 200

    response = client_fixture.get("/task/smb-query")
    assert response.status_code == 200

    response = client_fixture.get("/task/smb-processing")
    assert response.status_code == 200

    response = client_fixture.get("/task/database-source")
    assert response.status_code == 200
