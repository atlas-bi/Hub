# flake8: noqa,
# pylint: skip-file
# check all admin links

from datetime import datetime

import pytest
from flask import g

from em_web.model import Project, Task


def test_admin_online(em_web_authed):
    page = em_web_authed.get("/admin")
    assert page.status_code == 200


"""
    Scheduler Tasks
"""


def test_admin_empty(em_web_authed):
    page = em_web_authed.get("/admin/emptyScheduler", follow_redirects=True)
    assert page.status_code == 200

    assert "flashes" in page.get_data(as_text=True)


def test_admin_pause(em_web_authed):
    page = em_web_authed.get("/admin/pauseJobs", follow_redirects=True)

    assert page.status_code == 200

    assert "flashes" in page.get_data(as_text=True)


def test_admin_resume(em_web_authed):
    page = em_web_authed.get("/admin/resumeJobs", follow_redirects=True)
    assert page.status_code == 200

    assert "flashes" in page.get_data(as_text=True)


def test_admin_stop(em_web_authed):
    page = em_web_authed.get("/admin/stopJobs", follow_redirects=True)
    assert page.status_code == 200

    assert "flashes" in page.get_data(as_text=True)


def test_admin_kill(em_web_authed):
    page = em_web_authed.get("/admin/killJobs", follow_redirects=True)
    assert page.status_code == 200

    assert "flashes" in page.get_data(as_text=True)


"""
    Job tasks
"""


def test_admin_reload_jobs(em_web_authed):
    page = em_web_authed.get("/admin/reloadJobs", follow_redirects=True)
    assert page.status_code == 200

    assert "flashes" in page.get_data(as_text=True)


def test_admin_reset_tasks(em_web_authed):
    page = em_web_authed.get("/admin/resetTasks", follow_redirects=True)
    assert page.status_code == 200

    assert "flashes" in page.get_data(as_text=True)


def test_admin_clear_logs(em_web_authed):
    page = em_web_authed.get("/admin/clearlog", follow_redirects=True)
    assert page.status_code == 200

    assert "flashes" in page.get_data(as_text=True)


"""
    Server Tasks
"""


def test_admin_reload(em_web_authed):
    page = em_web_authed.get("/admin/reloadDaemon", follow_redirects=True)
    assert page.status_code == 200

    assert "flashes" in page.get_data(as_text=True)


def test_admin_restart(em_web_authed):
    page = em_web_authed.get("/admin/restartDaemon", follow_redirects=True)
    assert page.status_code == 200

    assert "flashes" in page.get_data(as_text=True)


def test_admin_whoami(em_web_authed):
    page = em_web_authed.get("/admin/whoami", follow_redirects=True)
    print(page.get_data(as_text=True))
    assert page.status_code == 200

    assert "flashes" in page.get_data(as_text=True)
