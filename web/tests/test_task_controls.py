"""Test web/task_controls.

run with::

   poetry run pytest web/tests/test_task_controls.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest web/tests/test_task_controls.py::test_delete_task \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings


"""
import json

from flask import request, url_for
from pytest import fixture

from .conftest import create_demo_task


def test_run_task(client_fixture: fixture) -> None:

    # test invalid task
    page = client_fixture.get(
        url_for("task_controls_bp.run_task", task_id=99), follow_redirects=True
    )
    assert page.status_code == 200
    assert "Task does not exist." in page.get_data(as_text=True)
    assert request.path == url_for("project_bp.new_project_form")

    _, t_id = create_demo_task(2025)

    page = client_fixture.get(
        url_for("task_controls_bp.run_task", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200
    assert request.path == url_for("task_bp.one_task", task_id=t_id)
    assert "Failed to run task." in page.get_data(as_text=True)


# def test_run_task_with_scheduler(client_fixture_with_scheduler: fixture) -> None:

#     _, t_id = create_demo_task(2025)

#     page = client_fixture_with_scheduler.get(
#         url_for("task_controls_bp.run_task", task_id=t_id), follow_redirects=True
#     )
#     assert page.status_code == 200
#     assert request.path == url_for("task_bp.one_task", task_id=t_id)
#     assert "Task run started." in page.get_data(as_text=True)


def test_scheduler_task(client_fixture: fixture) -> None:

    # test invalid task
    page = client_fixture.get(
        url_for("task_controls_bp.schedule_task", task_id=99), follow_redirects=True
    )
    assert page.status_code == 200
    assert "Task does not exist." in page.get_data(as_text=True)
    assert request.path == url_for("task_bp.all_tasks")

    _, t_id = create_demo_task(2025)

    page = client_fixture.get(
        url_for("task_controls_bp.schedule_task", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200
    assert request.path == url_for("task_bp.one_task", task_id=t_id)
    assert "Scheduling task." in page.get_data(as_text=True)
    # failure message will be in executor.
    executor = client_fixture.get(url_for("executors_bp.executor_status"))
    assert b"Failed to schedule" in executor.data


# def test_scheduler_task_with_scheduler(client_fixture_with_scheduler: fixture) -> None:

#     _, t_id = create_demo_task(2025)

#     page = client_fixture_with_scheduler.get(
#         url_for("task_controls_bp.schedule_task", task_id=t_id), follow_redirects=True
#     )
#     assert page.status_code == 200
#     assert request.path == url_for("task_bp.one_task", task_id=t_id)
#     assert "Scheduling task." in page.get_data(as_text=True)


def test_enable_task(client_fixture: fixture) -> None:
    _, t_id = create_demo_task()
    page = client_fixture.get(
        url_for("task_controls_bp.enable_task", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200
    assert "enabling task" in page.get_data(as_text=True)


def test_disable_task(client_fixture: fixture) -> None:

    _, t_id = create_demo_task()
    page = client_fixture.get(
        url_for("task_controls_bp.disable_task", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200
    assert "disabling task" in page.get_data(as_text=True)


def test_duplicate_task(client_fixture: fixture) -> None:

    # test invalid task
    page = client_fixture.get(
        url_for("task_controls_bp.duplicate_task", task_id=99), follow_redirects=True
    )
    assert page.status_code == 200
    assert "Task does not exist" in page.get_data(as_text=True)

    _, t_id = create_demo_task()
    page = client_fixture.get(
        url_for("task_controls_bp.duplicate_task", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200

    assert "- Duplicated" in page.get_data(as_text=True)


def test_task_status(client_fixture: fixture) -> None:

    # test invalid task
    page = client_fixture.get(url_for("task_controls_bp.task_status", task_id=99))
    assert page.status_code == 200
    assert json.loads(page.get_data(as_text=True)) == {}

    _, t_id = create_demo_task()
    page = client_fixture.get(url_for("task_controls_bp.task_status", task_id=t_id))
    assert page.status_code == 200
    assert json.loads(page.get_data(as_text=True))["status"] == ""


def test_delete_task(client_fixture: fixture) -> None:

    # test invalid task
    page = client_fixture.get(
        url_for("task_controls_bp.delete_task", task_id=99), follow_redirects=True
    )
    assert page.status_code == 200
    assert request.path == url_for("task_bp.all_tasks")
    assert "Task does not exist." in page.get_data(as_text=True)

    _, t_id = create_demo_task()
    page = client_fixture.get(
        url_for("task_controls_bp.delete_task", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200
    assert b"Deleting task" in page.data

    # this will show in executor messages
    executor = client_fixture.get(url_for("executors_bp.executor_status"))
    assert b"Failed to disable task." in executor.data


def test_delete_task_with_scheduler(client_fixture_with_scheduler: fixture) -> None:

    p_id, t_id = create_demo_task()
    page = client_fixture_with_scheduler.get(
        url_for("task_controls_bp.delete_task", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200

    assert "Deleting task." in page.get_data(as_text=True)
    assert request.path == url_for("project_bp.one_project", project_id=p_id)


def test_end_retry(client_fixture: fixture) -> None:

    # test invalid task
    page = client_fixture.get(
        url_for("task_controls_bp.task_endretry", task_id=99), follow_redirects=True
    )
    assert page.status_code == 200
    assert request.path == url_for("task_bp.all_tasks")
    assert "Task does not exist." in page.get_data(as_text=True)

    _, t_id = create_demo_task()
    page = client_fixture.get(
        url_for("task_controls_bp.task_endretry", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200

    # this will show in executor messages
    executor = client_fixture.get(url_for("executors_bp.executor_status"))
    assert b"Failed to disable" in executor.data


def test_reset(client_fixture: fixture) -> None:

    # test invalid task
    page = client_fixture.get(
        url_for("task_controls_bp.reset_task", task_id=99), follow_redirects=True
    )
    assert page.status_code == 200
    assert request.path == url_for("task_bp.all_tasks")
    assert "Task does not exist." in page.get_data(as_text=True)

    _, t_id = create_demo_task()
    page = client_fixture.get(
        url_for("task_controls_bp.reset_task", task_id=t_id), follow_redirects=True
    )
    assert page.status_code == 200

    assert "Task has been reset to completed." in page.get_data(as_text=True)
