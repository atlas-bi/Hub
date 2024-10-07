"""Test web/task_edit.

run with::

   poetry run pytest tests/test_task_edit.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest tests/test_task_edit.py::test_admin_online \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings


"""

from flask import request, url_for
from pytest import fixture

from web.extensions import db

from .conftest import create_demo_task


def test_invalid_project_new_task_get(client_fixture: fixture) -> None:
    # test with invalid project
    page = client_fixture.get(
        url_for("task_edit_bp.task_new_get", project_id=99), follow_redirects=True
    )
    assert page.status_code == 200
    assert page.request.path == url_for("project_bp.new_project_form")
    assert "Project does not exist" in page.get_data(as_text=True)


def test_valid_project_new_task_get(client_fixture: fixture) -> None:
    p_id, _ = create_demo_task(db.session)
    page = client_fixture.get(
        url_for("task_edit_bp.task_new_get", project_id=p_id), follow_redirects=False
    )
    assert page.status_code == 200


def test_new_task(client_fixture: fixture) -> None:
    # get project id
    p_id, _ = create_demo_task(db.session)
    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}

    data = {
        "name": "test task",
    }

    page = client_fixture.post(
        url_for("task_edit_bp.task_new", project_id=p_id),
        data=data,
        follow_redirects=True,
        headers=headers,
    )
    # get id
    t_id = int(page.request.path.split("/")[-1])

    # check redirect
    assert page.request.path == url_for("task_bp.one_task", task_id=t_id)

    # try an enabled task
    data = {"name": "test task", "task-ooff": "1"}

    page = client_fixture.post(
        url_for("task_edit_bp.task_new", project_id=p_id),
        data=data,
        follow_redirects=True,
        headers=headers,
    )
    # get id
    t_id = int(page.request.path.split("/")[-1])

    # check redirect
    assert page.request.path == url_for("task_bp.one_task", task_id=t_id)


def test_edit_invalid_task_get(client_fixture: fixture) -> None:
    # test with invalid project
    page = client_fixture.get(
        url_for("task_edit_bp.task_edit_get", task_id=99), follow_redirects=True
    )
    assert page.status_code == 200
    assert page.request.path == url_for("project_bp.new_project")
    assert "Task does not exist" in page.get_data(as_text=True)


def test_edit_valid_task_get(client_fixture: fixture) -> None:
    # try with valid project
    _, t_id = create_demo_task(db.session)
    page = client_fixture.get(
        url_for("task_edit_bp.task_edit_get", task_id=t_id), follow_redirects=False
    )
    assert page.status_code == 200


def test_edit_task(client_fixture: fixture) -> None:
    # get project id
    _, t_id = create_demo_task(db.session)
    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}

    data = {
        "name": "test task",
    }

    page = client_fixture.post(
        url_for("task_edit_bp.task_edit_post", task_id=t_id),
        data=data,
        follow_redirects=True,
        headers=headers,
    )
    # get id
    t_id = int(page.request.path.split("/")[-1])

    # check redirect
    assert page.request.path == url_for("task_bp.one_task", task_id=t_id)

    # try an enabled task
    data = {"name": "test task", "task-ooff": "1"}

    page = client_fixture.post(
        url_for("task_edit_bp.task_edit_post", task_id=t_id),
        data=data,
        follow_redirects=True,
        headers=headers,
    )
    # get id
    t_id = int(page.request.path.split("/")[-1])

    # check redirect
    assert page.request.path == url_for("task_bp.one_task", task_id=t_id)


def test_new_task(client_fixture: fixture) -> None:
    p_id, _ = create_demo_task(db.session)

    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    response = client_fixture.post(
        "/project/" + str(p_id) + "/task/new",
        data={
            "name": "Test task",
            "enabled": 0,
        },
        headers=headers,
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_task_params(client_fixture: fixture) -> None:
    p_id, _ = create_demo_task(db.session)

    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    response = client_fixture.post(
        "/project/" + str(p_id) + "/task/new",
        data={
            "name": "Test task params",
            "enabled": 0,
            "sourceType": 1,  # database
            "sourceQueryType": 4,  # source code
            "sourceCode": "Declare @test int = 1;\nDeclare @test_two int = 2;Set @test_colon int = 1;",
            "taskParams": "@test=2\n@test_colon:2\n@test_two=parse(%Y)",
        },
        headers=headers,
        follow_redirects=True,
    )
    # check source code for params
    # task/1923/source
    # need to check the code here
    assert response.status_code == 200


def test_edit_task(client_fixture: fixture) -> None:
    _, t_id = create_demo_task(db.session)

    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    response = client_fixture.post(
        "/task/" + str(t_id) + "/edit",
        data={
            "name": "Test task",
            "enabled": 0,
        },
        headers=headers,
        follow_redirects=True,
    )

    assert response.status_code == 200
