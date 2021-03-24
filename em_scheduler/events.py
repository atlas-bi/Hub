"""Log scheduler events.

Scheduler events have a listener added to trigger a logging function.
The event details are logged to ``Model.TaskLog``.

These logs will only be from scheduler events (starting/stoping/etc)
and not from the actual details of the run. Run detail are added to
the logs by ``em_runner``.

Events saved to :obj:`em_scheduler.model.TaskLog`:

* EVENT_JOB_ADDED
* EVENT_JOB_ERROR
* EVENT_JOB_EXECUTED
* EVENT_JOB_MISSED
* EVENT_JOB_REMOVED
* EVENT_JOB_SUBMITTED

Events not saved to :obj:`em_scheduler.model.TaskLog`:

* EVENT_ALL_JOBS_REMOVED
* EVENT_EXECUTOR_ADDED
* EVENT_EXECUTOR_REMOVED
* EVENT_JOB_MAX_INSTANCES
* EVENT_JOB_MODIFIED
* EVENT_JOBSTORE_ADDED
* EVENT_JOBSTORE_REMOVED
* EVENT_SCHEDULER_PAUSED,
* EVENT_SCHEDULER_RESUMED
* EVENT_SCHEDULER_SHUTDOWN
* EVENT_SCHEDULER_STARTED

"""

import datetime

from apscheduler.events import (
    EVENT_JOB_ADDED,
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_MISSED,
    EVENT_JOB_REMOVED,
    EVENT_JOB_SUBMITTED,
)

from em_scheduler.extensions import db, scheduler
from em_scheduler.model import Task, TaskLog


def scheduler_logs(app):
    """Wrap function to pass app context to all logs."""

    def job_missed(event):
        with app.app_context():
            job = scheduler.get_job(event.job_id)
            if job:
                task = Task.query.filter_by(id=job.args[0]).first()
                ex_time = (
                    datetime.datetime.now(datetime.timezone.utc)
                    - event.scheduled_run_time
                )
                if task:
                    log = TaskLog(
                        task_id=task.id if task else event.job_id,
                        status_id=6,
                        error=1,
                        message="Job missed. Scheduled for: "
                        + datetime.datetime.strftime(
                            event.scheduled_run_time,
                            "%a, %b %-d, %Y %H:%M:%S",
                        )
                        + ". Missed by : "
                        + str(ex_time),
                    )
                    db.session.add(log)
                    db.session.commit()

    def job_error(event):
        with app.app_context():
            job = scheduler.get_job(event.job_id)
            if job:
                task = Task.query.filter_by(id=job.args[0]).first()
                ex_time = (
                    datetime.datetime.now(datetime.timezone.utc)
                    - event.scheduled_run_time
                )
                if task:
                    log = TaskLog(
                        task_id=task.id if task else event.job_id,
                        job_id=task.last_run_job_id or "",
                        status_id=6,
                        error=1,
                        message="Job error. Scheduled for: "
                        + datetime.datetime.strftime(
                            event.scheduled_run_time,
                            "%a, %b %-d, %Y %H:%M:%S",
                        )
                        + ". Execution time: "
                        + str(ex_time)
                        + " error: "
                        + str(event.exception)
                        + " trace: "
                        + str(event.traceback),
                    )
                    task.status_id = 2
                    db.session.add(log)
                    db.session.commit()

    def job_executed(event):
        with app.app_context():
            job = scheduler.get_job(event.job_id)
            if job:
                task = (
                    Task.query.filter_by(id=job.args[0]).first()
                    if job and len(job.args) > 0
                    else None
                )
                if task:
                    ex_time = (
                        datetime.datetime.now(datetime.timezone.utc)
                        - event.scheduled_run_time
                    )
                    log = TaskLog(
                        task_id=(task.id if task else None),
                        job_id=(task.last_run_job_id or "" if task else None),
                        status_id=6,
                        message="Job excecuted in " + str(ex_time) + ".",
                    )
                    db.session.add(log)
                    db.session.commit()

    def job_added(event):
        """Event is triggered when job is first created in scheduler not for repeat runs."""
        with app.app_context():
            job = scheduler.get_job(event.job_id)
            if job:
                task = Task.query.filter_by(
                    id=(job.args[0] if job.args else -1)
                ).first()
                task.next_run = None
                if task:
                    task.next_run = (
                        (
                            min(
                                task.next_run,
                                job.next_run_time,
                            )
                            if task.next_run is not None
                            else job.next_run_time
                        )
                        if job
                        else None
                    )
                    db.session.commit()

                    log = TaskLog(
                        task_id=task.id if task else event.job_id,
                        status_id=6,
                        error=(0 if job.next_run_time else 1),
                        message=(
                            "Job added. Scheduled for: "
                            + datetime.datetime.strftime(
                                job.next_run_time,
                                "%a, %b %-d, %Y %H:%M:%S",
                            )
                            if job.next_run_time
                            else "Job could not be scheduled. Verify project has a valid schedule."
                        ),
                    )
                    db.session.add(log)
                    db.session.commit()

    def job_removed(event):
        with app.app_context():
            task = Task.query.filter_by(
                id=(event.job_id.split("-")[1] if "-" in event.job_id else -1)
            ).first()

            if task:
                log = TaskLog(
                    task_id=task.id if task else event.job_id,
                    status_id=6,
                    message="Job removed.",
                )
                db.session.add(log)
                db.session.commit()

    def job_submitted(event):
        """Event is triggered when an already added job is run."""
        with app.app_context():
            job = scheduler.get_job(event.job_id)
            if job:
                task = (
                    Task.query.filter_by(id=job.args[0]).first()
                    if job and len(job.args) > 0
                    else None
                )
                if task:
                    task.next_run = None
                    task.next_run = (
                        (
                            min(
                                task.next_run,
                                job.next_run_time,
                            )
                            if task.next_run is not None
                            else job.next_run_time
                        )
                        if job
                        else None
                    )
                    db.session.add(task)
                    db.session.commit()

                    log = TaskLog(
                        task_id=task.id if task else event.job_id,
                        status_id=6,
                        message="Job submitted.",
                    )
                    db.session.add(log)
                    db.session.commit()

    scheduler.add_listener(job_missed, EVENT_JOB_MISSED)
    scheduler.add_listener(job_error, EVENT_JOB_ERROR)
    scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)
    scheduler.add_listener(job_added, EVENT_JOB_ADDED)
    scheduler.add_listener(job_removed, EVENT_JOB_REMOVED)
    scheduler.add_listener(job_submitted, EVENT_JOB_SUBMITTED)
