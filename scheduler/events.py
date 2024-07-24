"""Log scheduler events.

Scheduler events have a listener added to trigger a logging function.
The event details are logged to ``Model.TaskLog``.

These logs will only be from scheduler events (starting/stoping/etc)
and not from the actual details of the run. Run detail are added to
the logs by ``runner``.

Events saved to :obj:`scheduler.model.TaskLog`:

* EVENT_JOB_ADDED
* EVENT_JOB_ERROR
* EVENT_JOB_EXECUTED
* EVENT_JOB_MISSED
* EVENT_JOB_REMOVED
* EVENT_JOB_SUBMITTED

Events not saved to :obj:`scheduler.model.TaskLog`:

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
import re

from apscheduler.events import JobEvent, JobExecutionEvent, JobSubmissionEvent
from dateutil.tz import tzlocal

from scheduler.extensions import atlas_scheduler, db
from scheduler.model import Task, TaskLog


def job_missed(event: JobEvent) -> None:
    """Capture missed job events.

    Once a job is missed it is potentially no longer tracked
    so any pertinent info must be scrapped from the event.

    job_id follows the pattern proj_id-task-id-stuff
    """
    with atlas_scheduler.app.app_context():
        if re.match(r"^\d+-\d+-.+?$", event.job_id):
            _, task_id = event.job_id.split("-")[:2]

            ex_time = datetime.datetime.now(datetime.timezone.utc) - event.scheduled_run_time

            if Task.query.filter_by(id=task_id).first():
                log = TaskLog(
                    task_id=task_id,
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


def job_error(event: JobEvent) -> None:
    """Capture execution errors."""
    with atlas_scheduler.app.app_context():
        if re.match(r"^\d+-\d+-.+?$", event.job_id):
            _, task_id = event.job_id.split("-")[:2]

            task = Task.query.filter_by(id=task_id).first()

            # only add logs for valid tasks
            if task:
                ex_time = datetime.datetime.now(datetime.timezone.utc) - event.scheduled_run_time

                log = TaskLog(
                    task_id=task_id,
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


def job_executed(event: JobExecutionEvent) -> None:
    """Event triggered when a job has been executed by scheduler."""
    with atlas_scheduler.app.app_context():
        if re.match(r"^\d+-\d+-.+?$", event.job_id):
            _, task_id = event.job_id.split("-")[:2]

            task = Task.query.filter_by(id=task_id).first()

            # only log valid tasks
            if task:
                ex_time = datetime.datetime.now(datetime.timezone.utc) - event.scheduled_run_time

                log = TaskLog(
                    task_id=task_id,
                    job_id=(str(task.last_run_job_id or "") if task else None),
                    status_id=6,
                    message="Job excecuted in " + str(ex_time) + ".",
                )
                db.session.add(log)
                db.session.commit()


def job_added(event: JobEvent) -> None:
    """Event is triggered when job is first created in scheduler not for repeat runs."""
    with atlas_scheduler.app.app_context():
        job = atlas_scheduler.get_job(event.job_id)

        # job and task just exist still
        if re.match(r"^\d+-\d+-.+?$", event.job_id) and job:
            _, task_id = event.job_id.split("-")[:2]

            task = Task.query.filter_by(id=task_id).first()

            if task:
                if task.next_run and task.next_run.replace(
                    tzinfo=tzlocal()
                ) < datetime.datetime.now().replace(tzinfo=tzlocal()):
                    task.next_run = None

                task.next_run = (
                    min(
                        task.next_run.replace(tzinfo=tzlocal()),
                        job.next_run_time.replace(tzinfo=tzlocal()),
                    )
                    if task.next_run is not None
                    else job.next_run_time.replace(tzinfo=tzlocal())
                )

                db.session.commit()

                log = TaskLog(
                    task_id=task_id,
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


def job_removed(event: JobEvent) -> None:
    """Event triggered when a job is removed."""
    with atlas_scheduler.app.app_context():
        if re.match(r"^\d+-\d+-.+?$", event.job_id):
            _, task_id = event.job_id.split("-")[:2]

            task = Task.query.filter_by(id=task_id).first()

            if task:
                log = TaskLog(
                    task_id=task_id,
                    status_id=6,
                    message="Job removed.",
                )
                db.session.add(log)
                db.session.commit()


def job_submitted(event: JobSubmissionEvent) -> None:
    """Event is triggered when an already added job is run."""
    with atlas_scheduler.app.app_context():
        if re.match(r"^\d+-\d+-.+?$", event.job_id):
            _, task_id = event.job_id.split("-")[:2]

            task = Task.query.filter_by(id=task_id).first()

            if task:
                # if job still exists (not one off..)
                job = atlas_scheduler.get_job(event.job_id)

                if task.next_run and task.next_run.replace(
                    tzinfo=tzlocal()
                ) < datetime.datetime.now().replace(tzinfo=tzlocal()):
                    task.next_run = None

                if job:
                    task.next_run = (
                        (
                            min(
                                task.next_run.replace(tzinfo=tzlocal()),
                                job.next_run_time.replace(tzinfo=tzlocal()),
                            )
                            if task.next_run is not None
                            else job.next_run_time.replace(tzinfo=tzlocal())
                        )
                        if job
                        else None
                    )
                else:
                    task.next_run = None

                db.session.add(task)
                db.session.commit()

                log = TaskLog(
                    task_id=task_id,
                    status_id=6,
                    message="Job submitted.",
                )
                db.session.add(log)
                db.session.commit()
