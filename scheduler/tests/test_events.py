"""Test scheduler.

run with::

   poetry run pytest scheduler/tests/test_events.py \
   --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings

   poetry run pytest tests/test_events.py::test_job_missed -v \
   --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings

"""

print("importing tests")
import time
from datetime import datetime, timedelta

from pytest import fixture

print("importing scheduler")
from scheduler.extensions import atlas_scheduler, db
from scheduler.model import TaskLog

from .conftest import bad_demo_task, create_demo_task, demo_task


# assert 1==2
def test_job_missed(api_fixture: fixture, caplog: fixture) -> None:
    # grace time is 30 seconds, so attempt to run 40 seconds ago
    # get a task ID.. task isnt' used
    p_id, t_id = create_demo_task(db.session)

    # create an interval task (only interval and cron can capture
    # a missed job and add to logs. one-off jobs disappear after run.)
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="date",
        id=f"{p_id}-{t_id}-ooff",
        name="test_job_missed",
        args=[str(t_id)],
        run_date=datetime.now() - timedelta(minutes=1),
        replace_existing=True,
    )
    # wait for logs to be added by background process
    time.sleep(1)
    # check that log was added
    log = TaskLog.query.filter_by(task_id=t_id, status_id=6, error=1).first()
    assert "Job missed. Scheduled for:" in log.message

    # check logs
    assert "was missed by 0:01" in caplog.text
    for record in caplog.records:
        assert record.levelname not in ["CRITICAL", "ERROR"]

    caplog.clear()

    # check without id
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="date",
        id="asdf",
        name="test_job_missed 2",
        args=[str(t_id)],
        run_date=datetime.now() - timedelta(minutes=1),
        replace_existing=True,
    )
    time.sleep(1)
    assert "was missed by 0:01" in caplog.text
    caplog.clear()

    # task that does not exists
    p_id, t_id = (9, 9)
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="date",
        id=f"{p_id}-{t_id}-ooff",
        name="test_job_missed 3",
        args=[str(t_id)],
        run_date=datetime.now() - timedelta(minutes=1),
        replace_existing=True,
    )
    # wait for logs to be added by background process
    time.sleep(1)
    # check that log was added
    # log = TaskLog.query.filter_by(task_id=t_id, status_id=6, error=1).first()
    # assert "Job missed. Scheduled for:" in log.message


def test_job_error(api_fixture: fixture, caplog: fixture) -> None:
    # get a dummy task id
    p_id, t_id = create_demo_task(db.session)

    # add a task that will fail
    atlas_scheduler.add_job(
        func=bad_demo_task,
        trigger="date",
        id=f"{p_id}-{t_id}-ooff",
        name="test_job_error",
        replace_existing=True,
    )

    time.sleep(1)

    # verify failure
    log = (
        TaskLog.query.filter_by(task_id=t_id, status_id=6, error=1)
        .filter(TaskLog.message.like("%Job error. Scheduled for:%"))  # type: ignore[attr-defined,union-attr]
        .first()
    )
    assert log is not None

    assert "raised an exception" in caplog.text

    caplog.clear()

    # try with invalid job
    p_id, t_id = (9, 9)
    atlas_scheduler.add_job(
        func=bad_demo_task,
        trigger="date",
        id=f"{p_id}-{t_id}-ooff",
        name="test_job_error 2",
        replace_existing=True,
    )
    time.sleep(1)
    # verify failure
    log = (
        TaskLog.query.filter_by(task_id=t_id, status_id=6, error=1)
        .filter(TaskLog.message.like("%Job error. Scheduled for:%"))  # type: ignore[attr-defined,union-attr]
        .first()
    )
    assert log is None

    # test job without id
    atlas_scheduler.add_job(
        func=bad_demo_task,
        trigger="date",
        id="ooff",
        name="test_job_error 3",
        replace_existing=True,
    )

    time.sleep(1)


def test_job_executed(api_fixture: fixture, caplog: fixture) -> None:
    caplog.clear()
    # get a dummy task id
    p_id, t_id = create_demo_task(db.session)

    # add a task that will run
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="date",
        id=f"{p_id}-{t_id}-ooff",
        name="test job 2",
        replace_existing=True,
    )
    # give time to execute
    time.sleep(1)

    # verify execution
    # the 2nd to last log should be that the job has executed.
    # last log will be job removed.
    log = (
        TaskLog.query.filter_by(task_id=t_id, status_id=6)
        .filter(TaskLog.message.like("%Job excecuted in%"))  # type: ignore[attr-defined,union-attr]
        .first()
    )
    assert log is not None

    assert "Running job" in caplog.text
    assert "executed successfully" in caplog.text

    for record in caplog.records:
        assert record.levelname not in ["CRITICAL", "ERROR"]

    caplog.clear()

    # try with invalid job
    p_id, t_id = (9, 9)
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="date",
        id=f"{p_id}-{t_id}-ooff",
        name="test job 2",
        replace_existing=True,
    )

    time.sleep(1)

    # verify no logs
    log = (
        TaskLog.query.filter_by(task_id=t_id, status_id=6)
        .filter(TaskLog.message.like("%Job excecuted in%"))  # type: ignore[attr-defined,union-attr]
        .first()
    )
    assert log is None

    for record in caplog.records:
        assert record.levelname not in ["CRITICAL", "ERROR"]

    caplog.clear()

    # test job without id
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="date",
        id="ooff",
        name="test job 2",
        replace_existing=True,
    )

    time.sleep(1)

    for record in caplog.records:
        assert record.levelname not in ["CRITICAL", "ERROR"]


def test_job_added(api_fixture: fixture, caplog: fixture) -> None:
    # get a dummy task id
    p_id, t_id = create_demo_task(db.session)

    # add a task that will run
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="date",
        id=f"{p_id}-{t_id}-ooff",
        name="test job 2",
        replace_existing=True,
    )
    # give time to execute
    time.sleep(1)

    log = (
        TaskLog.query.filter_by(task_id=t_id, status_id=6)
        .filter(TaskLog.message.like("%Job added. Scheduled for:%"))  # type: ignore[attr-defined,union-attr]
        .first()
    )
    assert log is not None

    assert 'Added job "test job 2"' in caplog.text

    for record in caplog.records:
        assert record.levelname not in ["CRITICAL", "ERROR"]

    # test with invalid task id
    p_id, t_id = (9, 9)
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="date",
        id=f"{p_id}-{t_id}-ooff",
        name="test job 2",
        replace_existing=True,
    )

    time.sleep(1)

    log = (
        TaskLog.query.filter_by(task_id=t_id, status_id=6)
        .filter(TaskLog.message.like("%Job added. Scheduled for:%"))  # type: ignore[attr-defined,union-attr]
        .first()
    )
    assert log is None

    assert 'Added job "test job 2"' in caplog.text


def test_job_removed(api_fixture: fixture, caplog: fixture) -> None:
    # get a dummy task id
    p_id, t_id = create_demo_task(db.session)

    # add a task that will run
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="date",
        id=f"{p_id}-{t_id}-ooff",
        name="test job 2",
        replace_existing=True,
    )

    # give time to process
    time.sleep(1)

    assert "Removed job" in caplog.text
    for record in caplog.records:
        assert record.levelname not in ["CRITICAL", "ERROR"]

    log = TaskLog.query.filter_by(task_id=t_id, status_id=6, message="Job removed.").first()
    assert log is not None
    caplog.clear()
    # try invalid task_id

    p_id, t_id = (9, 9)
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="date",
        id=f"{p_id}-{t_id}-ooff",
        name="test job 2",
        replace_existing=True,
    )
    time.sleep(1)

    assert "Removed job" in caplog.text

    for record in caplog.records:
        assert record.levelname not in ["CRITICAL", "ERROR"]

    log = TaskLog.query.filter_by(task_id=t_id, status_id=6, message="Job removed.").first()
    assert log is None
    caplog.clear()

    # test with no id
    atlas_scheduler.add_job(
        func=demo_task,
        trigger="date",
        id="ooff",
        name="test job 2",
        replace_existing=True,
    )
    time.sleep(1)

    assert "Removed job" in caplog.text
    for record in caplog.records:
        assert record.levelname not in ["CRITICAL", "ERROR"]

    log = TaskLog.query.filter_by(task_id=t_id, status_id=6, message="Job removed.").first()
    assert log is None


# def test_job_submitted(api_fixture: fixture, caplog: fixture) -> None:
#    # get a dummy task id
#    p_id,t_id = create_demo_task(db.session)

#    # add a task that will run
#    atlas_scheduler.add_job(func=demo_task,
#      trigger="interval",
#      id=f"{p_id}-{t_id}-intv",
#      name="test job 2",
#      seconds=2,
#      replace_existing=True,
#    )
#    atlas_scheduler.pause_job(f"{p_id}-{t_id}-intv")
# #   job.resume()

#    # give time to process. job must run, then be readded
#    time.sleep(5)

#    assert "Job submitted" in caplog.text
#    for record in caplog.records:
#       assert record.levelname not in ["CRITICAL", "ERROR"]

#    log = TaskLog.query.filter_by(task_id=t_id, status_id=6, message="Job submitted.").first()
#    assert log is not None
#    caplog.clear()
#    # try invalid task_id

#    p_id, t_id = (9,9)
#    atlas_scheduler.add_job(func=demo_task,
#      trigger="date",
#      id=f"{p_id}-{t_id}-ooff",
#      name="test job 2",
#      run_date=datetime.now() + timedelta(seconds=10),
#      replace_existing=True,
#    )
#    time.sleep(2)

#    assert "Removed job" in caplog.text

#    for record in caplog.records:
#       assert record.levelname not in ["CRITICAL", "ERROR"]

#    log = TaskLog.query.filter_by(task_id=t_id, status_id=6, message="Job submitted.").first()
#    assert log is None
#    caplog.clear()

#    # test with no id
#    atlas_scheduler.add_job(func=demo_task,
#      trigger="date",
#      id=f"ooff",
#      name="test job 2",
#      run_date=datetime.now() + timedelta(seconds=10),
#      replace_existing=True,
#    )
#    time.sleep(2)

#    assert "Removed job" in caplog.text
#    for record in caplog.records:
#       assert record.levelname not in ["CRITICAL", "ERROR"]

#    log = TaskLog.query.filter_by(task_id=t_id, status_id=6, message="Job submitted.").first()
#    assert log is None
