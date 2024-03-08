"""Test web/task_controls.

run with::

   poetry run pytest web/tests/test_task_controls.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest web/tests/test_task_controls.py::test_delete_task \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings


"""

import json
import time

from flask import request, url_for
from pytest import fixture

from web.extensions import db

from .conftest import create_demo_task


def test_run_invalid_task(client_fixture: fixture) -> None:
    # test invalid task
    page = client_fixture.get(
        url_for("task_controls_bp.run_task", task_id=99), follow_redirects=True
    )
    assert page.status_code == 200
    assert "Task does not exist." in page.get_data(as_text=True)
    assert page.request.path in [
        url_for("project_bp.new_project_form"),
        url_for("task_bp.all_tasks"),
    ]


def test_run_valid_task(client_fixture: fixture) -> None:
    _, t_id = create_demo_task(db.session, 2025)

    page = client_fixture.get(
        url_for("task_controls_bp.run_task", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200
    assert page.request.path == url_for("task_bp.one_task", task_id=t_id)
    assert "Failed to run task." in page.get_data(as_text=True)


def test_scheduler_invalid_task(client_fixture: fixture) -> None:
    # test invalid task
    page = client_fixture.get(
        url_for("task_controls_bp.schedule_task", task_id=99), follow_redirects=True
    )
    assert page.status_code == 200
    assert "Task does not exist." in page.get_data(as_text=True)
    assert page.request.path in [
        url_for("task_bp.all_tasks"),
        url_for("project_bp.new_project"),
    ]


def test_scheduler_valid_task(client_fixture: fixture) -> None:
    _, t_id = create_demo_task(db.session, 2025)

    page = client_fixture.get(
        url_for("task_controls_bp.schedule_task", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200
    assert page.request.path == url_for("task_bp.one_task", task_id=t_id)
    assert "Scheduling task." in page.get_data(as_text=True)
    # failure message will be in executor.
    # time.sleep(1)
    executor = client_fixture.get(url_for("executors_bp.executor_status"))

    assert b"Failed to schedule" in executor.data


def test_enable_task(client_fixture: fixture) -> None:
    _, t_id = create_demo_task(db.session)
    page = client_fixture.get(
        url_for("task_controls_bp.enable_task", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200
    assert "enabling task" in page.get_data(as_text=True)
    time.sleep(1)  # wait for completion


def test_disable_task(client_fixture: fixture) -> None:
    _, t_id = create_demo_task(db.session)
    page = client_fixture.get(
        url_for("task_controls_bp.disable_task", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200
    assert "disabling task" in page.get_data(as_text=True)
    time.sleep(1)  # wait for completion


def test_duplicate_invalid_task(client_fixture: fixture) -> None:
    # test invalid task
    page = client_fixture.get(
        url_for("task_controls_bp.duplicate_task", task_id=99), follow_redirects=True
    )
    assert page.status_code == 200
    assert "Task does not exist" in page.get_data(as_text=True)


def test_duplicate_valid_task(client_fixture: fixture) -> None:
    _, t_id = create_demo_task(db.session)
    page = client_fixture.get(
        url_for("task_controls_bp.duplicate_task", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200

    assert "- Duplicated" in page.get_data(as_text=True)


def test_invalid_task_status(client_fixture: fixture) -> None:
    # test invalid task
    page = client_fixture.get(url_for("task_controls_bp.task_status", task_id=99))
    assert page.status_code == 200
    assert json.loads(page.get_data(as_text=True)) == {}


def test_valid_task_status(client_fixture: fixture) -> None:
    _, t_id = create_demo_task(db.session)
    page = client_fixture.get(url_for("task_controls_bp.task_status", task_id=t_id))
    assert page.status_code == 200
    assert json.loads(page.get_data(as_text=True))["status"] == ""


def test_delete_invalid_task(client_fixture: fixture) -> None:
    # test invalid task
    page = client_fixture.get(
        url_for("task_controls_bp.delete_task", task_id=99), follow_redirects=True
    )
    assert page.status_code == 200
    assert page.request.path == url_for("project_bp.new_project")
    assert "Task does not exist." in page.get_data(as_text=True)


def test_delete_valid_task(client_fixture: fixture) -> None:
    _, t_id = create_demo_task(db.session)
    page = client_fixture.get(
        url_for("task_controls_bp.delete_task", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200
    assert b"Deleting task" in page.data

    # this will show in executor messages
    executor = client_fixture.get(url_for("executors_bp.executor_status"))
    assert b"Failed to disable task." in executor.data


def test_end_retry_invalid_task(client_fixture: fixture) -> None:
    # test invalid task
    page = client_fixture.get(
        url_for("task_controls_bp.task_endretry", task_id=99), follow_redirects=True
    )
    assert page.status_code == 200
    # no tasks exist so going to project.. depends on order of tests
    assert page.request.path in [
        url_for("project_bp.new_project"),
        url_for("task_bp.all_tasks"),
    ]
    assert "Task does not exist." in page.get_data(as_text=True)


def test_end_retry_valid_task(client_fixture: fixture) -> None:
    _, t_id = create_demo_task(db.session)
    page = client_fixture.get(
        url_for("task_controls_bp.task_endretry", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200

    # this will show in executor messages
    # time.sleep(1)
    executor = client_fixture.get(url_for("executors_bp.executor_status"))
    assert "Failed to disable" in executor.get_data(as_text=True)


def test_reset_invalid_task(client_fixture: fixture) -> None:
    # test invalid task
    page = client_fixture.get(
        url_for("task_controls_bp.reset_task", task_id=99), follow_redirects=True
    )
    assert page.status_code == 200
    assert page.request.path == url_for("project_bp.new_project")
    assert "Task does not exist." in page.get_data(as_text=True)


def test_reset_valid_task(client_fixture: fixture) -> None:
    _, t_id = create_demo_task(db.session)
    page = client_fixture.get(
        url_for("task_controls_bp.reset_task", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200

    assert "Task has been reset to completed." in page.get_data(as_text=True)
