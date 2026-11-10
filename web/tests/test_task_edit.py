"""Test web/task_edit.

run with::

   poetry run pytest tests/test_task_edit.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest tests/test_task_edit.py::test_admin_online \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings


"""

from pathlib import Path

from bs4 import BeautifulSoup
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


def test_task_and_project_forms_include_csrf_tokens(client_fixture: fixture) -> None:
    """Task/project edit forms expose CSRF tokens and reject tokenless POSTs."""
    client_fixture.application.config["WTF_CSRF_ENABLED"] = True
    p_id, t_id = create_demo_task(db.session)

    task_page = client_fixture.get(url_for("task_edit_bp.task_edit_get", task_id=t_id))
    task_soup = BeautifulSoup(task_page.data, features="lxml")
    assert task_soup.find("input", attrs={"name": "csrf_token", "value": True})
    assert (
        client_fixture.post(f"/task/{t_id}/edit", data={"name": "Missing token"}).status_code
        == 400
    )

    project_page = client_fixture.get(f"/project/{p_id}/edit")
    project_soup = BeautifulSoup(project_page.data, features="lxml")
    assert project_soup.find("input", attrs={"name": "csrf_token", "value": True})
    assert (
        client_fixture.post(f"/project/{p_id}/edit", data={"project_name": "Missing"}).status_code
        == 400
    )

    templates = Path(__file__).parents[1] / "templates" / "pages"
    for relative in ("task/new.html.j2", "project/new.html.j2", "login.html.j2"):
        assert 'name="csrf_token"' in (templates / relative).read_text()
