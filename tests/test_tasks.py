# flake8: noqa,
# pylint: skip-file
from datetime import datetime

import pytest
from flask import g

from em_web.model import Project, Task


def test_tasks_home(em_web_authed):
    assert em_web_authed.get("/task").status_code == 200


def test_tasks_mine(em_web_authed):
    assert em_web_authed.get("/task/mine", follow_redirects=True).status_code == 200


def tast_tasks_user(em_web_authed):
    assert em_web_authed.get("/task/user/1").status_code == 200


# add a task
def test_create_task(em_web_authed):
    project = Project(
        name="test project",
        description="my project description",
    )

    db = g.get("db")
    db.session.rollback()
    db.session.add(project)
    db.session.commit()

    g.task_project_id = project.id

    task = Task(
        name="test task",
        project_id=project.id,
        status_id=1,
        enabled=1,
    )

    db.session.add(task)
    db.session.commit()

    g.task_task_id = task.id

    # disable the task
    assert (
        em_web_authed.get(
            "/task/" + str(task.id) + "/disable", follow_redirects=True
        ).status_code
        == 200
    )

    # enable the task
    assert (
        em_web_authed.get(
            "/task/" + str(task.id) + "/enable", follow_redirects=True
        ).status_code
        == 200
    )

    # reschedule the task
    assert (
        em_web_authed.get(
            "/task/" + str(task.id) + "/schedule", follow_redirects=True
        ).status_code
        == 200
    )

    # run the task
    assert (
        em_web_authed.get(
            "/task/" + str(task.id) + "/run", follow_redirects=True
        ).status_code
        == 200
    )

    # attempt to enable from project level
    assert (
        em_web_authed.get(
            "/project/" + str(project.id) + "/enable", follow_redirects=True
        ).status_code
        == 200
    )
    # attempt to disable from project level
    assert (
        em_web_authed.get(
            "/project/" + str(project.id) + "/disable", follow_redirects=True
        ).status_code
        == 200
    )

    # attempt to run from the project level
    assert (
        em_web_authed.get(
            "/project/" + str(project.id) + "/run", follow_redirects=True
        ).status_code
        == 200
    )

    # delete the task
    assert (
        em_web_authed.get(
            "/task/" + str(task.id) + "/delete", follow_redirects=True
        ).status_code
        == 200
    )
    assert Task.query.filter(id == g.get("task_task_id")).count() < 1

    # delete the project
    assert (
        em_web_authed.get(
            "/project/" + str(project.id) + "/delete", follow_redirects=True
        ).status_code
        == 200
    )
    assert Project.query.filter(id == g.get("task_project_id")).count() < 1
