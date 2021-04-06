# flake8: noqa,
# pylint: skip-file
import json

import pytest
from flask import g

from em_scheduler.model import Task

# need to add a dummy task, then run tests against that task.
# delete task at the end


def test_fourhundred(scheduler_client):
    response = scheduler_client.get("/api/blah")

    assert response.status_code == 404

    data = json.loads(response.data.decode("utf8"))
    assert data["error"]
    scheduler_client.get("/api/pause")


def test_alive(scheduler_client):
    response = scheduler_client.get("/api")
    assert response.status_code == 200
    data = json.loads(response.data.decode("utf8"))

    assert data["status"] == "alive"


def test_add_task(scheduler_client):
    scheduler_client.get("/api/resume")
    response = scheduler_client.get("/api/add/" + str(g.get("task_id")))
    assert response.status_code == 200

    data = json.loads(response.data.decode("utf8"))

    assert data == {"message": "Scheduler: task job added!"}

    scheduler_client.get("/api/pause")


def test_run_task(scheduler_client):
    scheduler_client.get("/api/resume")
    response = scheduler_client.get("/api/run/" + str(g.get("task_id")))

    assert response.status_code == 200

    data = json.loads(response.data.decode("utf8"))

    # if em_runner is not started, there will be error. if
    # it is running, there should be a response.
    assert data.get("error") or data["message"]

    scheduler_client.get("/api/pause")


def test_jobs(scheduler_client):
    scheduler_client.get("/api/resume")
    scheduler_client.get("/api/add/" + str(g.get("task_id")))
    response = scheduler_client.get("/api/jobs")
    assert response.status_code == 200

    scheduler_client.get("/api/pause")


def test_delete_task(scheduler_client):
    scheduler_client.get("/api/resume")
    add = scheduler_client.get("/api/add/" + str(g.get("task_id")))

    response = scheduler_client.get("/api/delete/" + str(g.get("task_id")))
    assert response.status_code == 200

    scheduler_client.get("/api/pause")


def test_details(scheduler_client):
    scheduler_client.get("/api/resume")
    scheduler_client.get("/api/add/" + str(g.get("task_id")))

    response = scheduler_client.get("/api/details")
    assert response.status_code == 200

    data = json.loads(response.data.decode("utf8"))
    assert data

    scheduler_client.get("/api/pause")


def test_scheduled(scheduler_client):
    scheduler_client.get("/api/resume")
    scheduler_client.get("/api/add/" + str(g.get("task_id")))

    response = scheduler_client.get("/api/scheduled")
    assert response.status_code == 200

    data = json.loads(response.data.decode("utf8"))
    assert data

    scheduler_client.get("/api/pause")


def test_delete(scheduler_client):
    scheduler_client.get("/api/resume")
    response = scheduler_client.get("/api/delete")
    assert response.status_code == 200

    data = json.loads(response.data.decode("utf8"))

    assert data == {"message": "Scheduler: all jobs deleted!"}

    scheduler_client.get("/api/pause")


def test_pause(scheduler_client):
    scheduler_client.get("/api/resume")
    response = scheduler_client.get("/api/pause")
    assert response.status_code == 200

    # data = json.loads(response.data.decode("utf8"))

    # assert data == {"message": "Scheduler: all jobs paused!"}

    scheduler_client.get("/api/pause")


def test_resume(scheduler_client):
    scheduler_client.get("/api/resume")
    response = scheduler_client.get("/api/resume")
    assert response.status_code == 200

    # data = json.loads(response.data.decode("utf8"))

    # assert data == {"message": "Scheduler: all jobs resumed!"}

    scheduler_client.get("/api/pause")


def test_shutdown(scheduler_client):
    scheduler_client.get("/api/resume")
    response = scheduler_client.get("/api/shutdown")
    assert response.status_code == 200

    # data = json.loads(response.data.decode("utf8"))

    # assert data == {"message": "Scheduler: scheduler shutdown!"}

    scheduler_client.get("/api/pause")


def test_kill(scheduler_client):
    scheduler_client.get("/api/resume")
    response = scheduler_client.get("/api/kill")
    assert response.status_code == 200

    data = json.loads(response.data.decode("utf8"))

    # scheduler has already been shutdown
    assert data["error"]


def test_delete_orphans(scheduler_client):
    scheduler_client.get("/api/resume")
    response = scheduler_client.get("/api/delete-orphans")
    assert response.status_code == 200

    data = json.loads(response.data.decode("utf8"))

    assert data == {"message": "Scheduler: orphans deleted!"}

    scheduler_client.get("/api/pause")
