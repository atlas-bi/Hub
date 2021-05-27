"""Scheduler Web API."""
# Extract Management 2.0
# Copyright (C) 2020  Riverside Healthcare, Kankakee, IL

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import datetime
import hashlib
import time
from itertools import groupby

from flask import Blueprint, jsonify

from em_scheduler.extensions import scheduler
from em_scheduler.functions import (
    scheduler_add_task,
    scheduler_delete_all_tasks,
    scheduler_delete_task,
    scheduler_task_runner,
)
from em_scheduler.model import Task

web_bp = Blueprint("web_bp", __name__)


@web_bp.route("/api")
def alive():
    """Check API status.

    :url: /api/
    :returns: status alive!
    """
    return jsonify({"status": "alive"})


@web_bp.route("/api/schedule")
def schedule():
    """Build simulated run schedule.

    Build list of hours to show on the chart:
    ['now', <now + 1>, <now + 2>, etc]

    Build list of schedule for next 24 hours

    Merge two lists and put 0 where needed.

    :url: /api/
    :returns: status alive!
    """
    now = datetime.datetime.now(
        datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    )
    tomorrow = now + datetime.timedelta(hours=24)

    hour_list = ["now"]

    now_int = now

    while now_int < tomorrow:
        now_int = now_int + datetime.timedelta(hours=1)
        hour_list.append(datetime.datetime.strftime(now_int, "%-H:00"))

    active_schedule = []

    for job in scheduler.get_jobs():

        if (
            job.id == "job_sync"
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

            if not job_date.tzinfo:
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
                "count": (sum(1 for x in groups.get(hour)) if groups.get(hour) else 0),
            }
        )

    return jsonify(active_schedule)


@web_bp.route("/api/add/<task_id>")
def add_task(task_id):
    """Schedule task to run.

    :url: /api/add/<task_id>
    :param int task_id: id of task to schedule
    :returns: json message

    First check for any existing schedules, remove them, then add a new schedule.
    """
    try:
        scheduler_delete_task(task_id)
        if scheduler_add_task(task_id):
            return jsonify({"message": "Scheduler: task job added!"})
        return jsonify({"message": "Scheduler: failed to create job!"})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": "Scheduler (add job):\n" + str(e)})


@web_bp.route("/api/delete/<task_id>")
def delete_task(task_id):
    """Delete tasks schedule.

    :url: /api/delete/<task_id>
    :param task_id: id of task to delete
    :returns: json message
    """
    try:
        if scheduler_delete_task(task_id):
            return jsonify({"message": "Scheduler: task job deleted!"})
        return jsonify({"message": "Scheduler: failed to delete job!"})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": "Scheduler (delete task jobs):\n" + str(e)})


@web_bp.route("/api/run/<task_id>")
def run_task(task_id):
    """Run task now.

    :url: /api/run/<task_id>
    :param task_id: id of task to run
    :returns: json message
    """
    try:
        scheduler_task_runner(task_id)
        return jsonify({"message": "Scheduler: task job started!"})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": "Scheduler (run task):\n" + str(e)})


@web_bp.route("/api/run/<task_id>/delay/<minutes>")
def run_task_delay(task_id, minutes):
    """Run task in x minutes.

    :url: /api/run/<task_id>/delay/<minutes>
    :param task_id: id of task to run
    :param minutes: minutes from now to run task
    :returns: json message
    """
    try:
        task = Task.query.filter_by(id=task_id).first()
        project = task.project

        my_hash = hashlib.sha256()
        my_hash.update(str(time.time()).encode("utf-8"))

        scheduler.add_job(
            func=scheduler_task_runner,
            trigger="date",
            run_date=datetime.datetime.now() + datetime.timedelta(minutes=int(minutes)),
            args=[str(task_id)],
            id=str(project.id) + "-" + str(task.id) + "-" + my_hash.hexdigest()[:10],
            name="(one off delay) " + project.name + ": " + task.name,
        )

        return jsonify({"message": "Scheduler: task scheduled!"})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": "Scheduler (run task with delay):\n" + str(e)})


@web_bp.route("/api/delete")
def delete_all_tasks():
    """Delete all scheduled tasks.

    :url: /api/delete
    :returns: json message
    """
    try:
        if scheduler_delete_all_tasks():
            return jsonify({"message": "Scheduler: all jobs deleted!"})
        return jsonify({"message": "Scheduler: failed to delete jobs!"})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": "Scheduler (delete all tasks):\n" + str(e)})


@web_bp.route("/api/pause")
def pause_all_tasks():
    """Pause all tasks.

    :url: /api/pause
    :returns: json message
    """
    try:
        scheduler.pause()

        return jsonify({"message": "Scheduler: all jobs paused!"})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": "Scheduler (pause all jobs):\n" + str(e)})


@web_bp.route("/api/resume")
def resume_all_tasks():
    """Resume all tasks.

    :url: /api/resume
    :returns: succss message.
    """
    try:
        scheduler.resume()

        return jsonify({"message": "Scheduler: all jobs resumed!"})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": "Scheduler (resume jobs):\n" + str(e)})


@web_bp.route("/api/shutdown")
def shutdown():
    """Gracefully shutdown scheduler.

    :url: /api/shutdown
    :returns: succss message.
    """
    try:
        scheduler.shutdown()

        return jsonify({"message": "Scheduler: scheduler shutdown!"})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": "Scheduler (shutdown):\n" + str(e)})


@web_bp.route("/api/kill")
def kill():
    """Kill scheduler.

    :url: /api/kill
    :returns: succss message.
    """
    try:
        scheduler.shutdown(wait=False)
        return jsonify({"message": "Scheduler: scheduler killed!"})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": "Scheduler (kill):\n" + str(e)})


@web_bp.route("/api/jobs")
def get_jobs():
    """Get list of all job ids.

    :url: /api/jobs
    :returns: list of job ids.
    """
    try:
        return jsonify([int(job.args[0]) for job in scheduler.get_jobs() if job.args])

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/api/details")
def get_jobs_details():
    """Get list of all jobs with all details.

    :url: /api/details
    :returns: list of job ids.
    """
    try:
        return jsonify(
            [
                {
                    "name": job.name,
                    "job_id": job.id,
                    "next_run_time": job.next_run_time,
                    "id": job.args[0],
                }
                for job in scheduler.get_jobs()
                if job.args
            ]
        )

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/api/scheduled")
def get_scheduled_jobs():
    """Get list of all scheduled job ids.

    :url: /api/scheduled
    :returns: json list of ids for active jobs
    """
    try:
        return jsonify(
            [
                int(job.args[0])
                for job in scheduler.get_jobs()
                if job.next_run_time is not None and job.args
            ]
        )

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/api/delete-orphans")
def delete_orphans():
    """Delete all orphaned jobs.

    :url: /api/delete-orphans
    :returns: json message
    """
    try:
        for job in scheduler.get_jobs():
            if job.args and Task.query.filter_by(id=int(job.args[0])).count() == 0:
                job.remove()

        return jsonify({"message": "Scheduler: orphans deleted!"})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": "Scheduler (delete orphans):\n" + str(e)})
