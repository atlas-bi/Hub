# flake8: noqa,
# pylint: skip-file
import datetime
import os

import pytest
from flask import g, url_for

from em_runner import create_app as em_runner_create_app
from em_scheduler import app as em_scheduler_app
from em_web import create_app as em_web_create_app


@pytest.fixture
def em_web_app():
    app = em_web_create_app()
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
@pytest.mark.options(env="test")
def em_web_authed(em_web_app):
    assert em_web_app.get("/login").status_code == 200

    import os

    # if not em_web_app.application.config["TEST"]:
    em_web_app.post(
        url_for("auth_bp.login"),
        data=dict(
            user="mr-cool",
            password="",
        ),
        follow_redirects=True,
    )

    from em_web.extensions import db

    g.db = db

    with em_scheduler_app.test_client() as scheduler_client:
        em_runner_create_app()
        yield em_web_app

    from em_web.model import Project, Task, TaskLog

    # remove leftovers
    db = g.get("db")

    # remove test project
    if g.get("project_project_id"):
        db.session.rollback()
        Project.query.filter(id == g.get("project_project_id")).delete()
        db.session.commit()

    # remove test task
    if g.get("task_task_id"):
        db.session.rollback()

        TaskLog.query.filter_by(task_id=g.get("task_task_id")).delete()
        db.session.commit()

        Task.query.filter(id == g.get("task_task_id")).delete()
        db.session.commit()
    # remove test task project
    if g.get("task_project_id"):
        db.session.rollback()
        Project.query.filter(id == g.get("task_project_id")).delete()
        db.session.commit()


@pytest.fixture
def runner():
    with em_runner_create_app() as runner:
        print("runner started")
        yield runner


@pytest.fixture
def scheduler_client():
    import os

    from em_scheduler import app
    from em_scheduler.extensions import db
    from em_scheduler.model import Project, Task, TaskLog

    with app.test_client() as client:
        with app.app_context():
            print("scheduler started")
            test_project = Project(
                name="scheduler_test_project",
                intv=1,
                intv_type="w",
                intv_value=1,
                cron=1,
                cron_sec=59,
                ooff=1,
                ooff_date=datetime.datetime.now(),
            )
            db.session.add(test_project)
            db.session.commit()
            test_task = Task(
                project_id=test_project.id,
                name="scheduler_test_task",
                source_type_id=1,
                source_database_id=1,
                source_query_type_id=4,
                source_code="select getdate()",
            )
            db.session.add(test_task)
            db.session.commit()

            g.task_id = test_task.id
            g.project_id = test_project.id

            db.session.rollback()

            yield client

            db.session.rollback()
            db.session.commit()

            # # logs are still getting adding during teardown.
            # while TaskLog.query.filter_by(task_id=g.task_id).count() > 0:
            #     TaskLog.query.filter_by(task_id=g.task_id).delete()
            #     db.session.commit()

            # Task.query.filter_by(id=g.task_id).delete()
            # db.session.commit()

            # Project.query.filter_by(id=g.project_id).delete()
            # db.session.commit()
