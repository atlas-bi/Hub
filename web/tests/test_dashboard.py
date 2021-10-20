"""Test web/admin.

run with::

   poetry run pytest tests/test_dashboard.py \
       --cov --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest tests/test_dashboard.py::test_schedule \
       --cov --cov-branch --cov-append --cov-report=term-missing --disable-warnings


"""


from pytest import fixture

from .conftest import create_demo_task


def test_search(client_fixture: fixture) -> None:
    # add a task and project
    create_demo_task(2025)

    response = client_fixture.get("/search")
    assert response.status_code == 200

    # verify search data
    assert response.get_json()["task"]["/task/1"] is not None
    assert response.get_json()["project"]["/project/1"] is not None


def test_home_with_project(client_fixture: fixture) -> None:
    # add a task and project
    create_demo_task(2025)

    response = client_fixture.get("/", follow_redirects=True)
    assert response.status_code == 200
    # verify we are on the user project page
    assert response.request.path == "/"


def test_schedule(client_fixture: fixture) -> None:
    # offline scheduler should return nothing
    response = client_fixture.get("/schedule")
    assert response.status_code == 200

    assert response.get_data(as_text=True) == ""


def test_schedule_with_scheduler(
    client_fixture: fixture, client_fixture_with_scheduler: fixture
) -> None:
    response = client_fixture.get("/schedule")
    assert response.status_code == 200
    assert "em-timelineScale" in response.get_data(as_text=True)


def test_errored_schedule_now(client_fixture: fixture) -> None:
    response = client_fixture.get("/dash/errored/schedule", follow_redirects=True)
    assert response.status_code == 200


def test_scheduled_schedule_now(client_fixture: fixture) -> None:
    response = client_fixture.get("/dash/scheduled/reschedule", follow_redirects=True)
    assert response.status_code == 200


def test_orphaned_delete(client_fixture: fixture) -> None:
    response = client_fixture.get("/dash/orphans/delete", follow_redirects=True)
    assert response.status_code == 200

    assert "Failed to delete orphans. Scheduler offline." in response.get_data(
        as_text=True
    )


def test_orphaned_delete_with_scheduler(
    client_fixture: fixture, client_fixture_with_scheduler: fixture
) -> None:
    response = client_fixture.get("/dash/orphans/delete", follow_redirects=True)
    assert response.status_code == 200

    assert "Scheduler: orphans deleted!" in response.get_data(as_text=True)


def test_errored_run(client_fixture: fixture) -> None:
    response = client_fixture.get("/dash/errored/run", follow_redirects=True)
    assert response.status_code == 200


def test_active_run(client_fixture: fixture) -> None:
    response = client_fixture.get("/dash/active/run", follow_redirects=True)
    assert response.status_code == 200


def test_scheduled_run(client_fixture: fixture) -> None:
    response = client_fixture.get("/dash/scheduled/run", follow_redirects=True)
    assert response.status_code == 200


def test_scheduled_disable(client_fixture: fixture) -> None:
    response = client_fixture.get("/dash/scheduled/disable", follow_redirects=True)
    assert response.status_code == 200
