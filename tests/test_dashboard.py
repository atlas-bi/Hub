# flake8: noqa,
# pylint: skip-file
from datetime import datetime

import pytest
from flask import g

from em_web.model import Project, Task


def test_errored_schedule_now(em_web_authed):
    assert (
        em_web_authed.get("/dash/errored/schedule", follow_redirects=True).status_code
        == 200
    )


def test_scheduled_schedule_now(em_web_authed):
    assert (
        em_web_authed.get(
            "/dash/scheduled/reschedule", follow_redirects=True
        ).status_code
        == 200
    )


def test_orphaned_delete(em_web_authed):
    assert (
        em_web_authed.get("/dash/orphans/delete", follow_redirects=True).status_code
        == 200
    )
