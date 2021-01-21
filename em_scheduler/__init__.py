"""
EM's scheduler module.

EM's scheduler is a Flask web API running Flask_APScheduler on a single
worker process.

The scheduler should be running on a single worker process and only accessable on localhost.

Tasks are started and stopped by sending a web request to various URL's.

* /add/<task_id>
* /delete/<task_id>
* /run/<task_id>


When the scheduler is ready to run a task it will send an async web request to the runner API
with the id of the task to run next.

Other Urls
**********

* /delete - delete all jobs
* /pause - pause all jobs
* /resume - resume all paused jobs
* /shutdown - gracefully shutdown the scheduler
* /kill - kill the scheduler
* /jobs - list all id's
* /details - list all job details
* /scheduled - list id's of scheduled jobs
* /delete-orphans - delete all orphaned jobs (jobs that no
  longer have an associated EM task existing)

Database Model
**************

Database model should be cloned from `em_web` before running app.

.. code-block:: console

    cp em_web/model.py em_scheduler/

"""

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

import hashlib
import logging
import time

from em_scheduler import config
from em_scheduler.extensions import db
from em_scheduler.model import Task
from flask import Flask, jsonify, make_response
from flask_apscheduler import APScheduler
from requests import get

from .scripts import event_log

app = Flask(__name__)

if app.config["DEBUG"] or app.config["ENV"] == "test" and not app.config["DEBUG"]:
    logging.info("loading dev config")
    app.config.from_object(config.DevConfig)
elif app.config["ENV"] == "test" and app.config["DEBUG"]:
    logging.info("loading test congif")
    app.config.from_object(config.TestConfig)
else:
    logging.info("loading prod config")
    app.config.from_object(config.Config)


db.init_app(app)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


logging.basicConfig(level=logging.WARNING)

if app.config["DEBUG"]:
    logging.getLogger("apscheduler").setLevel(logging.DEBUG)
else:
    logging.getLogger("apscheduler").setLevel(logging.ERROR)

event_log(app)


@app.errorhandler(404)
@app.errorhandler(500)
def error_message(error):
    """Return error page for 404 and 500 errors including the specific error message.

    :param error: error message
    :return: json web response with error message:

    .. code-block:: python

        {"error": "messsage"}

    """
    return make_response(jsonify({"error": str(error)}), 404)


@app.route("/api")
def alive():
    """Check API status.

    :url: /api/
    :returns: status alive!
    """
    return jsonify({"status": "alive"})


@app.route("/api/add/<task_id>")
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


@app.route("/api/delete/<task_id>")
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


@app.route("/api/run/<task_id>")
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


@app.route("/api/delete")
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


@app.route("/api/pause")
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


@app.route("/api/resume")
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


@app.route("/api/shutdown")
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


@app.route("/api/kill")
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


@app.route("/api/jobs")
def get_jobs():
    """Get list of all job ids.

    :url: /api/jobs
    :returns: list of job ids.
    """
    try:
        return jsonify([int(job.args[0]) for job in scheduler.get_jobs()])

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@app.route("/api/details")
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
            ]
        )

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@app.route("/api/scheduled")
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
                if job.next_run_time is not None
            ]
        )

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@app.route("/api/delete-orphans")
def delete_orphans():
    """Delete all orphaned jobs.

    :url: /api/delete-orphans
    :returns: json message
    """
    try:
        for job in scheduler.get_jobs():
            if Task.query.filter_by(id=int(job.args[0])).count() == 0:
                job.remove()

        return jsonify({"message": "Scheduler: orphans deleted!"})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": "Scheduler (delete orphans):\n" + str(e)})


def scheduler_delete_all_tasks():
    """Delete all jobs associated with a task from the scheduler.

    :returns: true
    """
    for job in scheduler.get_jobs():
        job.remove()

    return True


def scheduler_delete_task(task_id):
    """Delete all jobs associated with a task from the scheduler.

    :param task_id: id of task to delete associated jobs
    :returns: true
    """
    for job in scheduler.get_jobs():
        if str(job.args[0]) == str(task_id):
            job.remove()

    return True


def scheduler_task_runner(task_id):
    """Send request to runner api to run task.

    :param task_id: id of task to run
    """
    with app.app_context():
        try:
            get(app.config["RUNNER_HOST"] + "/" + task_id)
        # pylint: disable=broad-except
        except BaseException as e:
            print("failed to run job.")  # noqa: T001
            print(str(e))  # noqa: T001


def scheduler_add_task(task_id):
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
        my_hash.update(str(time.time()).encode("utf-8"))
        scheduler.add_job(
            func=scheduler_task_runner,
            trigger="cron",
            second=project.cron_sec,
            minute=project.cron_min,
            hour=project.cron_hour,
            year=project.cron_year,
            month=project.cron_month,
            week=project.cron_week,
            day=project.cron_day,
            day_of_week=project.cron_week_day,
            start_date=project.cron_start_date,
            end_date=project.cron_end_date,
            args=[
                str(task_id),
            ],
            id=str(project.id) + "-" + str(task.id) + "-" + my_hash.hexdigest()[:10],
            name="(cron) " + project.name + ": " + task.name,
        )

    # schedule interval
    task = Task.query.filter_by(id=task_id).first()
    if task.project.intv == 1:
        project = task.project
        my_hash.update(str(time.time()).encode("utf-8"))
        weeks = project.intv_value or 999 if project.intv_type == "w" else 0
        days = project.intv_value or 999 if project.intv_type == "d" else 0
        hours = project.intv_value or 999 if project.intv_type == "h" else 0
        minutes = project.intv_value or 999 if project.intv_type == "m" else 0
        seconds = project.intv_value or 999 if project.intv_type == "s" else 0

        scheduler.add_job(
            func=scheduler_task_runner,
            trigger="interval",
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            days=days,
            weeks=weeks,
            start_date=project.intv_start_date,
            end_date=project.intv_end_date,
            args=[
                str(task_id),
            ],
            id=str(project.id) + "-" + str(task.id) + "-" + my_hash.hexdigest()[:10],
            name="(inverval) " + project.name + ": " + task.name,
        )

    task = Task.query.filter_by(id=task_id).first()
    if task.project.ooff == 1:
        project = task.project
        my_hash.update(str(time.time()).encode("utf-8"))
        scheduler.add_job(
            func=scheduler_task_runner,
            trigger="date",
            run_date=project.ooff_date,
            args=[
                str(task_id),
            ],
            id=str(project.id) + "-" + str(task.id) + "-" + my_hash.hexdigest()[:10],
            name="(one off) " + project.name + ": " + task.name,
        )

    return True


if __name__ == "__main__":

    app.run(port=5001)
