# flake8: noqa,
# pylint: skip-file
from datetime import datetime

import pytest
from flask import g

from em_web.model import Project


def test_projects_home(em_web_app):
    # ensure we are sent to login page
    pg = em_web_app.get("/project")
    assert pg.status_code == 302


def test_projects_home(em_web_authed):
    assert em_web_authed.get("/project").status_code == 200


def test_projects_mine(em_web_authed):
    assert em_web_authed.get("/project/user", follow_redirects=True).status_code == 200


def test_projects_User(em_web_authed):
    assert (
        em_web_authed.get("/project/user/1", follow_redirects=True).status_code == 200
    )


def test_projects_new(em_web_authed):
    assert em_web_authed.get("/project/new").status_code == 200


# add a project
def test_create_project(em_web_authed):
    project = Project(
        name="test project",
        description="my project description",
        cron=1,
        cron_year=1,
        cron_month=1,
        cron_week=1,
        cron_day=1,
        cron_week_day=1,
        cron_hour=1,
        cron_min=1,
        cron_sec=1,
        cron_start_date=datetime.now(),
        cron_end_date=datetime.now(),
        intv=1,
        intv_type="w",
        intv_value=1,
        intv_start_date=datetime.now(),
        intv_end_date=datetime.now(),
        ooff=1,
        ooff_date=datetime.now(),
        global_params="@this-is-cool",
    )

    db = g.get("db")
    db.session.add(project)
    db.session.commit()

    project_id = project.id
    g.project_project_id = project.id

    # test add task button
    assert (
        em_web_authed.get(
            "/project/" + str(project.id) + "/task/new", follow_redirects=True
        ).status_code
        == 200
    )

    # delete the project
    assert (
        em_web_authed.get(
            "/project/" + str(project.id) + "/delete", follow_redirects=True
        ).status_code
        == 200
    )

    assert Project.query.filter(id == project_id).count() < 1
