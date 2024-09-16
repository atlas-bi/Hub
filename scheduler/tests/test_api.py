"""Test web/admin.

run with::

   poetry run pytest tests/test_api.py \
   --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings

   poetry run pytest tests/test_api.py::test_add_task -v \
   --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings

"""

# flake8: noqa,
# pylint: skip-file
# check all admin links

import sys
import time
from datetime import datetime, timedelta, timezone

import pytest
import werkzeug
from dateutil.tz import tzlocal
from flask import g, helpers
from pytest import fixture

from scheduler.extensions import atlas_scheduler, db
from scheduler.model import Project, Task, User

from . import get_or_create
from .conftest import create_demo_task, demo_task


def test_alive(client_fixture: fixture) -> None:
    page = client_fixture.get("/api")
    assert page.json == {"status": "alive"}
    assert page.status_code == 200


def test_schedule(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task(db.session)

    page = client_fixture.get(f"/api/add/{t_id}")
    assert page.json == {"message": "Scheduler: task job added!"}
    assert page.status_code == 200

    # check that status is now enabled
    t = Task.query.get(t_id)
    assert t.enabled == 1

    p_id, t_id = create_demo_task(db.session, 2021)

    page = client_fixture.get(f"/api/add/{t_id}")
    assert page.json == {"message": "Scheduler: task job added!"}
    assert page.status_code == 200

    # check that status is now enabled
    t = Task.query.get(t_id)
    assert t.enabled == 1

    # add a maintenance task
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="interval",
        hours=1,
        id="job_sync",
        name="job_sync",
        replace_existing=True,
    )

    page = client_fixture.get(f"/api/schedule")
    assert {"case": "now", "count": 0} in page.json
    assert page.status_code == 200


def test_add_task(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task(db.session)

    page = client_fixture.get(f"/api/add/{t_id}")
    assert page.json == {"message": "Scheduler: task job added!"}
    assert page.status_code == 200

    # check that status is now enabled
    t = Task.query.get(t_id)
    assert t.enabled == 1

    # check that job is in the scheduler
    scheduled_task = atlas_scheduler.get_job(f"{p_id}-{t.id}-cron")
    assert scheduled_task.args[0] == str(t.id)

    # depending on timezone results will vary (redis has no tz.)
    assert (
        scheduled_task.next_run_time.isoformat()
        == datetime(2025, 1, 1, 0, 1).replace(tzinfo=tzlocal()).isoformat()
    )

    assert "cron[minute='1']" in str(scheduled_task.trigger)

    # check next run time

    # print(t.next_run.isoformat())
    # assert (
    #     t.next_run.isoformat()
    #     == scheduled_task.next_run_time.replace(tzinfo=timezone.utc).isoformat()
    # )

    # timezone needs improvement.

    # add a non-existing job
    page = client_fixture.get(f"/api/add/-1")
    assert page.json == {"error": "Invalid job."}
    assert page.status_code == 200

    # add a non-existing job
    page = client_fixture.get(f"/api/add/asdf")
    assert page.json == {"error": "Invalid job."}
    assert page.status_code == 200

    # enable and try to add
    Task.query.get(t_id).enabled = 1
    db.session.commit()

    t = Task.query.get(t_id)
    assert t.enabled == 1

    page = client_fixture.get(f"/api/add/{t_id}")
    assert page.json == {"message": "Scheduler: task job added!"}
    assert page.status_code == 200

    # add a cron
    p = get_or_create(
        db.session,
        Project,
        name="Project 1",
        cron=1,
        cron_min="1",
        cron_start_date=datetime(2000, 1, 1, tzinfo=tzlocal()),
        intv=0,
        ooff=0,
    )
    # create a task
    t = get_or_create(
        db.session,
        Task,
        name="Task 1",
        source_type_id=6,
        source_code="""select getdate()""",
        project_id=p.id,
        source_query_type_id=4,
        enabled=0,
    )
    page = client_fixture.get(f"/api/add/{t.id}")
    assert page.json == {"message": "Scheduler: task job added!"}
    assert page.status_code == 200

    # add a intv
    p = get_or_create(
        db.session,
        Project,
        name="Project 1",
        intv=1,
        intv_type="w",
        intv_start_date=datetime(2000, 1, 1, tzinfo=tzlocal()),
        cron=0,
        ooff=0,
    )
    # create a task
    t = get_or_create(
        db.session,
        Task,
        name="Task 1",
        source_type_id=6,
        source_code="""select getdate()""",
        project_id=p.id,
        source_query_type_id=4,
        enabled=0,
    )
    page = client_fixture.get(f"/api/add/{t.id}")
    assert page.json == {"message": "Scheduler: task job added!"}
    assert page.status_code == 200

    # add a ooff
    p = get_or_create(
        db.session,
        Project,
        name="Project 1",
        ooff=1,
        ooff_date=datetime(9999, 1, 1, tzinfo=tzlocal()),
        cron=0,
        intv=0,
    )
    # create a task
    t = get_or_create(
        db.session,
        Task,
        name="Task 1",
        source_type_id=6,
        source_code="""select getdate()""",
        project_id=p.id,
        source_query_type_id=4,
        enabled=0,
    )
    page = client_fixture.get(f"/api/add/{t.id}")
    assert page.json == {"message": "Scheduler: task job added!"}
    assert page.status_code == 200


def test_delete_task(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task(db.session)
    page = client_fixture.get(f"/api/add/{t_id}")
    assert page.json == {"message": "Scheduler: task job added!"}
    assert page.status_code == 200

    page = client_fixture.get(f"/api/delete/{t_id}")
    assert page.json == {"message": "Scheduler: task job deleted!"}
    assert page.status_code == 200

    # delete a non-existing job.. all deletions are successful
    page = client_fixture.get(f"/api/delete/-1")
    assert page.json == {"error": "Invalid job."}
    assert page.status_code == 200

    # delete a non-existing job.. all deletions are successful
    page = client_fixture.get(f"/api/delete/asdf")
    assert page.json == {"error": "Invalid job."}
    assert page.status_code == 200


def test_run_task(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task(db.session)
    page = client_fixture.get(f"/api/run/{t_id}")
    assert page.json == {"message": "Scheduler: task job added!"}
    assert page.status_code == 200


def test_run_task_with_delay(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task(db.session)
    delay = 5
    page = client_fixture.get(f"/api/run/{t_id}/delay/{delay}")
    assert page.json == {"message": "Scheduler: task scheduled!"}
    assert page.status_code == 200

    # check that job is in scheduler
    scheduled_task = [
        x for x in atlas_scheduler.get_jobs() if len(x.args) > 0 and x.args[0] == str(t_id)
    ][0]
    assert (
        scheduled_task.next_run_time.replace(microsecond=0, second=0).isoformat()
        == (datetime.now() + timedelta(minutes=delay))
        .replace(microsecond=0, second=0, tzinfo=tzlocal())
        .isoformat()
    )


def test_delete_all(client_fixture: fixture) -> None:
    page = client_fixture.get(f"/api/delete")
    assert page.json == {"message": "Scheduler: all jobs deleted!"}
    assert page.status_code == 200

    # one maintenance job should be left
    assert len(atlas_scheduler.get_jobs()) == 0

    # add a job with no args
    from .conftest import demo_task

    atlas_scheduler.add_job(
        func=demo_task,
        trigger="interval",
        seconds=10,
        id="test job 2",
        name="test job 2",
        replace_existing=True,
    )

    # add a job and try again
    p_id, t_id = create_demo_task(db.session)
    page = client_fixture.get(f"/api/add/{t_id}")
    assert page.json == {"message": "Scheduler: task job added!"}
    assert page.status_code == 200

    page = client_fixture.get(f"/api/delete")
    assert page.json == {"message": "Scheduler: all jobs deleted!"}
    assert page.status_code == 200
    # one  job should be left
    assert len(atlas_scheduler.get_jobs()) == 1


def test_pause_resume(client_fixture: fixture) -> None:
    # add a job
    p_id, t_id = create_demo_task(db.session)

    page = client_fixture.get(f"/api/add/{t_id}")
    assert page.json == {"message": "Scheduler: task job added!"}
    assert page.status_code == 200

    # pause
    page = client_fixture.get(f"/api/pause")
    assert page.json == {"message": "Scheduler: all jobs paused!"}
    assert page.status_code == 200

    assert atlas_scheduler.state == 2
    assert atlas_scheduler.running == True

    page = client_fixture.get(f"/api/resume")
    assert page.json == {"message": "Scheduler: all jobs resumed!"}
    assert page.status_code == 200

    assert atlas_scheduler.state == 1
    assert atlas_scheduler.running == True

    # resume with scheduler already enabled
    page = client_fixture.get(f"/api/resume")
    assert page.json == {"message": "Scheduler: all jobs resumed!"}
    assert page.status_code == 200

    assert atlas_scheduler.state == 1
    assert atlas_scheduler.running == True


def test_kill(client_fixture: fixture) -> None:
    page = client_fixture.get(f"/api/kill")
    assert page.json == {"message": "Scheduler: scheduler killed!"}
    assert page.status_code == 200

    assert atlas_scheduler.state == 0
    assert atlas_scheduler.running == False


def test_jobs(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task(db.session)
    page = client_fixture.get(f"/api/add/{t_id}")
    assert page.json == {"message": "Scheduler: task job added!"}
    assert page.status_code == 200

    # check that status is now enabled
    t = Task.query.get(t_id)
    assert t.enabled == 1

    # job should be in list
    page = client_fixture.get(f"/api/jobs")
    assert page.json == [t_id, t_id, t_id]  # we have 3 schedules
    assert page.status_code == 200


def test_details(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task(db.session)
    page = client_fixture.get(f"/api/add/{t_id}")
    assert page.json == {"message": "Scheduler: task job added!"}
    assert page.status_code == 200

    # check that status is now enabled
    t = Task.query.get(t_id)
    assert t.enabled == 1

    # job with no args
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="interval",
        seconds=10,
        id="test job 3",
        name="test job 3",
        replace_existing=True,
    )

    page = client_fixture.get(f"/api/details")
    job = atlas_scheduler.get_job(f"{p_id}-{t.id}-cron")
    text = page.json[0]

    del text["next_run_time"]
    assert text == {
        "name": job.name,
        "job_id": job.id,
        "id": job.args[0],
    }
    assert page.status_code == 200


def test_scheduled(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task(db.session)
    page = client_fixture.get(f"/api/add/{t_id}")
    assert page.json == {"message": "Scheduler: task job added!"}
    assert page.status_code == 200

    # check that status is now enabled
    t = Task.query.get(t_id)
    assert t.enabled == 1

    # job with no args
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="interval",
        seconds=10,
        id="test job 3",
        name="test job 3",
        replace_existing=True,
    )

    # job should be in list
    page = client_fixture.get(f"/api/scheduled")
    assert page.json == [t_id, t_id, t_id]  # we have three schedules
    assert page.status_code == 200


def test_delete_orphans(client_fixture: fixture) -> None:
    # run without any orphans
    page = client_fixture.get(f"/api/delete-orphans")
    assert page.json == {"message": "Scheduler: orphans deleted!"}
    assert page.status_code == 200

    # manually add a job to scheduler
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="interval",
        seconds=10,
        id="test job 2",
        name="test job 2",
        args=["99"],
        replace_existing=True,
    )

    assert len(atlas_scheduler.get_jobs()) == 1

    # job with no args
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="interval",
        seconds=10,
        id="test job 3",
        name="test job 3",
        replace_existing=True,
    )

    assert len(atlas_scheduler.get_jobs()) == 2

    page = client_fixture.get(f"/api/delete-orphans")
    assert page.json == {"message": "Scheduler: orphans deleted!"}
    assert page.status_code == 200

    assert len(atlas_scheduler.get_jobs()) == 1


def test_400(client_fixture: fixture) -> None:
    page = client_fixture.get("/nothing")
    assert page.status == "404 NOT FOUND"


def test_get_user_id(client_fixture: fixture) -> None:
    u = get_or_create(db.session, User, email="nothing")
    assert u.get_id() >= "1"
