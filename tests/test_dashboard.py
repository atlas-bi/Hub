# flake8: noqa,
# pylint: skip-file
from datetime import datetime

import pytest
from flask import g

from em_web.model import Project, Task


def test_search(em_web_authed):
    response = em_web_authed.get("/search")
    assert response.status_code == 200


def test_schedule(em_web_authed):
    response = em_web_authed.get("/schedule")
    assert response.status_code == 200


# these tests will not run on sqlite
def test_error_guage(em_web_authed):
    response = em_web_authed.get("/dash/errorGauge")
    assert response.status_code == 200


def test_run_guage(em_web_authed):
    response = em_web_authed.get("/dash/runGauge")
    assert response.status_code == 200


def test_errored_schedule_now(em_web_authed):
    response = em_web_authed.get("/dash/errored/schedule", follow_redirects=True)
    assert response.status_code == 200


def test_scheduled_schedule_now(em_web_authed):
    response = em_web_authed.get("/dash/scheduled/reschedule", follow_redirects=True)
    assert response.status_code == 200


def test_orphaned_delete(em_web_authed):
    response = em_web_authed.get("/dash/orphans/delete", follow_redirects=True)
    assert response.status_code == 200


def test_errored_run(em_web_authed):
    response = em_web_authed.get("/dash/errored/run", follow_redirects=True)
    assert response.status_code == 200


def test_active_run(em_web_authed):
    response = em_web_authed.get("/dash/active/run", follow_redirects=True)
    assert response.status_code == 200


def test_scheduled_run(em_web_authed):
    response = em_web_authed.get("/dash/scheduled/run", follow_redirects=True)
    assert response.status_code == 200


def test_scheduled_disable(em_web_authed):
    response = em_web_authed.get("/dash/scheduled/disable", follow_redirects=True)
    assert response.status_code == 200
