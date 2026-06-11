"""Test runner/web.

run with::

   poetry run pytest runner/tests/test_web.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest runner/tests/test_web.py::test_resume_with_scheduler \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings


"""

from pytest import fixture

from runner.extensions import db
from runner.model import Project, Task, TaskLog

from .conftest import create_demo_task

# def test_source_code(client_fixture: fixture) -> None:
#     project = Project(name="demo")
#     db.session.add(project)
#     db.session.commit()

#     task = Task(
#         name="blah", source_query_type_id=1, source_git=None, project_id=project.id
#     )
#     db.session.add(task)
#     db.session.commit()

#     page = client_fixture.get(f"/api/{task.id}/source_code")
#     assert b"code" in page.data


def test_alive(client_fixture: fixture) -> None:
    page = client_fixture.get("/api")
    assert page.json == {"status": "alive"}


def test_run_missing_task(client_fixture: fixture) -> None:
    page = client_fixture.get("/api/999999")
    assert page.json == {"error": "Task 999999 not found."}


def test_run_logs_received_request(client_fixture: fixture, monkeypatch: fixture) -> None:
    _, task_id = create_demo_task()

    class FakeFuture:
        def add_done_callback(self, callback):  # noqa: ANN001, ANN201
            return None

    def submit(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        return FakeFuture()

    monkeypatch.setattr("runner.web.web.executor.submit", submit)

    page = client_fixture.get(f"/api/{task_id}")

    assert page.json == {"message": "runner completed."}
    assert (
        TaskLog.query.filter_by(task_id=task_id, status_id=8)
        .filter(TaskLog.message.like("%Runner received run request from scheduler.%"))
        .first()
        is not None
    )


def test_run_logs_queue_failure(client_fixture: fixture, monkeypatch: fixture) -> None:
    _, task_id = create_demo_task()

    def submit(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        raise RuntimeError("executor full")

    monkeypatch.setattr("runner.web.web.executor.submit", submit)

    page = client_fixture.get(f"/api/{task_id}")

    assert page.status_code == 500
    assert page.json == {"error": "Runner failed to queue task."}
    assert (
        TaskLog.query.filter_by(task_id=task_id, status_id=8, error=1)
        .filter(TaskLog.message.like("%Runner failed to queue task.%executor full%"))
        .first()
        is not None
    )
