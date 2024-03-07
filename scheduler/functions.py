"""Scheduler Event Logging."""

import hashlib
import time

from requests import get

from scheduler.extensions import atlas_scheduler, db
from scheduler.model import Task


def scheduler_delete_task(task_id: int) -> bool:
    """Delete all jobs associated with a task from the scheduler.

    :param task_id: id of task to delete associated jobs
    :returns: true
    """
    status = False
    for job in atlas_scheduler.get_jobs():
        if job.args and str(job.args[0]) == str(task_id):
            job.remove()
            status = True

    task = Task.query.filter_by(id=task_id).first()
    if task:
        task.next_run = None
        db.session.commit()

    return status


def scheduler_task_runner(task_id: int) -> None:
    """Send request to runner api to run task.

    :param task_id: id of task to run
    """
    try:
        with atlas_scheduler.app.app_context():
            # mark the task status as error in the
            # unlikely event that the runner is not
            # triggered.. then we will have the
            # job saved in an errored state.
            task = Task.query.filter_by(id=task_id).first()
            task.status_id = 2
            db.session.commit()

            get(atlas_scheduler.app.config["RUNNER_HOST"] + "/" + task_id, timeout=60)
    # pylint: disable=broad-except
    except BaseException as e:
        print("failed to run job.")  # noqa: T201
        print(str(e))  # noqa: T201
        raise e


def scheduler_add_task(task_id: int) -> bool:
    """Create job for task in the scheduler.

    :param task_id: id of task to create a schedule for

    *Parameters for APScheduler*

    :func: function to run
    :trigger: date, interval or cron
    :id: used to match job up to db
    :name: desc of job
    :misfire_grace_time: seconds a job can run late
    :coalesce: merge mul into one run
    :max_instances: max concurrent runs allowed
    :next_run_time: when to start schedule (None: job paused)
    :jobstore: alias of jobstore to use
    :executor: alias of excutor to use
    :replace_existing: true to replace jobs with same id

    *Parameters for Cron Jobs*

    :year: 4 digit year
    :month: 1-12
    :day: 1-31
    :week: 1-53
    :day_of_week: 0-6 or mon,tue,wed,thu,fri,sat,sun
    :hour: 0-23
    :minute: 0-59
    :second: 0-59
    :start_date: (datetime) soonest start
    :end_date: (datetime) latest run

    *Paramters for Interval Jobs*

    :weeks: (int) number of weeks between runs
    :days: (int) number of days between runs
    :hours: (int) number of hours between runs
    :minutes: (int) number of minutes between runs
    :seconds: (int) number of seconds between runs
    :start_date: (datetime) soonest start date
    :end_date: (datetime) latest run date

    *Parameters for One Off Jobs*

    :run_date: (datetime) when to run

    *Notes*

    If multiple triggers are specified on the task a schedule will be added for each trigger
    type. So it is possible to have multiple triggers per task. Because of this, the id
    assigned to the job is project_id-task_id-<time hash>. The tasks id is sent as an arg
    to the job.

    """
    task = Task.query.filter_by(id=task_id).first()

    # fyi, task must be re-queried after each type is
    # scheduled, as the scheduler events will modify
    # the task causing a session break!!
    if not task:
        return False

    task.enabled = 1
    db.session.commit()

    my_hash = hashlib.sha256()

    # schedule cron
    if task.project.cron == 1:
        project = task.project
        atlas_scheduler.add_job(
            func=scheduler_task_runner,
            trigger="cron",
            second=project.cron_sec if project.cron_sec else None,
            minute=project.cron_min if project.cron_min else None,
            hour=project.cron_hour if project.cron_hour else None,
            year=project.cron_year if project.cron_year else None,
            month=project.cron_month if project.cron_month else None,
            week=project.cron_week if project.cron_week else None,
            day=project.cron_day if project.cron_day else None,
            day_of_week=project.cron_week_day if project.cron_week_day else None,
            start_date=project.cron_start_date,
            end_date=project.cron_end_date,
            args=[str(task_id)],
            id=str(project.id) + "-" + str(task.id) + "-cron",
            name="(cron) " + project.name + ": " + task.name,
            replace_existing=True,
        )

    # schedule interval
    task = Task.query.filter_by(id=task_id).first()
    if task.project.intv == 1:
        project = task.project
        weeks = project.intv_value or 999 if project.intv_type == "w" else 0
        days = project.intv_value or 999 if project.intv_type == "d" else 0
        hours = project.intv_value or 999 if project.intv_type == "h" else 0
        minutes = project.intv_value or 999 if project.intv_type == "m" else 0
        seconds = project.intv_value or 999 if project.intv_type == "s" else 0

        atlas_scheduler.add_job(
            func=scheduler_task_runner,
            trigger="interval",
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            days=days,
            weeks=weeks,
            start_date=project.intv_start_date,
            end_date=project.intv_end_date,
            args=[str(task_id)],
            id=str(project.id) + "-" + str(task.id) + "-intv",
            name="(inverval) " + project.name + ": " + task.name,
            replace_existing=True,
        )

    # ooff tasks use a hash to identify jobs as a job can have multiple one-off runs scheduled.
    task = Task.query.filter_by(id=task_id).first()
    if task.project.ooff == 1:
        project = task.project
        my_hash.update(str(time.time()).encode("utf-8"))
        atlas_scheduler.add_job(
            func=scheduler_task_runner,
            trigger="date",
            run_date=project.ooff_date,
            args=[str(task_id)],
            id=str(project.id) + "-" + str(task.id) + "-" + my_hash.hexdigest()[:10],
            name="(one off) " + project.name + ": " + task.name,
            replace_existing=True,
        )

    return True
