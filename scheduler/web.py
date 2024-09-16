"""Scheduler Web API."""

import datetime
import hashlib
import re
import time
from itertools import groupby

from flask import Blueprint, jsonify
from werkzeug import Response

from scheduler.extensions import atlas_scheduler
from scheduler.functions import (
    scheduler_add_task,
    scheduler_delete_task,
    scheduler_task_runner,
)
from scheduler.model import Task

web_bp = Blueprint("web_bp", __name__)


@web_bp.route("/api")
def alive() -> Response:
    """Check API status."""
    return jsonify({"status": "alive"})


@web_bp.route("/api/schedule")
def schedule() -> Response:
    """Build simulated run schedule.

    Build list of hours to show on the chart:
    ['now', <now + 1>, <now + 2>, etc]

    Build list of schedule for next 24 hours

    Merge two lists and put 0 where needed.
    """
    now = datetime.datetime.now(datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo)
    tomorrow = now + datetime.timedelta(hours=24)

    hour_list = ["now"]

    now_int = now

    while now_int < tomorrow:
        now_int = now_int + datetime.timedelta(hours=1)
        hour_list.append(datetime.datetime.strftime(now_int, "%-H:00"))

    active_schedule = []

    for job in atlas_scheduler.get_jobs():
        if (
            job.id in ["job_sync", "temp_clean"]
            or not hasattr(job, "next_run_time")
            or job.next_run_time is None
            and job.args
        ):
            continue

        job_date = job.next_run_time

        while job_date and job_date < tomorrow:
            if now.replace(minute=0, second=0, microsecond=0) == job_date.replace(
                minute=0, second=0, microsecond=0
            ):
                message = "now"

            else:
                message = datetime.datetime.strftime(job_date, "%-H:00")

            active_schedule.append({"message": message, "date": job_date})

            if not job_date.tzinfo:  # pragma: no cover
                job_date.astimezone()

            job_date = job.trigger.get_next_fire_time(job_date, job_date)

    active_schedule.sort(key=lambda active_schedule: active_schedule["date"])
    groups = {
        key: list(group)
        for key, group in groupby(
            active_schedule, lambda active_schedule: active_schedule["message"]
        )
    }
    active_schedule = []

    for hour in hour_list:
        active_schedule.append(
            {
                "case": hour,
                "count": (sum(1 for x in groups.get(hour)) if groups.get(hour) else 0),  # type: ignore[union-attr,misc]
            }
        )

    return jsonify(active_schedule)


@web_bp.route("/api/add/<task_id>")
def add_task(task_id: int) -> Response:
    """Schedule task to run.

    First check for any existing schedules, remove them, then add a new schedule.
    """
    try:
        assert Task.query.filter_by(id=task_id).first()

    # pylint: disable=broad-except
    except BaseException as e:
        print(str(e))  # noqa: T201
        return jsonify({"error": "Invalid job."})
    try:
        scheduler_delete_task(task_id)

        # all sequence logic is done on the web/executors.py level.
        if scheduler_add_task(task_id):
            return jsonify({"message": "Scheduler: task job added!"})
        return jsonify({"message": "Scheduler: failed to create job!"})

    # pylint: disable=broad-except
    except BaseException as e:
        print(str(e))  # noqa: T201
        return jsonify({"error": "Scheduler (add job):\n" + str(e)})


@web_bp.route("/api/delete/<task_id>")
def delete_task(task_id: int) -> Response:
    """Delete tasks schedule."""
    try:
        assert Task.query.filter_by(id=task_id).first()

    # pylint: disable=broad-except
    except BaseException as e:
        print(str(e))  # noqa: T201
        return jsonify({"error": "Invalid job."})

    if scheduler_delete_task(task_id):
        return jsonify({"message": "Scheduler: task job deleted!"})
    return jsonify({"message": "Scheduler: failed to delete job!"})


@web_bp.route("/api/run/<task_id>")
def run_task(task_id: int) -> Response:
    """Run task now."""
    try:
        scheduler_task_runner(task_id)
        return jsonify({"message": "Scheduler: task job started!"})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": "Scheduler (run task):\n" + str(e)})


@web_bp.route("/api/run/<task_id>/delay/<minutes>")
def run_task_delay(task_id: int, minutes: str) -> Response:
    """Run task in x minutes."""
    task = Task.query.filter_by(id=task_id).first()
    project = task.project

    my_hash = hashlib.sha256()
    my_hash.update(str(time.time()).encode("utf-8"))

    atlas_scheduler.add_job(
        func=scheduler_task_runner,
        trigger="date",
        run_date=datetime.datetime.now() + datetime.timedelta(minutes=int(minutes)),
        args=[str(task_id)],
        id=str(project.id) + "-" + str(task.id) + "-" + my_hash.hexdigest()[:10],
        name="(one off delay) " + project.name + ": " + task.name,
    )

    return jsonify({"message": "Scheduler: task scheduled!"})


@web_bp.route("/api/delete")
def delete_all_tasks() -> Response:
    """Delete all scheduled tasks."""
    for job in atlas_scheduler.get_jobs():
        if re.match(r"^\d+-\d+-.+?$", job.id):
            job.remove()

    return jsonify({"message": "Scheduler: all jobs deleted!"})


@web_bp.route("/api/pause")
def pause_all_tasks() -> Response:
    """Pause all tasks."""
    if atlas_scheduler.running:
        atlas_scheduler.pause()

        return jsonify({"message": "Scheduler: all jobs paused!"})

    return jsonify({"error": "Scheduler: scheduler not running, restart service!"})


@web_bp.route("/api/resume")
def resume_all_tasks() -> Response:
    """Resume all tasks."""
    # pylint: disable=R1705
    if atlas_scheduler.state == 2 and atlas_scheduler.running:
        atlas_scheduler.resume()

        return jsonify({"message": "Scheduler: all jobs resumed!"})

    elif atlas_scheduler.state == 1:
        return jsonify({"message": "Scheduler: all jobs resumed!"})

    return jsonify({"error": "Scheduler: scheduler not running, restart service!"})


@web_bp.route("/api/kill")
def kill() -> Response:
    """Kill scheduler."""
    atlas_scheduler.shutdown(wait=False)
    return jsonify({"message": "Scheduler: scheduler killed!"})


@web_bp.route("/api/jobs")
def get_jobs() -> Response:
    """Get list of all job ids."""
    return jsonify(
        [
            int(job.id.split("-")[1])
            for job in atlas_scheduler.get_jobs()
            if re.match(r"^\d+-\d+-.+?$", job.id)
        ]
    )


@web_bp.route("/api/details")
def get_jobs_details() -> Response:
    """Get list of all jobs with all details."""
    return jsonify(
        [
            {
                "name": job.name,
                "job_id": job.id,
                "next_run_time": job.next_run_time,
                "id": job.id.split("-")[1],
            }
            for job in atlas_scheduler.get_jobs()
            if re.match(r"^\d+-\d+-.+?$", job.id)
        ]
    )


@web_bp.route("/api/scheduled")
def get_scheduled_jobs() -> Response:
    """Get list of all scheduled job ids."""
    return jsonify(
        [
            int(job.id.split("-")[1])
            for job in atlas_scheduler.get_jobs()
            if job.next_run_time is not None and re.match(r"^\d+-\d+-.+?$", job.id)
        ]
    )


@web_bp.route("/api/delete-orphans")
def delete_orphans() -> Response:
    """Delete all orphaned jobs."""
    for job in atlas_scheduler.get_jobs():
        if job.args and Task.query.filter_by(id=int(job.args[0])).count() == 0:
            job.remove()

    return jsonify({"message": "Scheduler: orphans deleted!"})
