"""Test web/project.

run with::

   poetry run pytest web/tests/test_projects.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest web/tests/test_projects.py::test_projects_user \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings


"""

import time
from datetime import datetime

from flask import request, url_for
from pytest import fixture

from web.extensions import db
from web.model import Project, Task, TaskFile, TaskLog, User

from .conftest import create_demo_task


def test_projects_home(client_fixture: fixture) -> None:
    # having no projects should redirect to new project page
    page = client_fixture.get(url_for("project_bp.all_projects"))
    assert page.status_code in [302, 200]  # depending on orderof tests

    page = client_fixture.get(url_for("project_bp.all_projects"), follow_redirects=True)
    assert page.status_code == 200
    assert page.request.path in [
        url_for("project_bp.new_project"),
        url_for("project_bp.all_projects"),
    ]

    # if we have a project, we should go to the project list page
    p_id, t_id = create_demo_task(db.session)
    page = client_fixture.get(url_for("project_bp.all_projects"), follow_redirects=False)
    assert page.status_code == 200
    assert page.request.path == url_for("project_bp.all_projects")
    assert "Projects" in page.get_data(as_text=True)

    # cleanup
    db.session.delete(Task.query.get(t_id))
    db.session.delete(Project.query.get(p_id))

    db.session.commit()


def test_projects_user(client_fixture: fixture) -> None:
    # get my user
    my_user = User.query.filter_by(id=1).first()

    # having no projects should redirect to new project page
    page = client_fixture.get("/project/user")
    assert page.status_code in [302, 200]  # depending on order of tests

    page = client_fixture.get("/project/user/1")
    assert page.status_code in [302, 200]  # depending on order of tests

    page = client_fixture.get("/project/user", follow_redirects=True)
    assert page.status_code == 200
    assert page.request.path in [
        url_for("project_bp.new_project_form"),
        url_for("project_bp.user_projects"),
    ]

    page = client_fixture.get("/project/user/1", follow_redirects=True)
    assert page.status_code == 200
    assert page.request.path in [url_for("project_bp.new_project"), "/project/user/1"]

    # if we have a project, we should go to the project list page
    create_demo_task(db.session)
    page = client_fixture.get("/project/user", follow_redirects=False)
    assert page.status_code == 200
    assert page.request.path == url_for("project_bp.user_projects")
    assert "Projects" in page.get_data(as_text=True)
    assert my_user.full_name in page.get_data(as_text=True)

    page = client_fixture.get("/project/user/1", follow_redirects=False)
    assert page.status_code == 200
    assert page.request.path == url_for("project_bp.user_projects", user_id=1)
    assert "Projects" in page.get_data(as_text=True)
    assert my_user.full_name in page.get_data(as_text=True)

    # check invalid user
    page = client_fixture.get("/project/user/100", follow_redirects=True)
    assert page.status_code == 200
    assert b"That user doesn't exist." in page.data


def test_one_project(client_fixture: fixture) -> None:
    # get invalid project
    # should redirect to project page and flash error
    page = client_fixture.get(url_for("project_bp.one_project", project_id=99))
    assert page.status_code == 302
    page = client_fixture.get(
        url_for("project_bp.one_project", project_id=99), follow_redirects=True
    )
    # no projects exist so go to new project page
    assert page.status_code == 200
    assert page.request.path == url_for("project_bp.new_project")

    assert "The project does not exist" in page.get_data(as_text=True)

    # try with valid project and task
    p_id, _ = create_demo_task(db.session)
    page = client_fixture.get(url_for("project_bp.one_project", project_id=p_id))

    assert page.request.path == url_for("project_bp.one_project", project_id=p_id)


def test_edit_project_form(client_fixture: fixture) -> None:
    # test with invalid project
    page = client_fixture.get(url_for("project_bp.edit_project_form", project_id=99))
    assert page.status_code == 302
    page = client_fixture.get(
        url_for("project_bp.edit_project_form", project_id=99), follow_redirects=True
    )
    assert page.status_code == 200
    # should be directed to new project if none exist
    assert page.request.path == url_for("project_bp.new_project")
    assert "The project does not exist" in page.get_data(as_text=True)

    # try with valid project and task
    p_id, _ = create_demo_task(db.session)
    page = client_fixture.get(url_for("project_bp.edit_project_form", project_id=p_id))
    assert page.request.path == url_for("project_bp.edit_project_form", project_id=p_id)
    assert "Editing" in page.get_data(as_text=True)


def test_projects_new(client_fixture: fixture) -> None:
    assert client_fixture.get("/project/new").status_code == 200


# add a project
def test_create_cron_project(client_fixture: fixture) -> None:
    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    date_now = datetime.now()

    data = {
        "project_name": "test cron project",
        "project_desc": "my cron project description",
        "project_cron": "1",
        "project_cron_year": "1970",
        "project_cron_mnth": "1",
        "project_cron_week": "1",
        "project_cron_day": "1",
        "project_cron_wday": "1",
        "project_cron_hour": "1",
        "project_cron_min": "1",
        "project_cron_sec": "1",
        "project_cron_sdate": datetime.strftime(date_now, "%Y-%m-%d %H:%M"),
        "project_cron_edate": datetime.strftime(date_now, "%Y-%m-%d %H:%M"),
        "project_globalParams": "@this-is-cool",
    }

    page = client_fixture.post(
        url_for("project_bp.new_project"),
        data=data,
        follow_redirects=True,
        headers=headers,
    )

    # get id
    p_id = int(page.request.path.split("/")[-1])

    # check redirect
    assert page.request.path == url_for("project_bp.one_project", project_id=p_id)

    # check project
    project = Project.query.get(p_id)

    assert project.name == data["project_name"]
    assert project.description == data["project_desc"]
    assert project.cron == int(data["project_cron"])

    # verify intv and oneoff are disabled.
    assert project.intv == 0
    assert project.ooff == 0


def test_edit_project(client_fixture: fixture) -> None:
    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    p_id, t_id = create_demo_task(db.session)

    # enable task to test reschedule
    Task.query.filter_by(id=t_id).update({"enabled": 1})
    db.session.commit()

    date_now = datetime.now()
    data = {
        "project_name": "test cron project",
        "project_desc": "my cron project description",
        "project_cron": "1",
        "project_cron_year": "2024",
        "project_cron_mnth": "1",
        "project_cron_week": "1",
        "project_cron_day": "1",
        "project_cron_wday": "1",
        "project_cron_hour": "1",
        "project_cron_min": "1",
        "project_cron_sec": "1",
        "project_cron_sdate": datetime.strftime(date_now, "%Y-%m-%d %H:%M"),
        "project_cron_edate": datetime.strftime(date_now, "%Y-%m-%d %H:%M"),
        "project_globalParams": "@this-is-cool",
    }
    page = client_fixture.post(
        url_for("project_bp.edit_project", project_id=p_id),
        data=data,
        follow_redirects=True,
        headers=headers,
    )
    # check project
    project = Project.query.get(p_id)

    assert project.name == data["project_name"]
    assert project.description == data["project_desc"]
    assert project.cron == int(data["project_cron"])

    # verify intv and oneoff are disabled.
    assert project.intv == 0
    assert project.ooff == 0

    assert page.request.path == url_for("project_bp.one_project", project_id=p_id)

    # check that task was rescheduled
    # assert (
    #     TaskLog.query.filter_by(task_id=t_id, error=1, status_id=7)
    #     .filter(TaskLog.message.like("%Failed to schedule task%"))  # type: ignore[union-attr]
    #     .first()
    #     is not None
    # )


def test_delete_project(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task(db.session)

    # delete project
    page = client_fixture.get(
        url_for("project_bp.delete_project", project_id=p_id), follow_redirects=True
    )

    # should redirect
    assert page.request.path == url_for("project_bp.new_project")

    # should be no files, logs, tasks
    assert TaskLog.query.filter_by(task_id=t_id).first() is None
    assert Task.query.filter_by(id=t_id).first() is None
    assert TaskFile.query.filter_by(task_id=t_id).first() is None
    assert Project.query.filter_by(id=p_id).first() is None


def test_enable_disable_project(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task(db.session)

    page = client_fixture.get(
        url_for("project_bp.enable_all_project_tasks", project_id=p_id),
        follow_redirects=True,
    )
    assert page.status_code == 200
    # check redirect
    assert page.request.path == url_for("project_bp.one_project", project_id=p_id)

    # will still show disabled, scheduler is offline
    # sleep to let executor run
    time.sleep(1)
    assert Task.query.filter_by(id=t_id).first().enabled == 0

    # manual enable
    Task.query.filter_by(id=t_id).update({"enabled": 1})
    db.session.commit()
    assert Task.query.filter_by(id=t_id).first().enabled == 1

    page = client_fixture.get(
        url_for("project_bp.disable_all_project_tasks", project_id=p_id),
        follow_redirects=True,
    )
    assert page.status_code == 200
    # check logs for scheduler offline error

    # check that task was rescheduled
    # assert TaskLog.query.filter_by(task_id=t_id, error=1, status_id=7).filter(TaskLog.message.like("%Failed to schedule task.%")).first() is not None  # type: ignore[union-attr]

    # check that task is disabled.. will fail with scheduler offline
    assert Task.query.filter_by(id=t_id).first().enabled == 1
    # check redirect
    assert page.request.path == url_for("project_bp.one_project", project_id=p_id)


def test_run_all(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task(db.session)

    # manual enable
    Task.query.filter_by(id=t_id).update({"enabled": 1})
    db.session.commit()
    assert Task.query.filter_by(id=t_id).first().enabled == 1

    # attempt to run
    page = client_fixture.get(
        url_for("project_bp.run_all_project_tasks", project_id=p_id),
        follow_redirects=True,
    )
    assert page.status_code == 200
    assert page.request.path == url_for("project_bp.one_project", project_id=p_id)

    # scheduler is offline
    # check that task was rescheduled
    # wait a second to executor to run.
    time.sleep(1)

    assert TaskLog.query.filter_by(task_id=t_id, error=1, status_id=7).filter(TaskLog.message.like("%Failed to send task to runner.%")).first() is not None  # type: ignore[union-attr]
