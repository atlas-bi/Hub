"""Test web/admin.

run with::

   poetry run pytest web/tests/test_admin.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest web/tests/test_admin.py::test_online \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings


"""

from flask import url_for
from pytest import fixture

from web.extensions import db
from web.model import Task

from .conftest import check_url, create_demo_task

# test homepage


def test_online(client_fixture: fixture) -> None:
    check_url(client_fixture, "/admin")

    # test with message
    page = check_url(client_fixture, "/admin?message=nice message", True)
    assert "nice message" in page


def test_pause(client_fixture: fixture) -> None:
    page = check_url(client_fixture, url_for("admin_bp.pause_scheduler"), True)
    assert "Failed to pause scheduler. Scheduler offline." in page


def test_resume(client_fixture: fixture) -> None:
    page = check_url(client_fixture, url_for("admin_bp.resume_scheduler"), True)
    assert "Failed to resume scheduler. Scheduler offline." in page


def test_kill(client_fixture: fixture) -> None:
    check_url(client_fixture, url_for("admin_bp.kill_scheduler"), True)


def test_reload_jobs(client_fixture: fixture) -> None:
    page = check_url(client_fixture, url_for("admin_bp.reschedule_tasks"), True)

    assert "Failed to remove jobs from scheduler. Scheduler offline." in page

    # add an enabled task and try again
    p_id, t_id = create_demo_task(db.session, 2021)
    Task.query.get(t_id).enabled = 1
    db.session.commit()

    page = check_url(client_fixture, url_for("admin_bp.reschedule_tasks"), True)

    assert "Failed to remove jobs from scheduler. Scheduler offline." in page


def test_reset_tasks(client_fixture: fixture) -> None:
    check_url(client_fixture, url_for("admin_bp.reset_tasks"), True)
