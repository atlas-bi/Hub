"""Test web/tasks.

run with::

   poetry run pytest tests/test_tasks.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest tests/test_tasks.py::test_admin_online \
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
    assert request.path == url_for("project_bp.new_project")

    # add a task
    create_demo_task()
    page = client_fixture.get("/task", follow_redirects=False)
    assert page.status_code == 200


def test_my_tasks(client_fixture: fixture) -> None:
    # remove everyting
    db.session.query(Task).delete(synchronize_session=False)
    db.session.commit()
    db.session.query(Project).delete(synchronize_session=False)
    db.session.commit()
    # check with no tasks
    page = client_fixture.get("/task/mine", follow_redirects=True)
    assert page.status_code == 200
    # no projects exists so go to new project
    assert request.path == url_for("project_bp.new_project")

    # add a task
    create_demo_task()
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
    assert request.path == url_for("project_bp.new_project")

    # add a task
    create_demo_task()
    page = client_fixture.get("/task/user/1", follow_redirects=False)
    assert page.status_code == 200


def test_one_task(client_fixture: fixture) -> None:
    # check invalid task
    page = client_fixture.get("/task/99", follow_redirects=True)
    assert page.status_code == 200
    # no projects exists so go to new project
    assert request.path == url_for("task_bp.all_tasks")
    assert "Task does not exist." in page.get_data(as_text=True)

    # check valid task
    _, t_id = create_demo_task()

    page = client_fixture.get(
        url_for("task_bp.one_task", task_id=t_id), follow_redirects=False
    )
    assert page.status_code == 200


def test_get_source_code(client_fixture_with_runner: fixture) -> None:
    # check invalid task
    page = client_fixture_with_runner.get("/task/99/source_code")
    assert page.status_code == 200

    # there should be a log
    assert (
        TaskLog.query.filter_by(status_id=7, error=1, task_id=99)
        .filter(TaskLog.message.like("%Failed to get source code%"))  # type: ignore[union-attr]
        .first()
        is not None
    )

    # check valid task
    _, t_id = create_demo_task()

    # change source type to code
    Task.query.filter_by(id=t_id).update(
        {"source_type_id": 4, "source_code": "something cool"}
    )
    db.session.commit()
    page = client_fixture_with_runner.get(
        url_for("task_bp.task_get_source_code", task_id=t_id), follow_redirects=False
    )

    assert page.status_code == 200
    assert "something cool" in page.get_data(as_text=True)


def test_get_processing_code(client_fixture_with_runner: fixture) -> None:
    # check invalid task
    page = client_fixture_with_runner.get("/task/99/processing_code")
    assert page.status_code == 200

    # there should be a log
    assert (
        TaskLog.query.filter_by(status_id=7, error=1, task_id=99)
        .filter(TaskLog.message.like("%Failed to get processing code%"))  # type: ignore[union-attr]
        .first()
        is not None
    )

    # check valid task
    _, t_id = create_demo_task()

    # change source type to code
    Task.query.filter_by(id=t_id).update(
        {"processing_type_id": 6, "processing_code": "something cool"}
    )
    db.session.commit()
    page = client_fixture_with_runner.get(
        url_for("task_bp.task_get_processing_code", task_id=t_id),
        follow_redirects=False,
    )

    assert page.status_code == 200
    assert "something cool" in page.get_data(as_text=True)


def test_sftp_dest(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/sftp-dest")
    assert response.status_code == 200


def test_gpg_file(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/gpg-file")
    assert response.status_code == 200


def test_sftp_source(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/sftp-source")
    assert response.status_code == 200


def test_ssh_source(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/ssh-source")
    assert response.status_code == 200


def test_sftp_query(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/sftp-query")
    assert response.status_code == 200


def test_sftp_processing(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/sftp-processing")
    assert response.status_code == 200


def test_ftp_dest(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/ftp-dest")
    assert response.status_code == 200


def test_ftp_source(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/ftp-source")
    assert response.status_code == 200


def test_ftp_processing(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/ftp-processing")
    assert response.status_code == 200


def test_ftp_query(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/ftp-query")
    assert response.status_code == 200


def test_smb_source(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/smb-source")
    assert response.status_code == 200


def test_smb_dest(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/smb-dest")
    assert response.status_code == 200


def test_smb_query(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/smb-query")
    assert response.status_code == 200


def test_smb_processing(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/smb-processing")
    assert response.status_code == 200


def test_database_source(client_fixture: fixture) -> None:
    response = client_fixture.get("/task/database-source")
    assert response.status_code == 200
