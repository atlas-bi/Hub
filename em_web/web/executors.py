"""Jobs to run through exectutor."""
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


import json

import requests
from flask import Blueprint
from flask import current_app as app
from flask import jsonify
from flask_login import current_user, login_required
from sqlalchemy import and_, or_, text

from em_web import db, executor, redis_client
from em_web.model import Task, TaskLog

executors_bp = Blueprint("executors_bp", __name__)


@executors_bp.route("/executor/status")
@login_required
def executor_status():
    """Get list of active executor jobs.

    :url: /executor/status
    :returns: json list of active jobs.
    """
    # get list of executors and check status
    active_executors = json.loads(redis_client.get("executors") or json.dumps({}))

    # if status is completed, remove from list
    keys = list(active_executors.keys())
    for name in keys:
        if executor.futures.done(name) or executor.futures.done(name) is None:
            active_executors.pop(name)

    redis_client.set("executors", json.dumps(active_executors))

    return jsonify(active_executors)


def submit_executor(name, *args):
    """Task Executor.

    Redis is used to track current executors. When an executor is launched
    it is added to Redis["executors"].

    The webapp can query /executor/status to get a listing of running
    tasks.

    :param name: name of function to call
    """
    # get list of active executors
    active_executors = json.loads(redis_client.get("executors") or json.dumps({}))

    # remove duplicate job
    if name in active_executors or executor.futures.done(name) is not None:
        executor.futures.pop(name)

    # launch job
    possibles = globals().copy()
    possibles.update(locals())
    method = possibles.get(name)
    active_executors[name] = method.__doc__
    executor.submit_stored(name, method, args)

    # update active executor list
    redis_client.set("executors", json.dumps(active_executors))


def enable_task(task_id):
    """Enable task."""
    task_id = task_id[0]
    redis_client.delete("runner_" + str(task_id) + "_attempt")
    task = Task.query.filter_by(id=task_id).first()
    task.enabled = 1
    db.session.commit()

    log = TaskLog(
        task_id=task_id,
        status_id=7,
        message=(current_user.full_name or "none") + ": Task enabled.",
    )
    db.session.add(log)
    db.session.commit()

    try:
        requests.get(app.config["SCHEUDULER_HOST"] + "/add/" + str(task_id))
        log = TaskLog(
            task_id=task_id,
            status_id=7,
            message=(current_user.full_name or "none") + ": Task scheduled.",
        )
        db.session.add(log)
        db.session.commit()

    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            error=1,
            task_id=task_id,
            message=(
                (current_user.full_name or "none")
                + ": Failed to schedule task. ("
                + task_id
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()


def disable_task(task_id):
    """Disable task."""
    task_id = task_id[0]
    try:
        requests.get(app.config["SCHEUDULER_HOST"] + "/delete/" + str(task_id))

        task = Task.query.filter_by(id=task_id).first()
        task.enabled = 0
        task.next_run = None
        db.session.commit()

        log = TaskLog(
            task_id=task_id,
            status_id=7,
            message=(current_user.full_name or "none") + ": Task disabled.",
        )
        db.session.add(log)
        db.session.commit()

    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            error=1,
            message=(
                (current_user.full_name or "none")
                + ": Failed to disable task. ("
                + task_id
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()


# pylint: disable=W0613
def rescheduled_scheduled_tasks(*args):
    """Rescheduling scheduled tasks."""
    ids = json.loads(requests.get(app.config["SCHEUDULER_HOST"] + "/scheduled").text)

    tasks = Task.query.filter(Task.id.in_(ids)).filter_by(enabled=1).all()

    for task in tasks:
        requests.get(app.config["SCHEUDULER_HOST"] + "/add/" + str(task.id))


# pylint: disable=W0613
def run_scheduled_tasks(*args):
    """Running all scheduled tasks."""  # noqa: D401
    ids = json.loads(requests.get(app.config["SCHEUDULER_HOST"] + "/scheduled").text)

    tasks = Task.query.filter(Task.id.in_(ids)).filter_by(enabled=1).all()

    for task in tasks:
        requests.get(app.config["SCHEUDULER_HOST"] + "/run/" + str(task.id))


# pylint: disable=W0613
def disabled_scheduled_tasks(*args):
    """Disabling scheduled tasks."""
    ids = json.loads(requests.get(app.config["SCHEUDULER_HOST"] + "/scheduled").text)

    tasks = Task.query.filter(Task.id.in_(ids)).filter_by(enabled=1).all()

    for task in tasks:
        task.enabled = 0
        db.session.commit()

        requests.get(app.config["SCHEUDULER_HOST"] + "/delete/" + str(task.id))


# pylint: disable=W0613
def schedule_errored_tasks(*args):
    """Scheduling all errored tasks."""
    ids = json.loads(requests.get(app.config["SCHEUDULER_HOST"] + "/scheduled").text)

    tasks = (
        db.session.query()
        .select_from(Task)
        .filter(or_(Task.status_id == 2, and_(Task.id.notin_(ids), Task.enabled == 1)))
        .add_columns(text("task.id"))
        .all()
    )

    for task in tasks:
        requests.get(app.config["SCHEUDULER_HOST"] + "/add/" + str(task[0]))


# pylint: disable=W0613
def run_errored_tasks(*args):
    """Running all errored tasks."""  # noqa: D401
    ids = json.loads(requests.get(app.config["SCHEUDULER_HOST"] + "/scheduled").text)

    tasks = (
        db.session.query()
        .select_from(Task)
        .filter(or_(Task.status_id == 2, and_(Task.id.notin_(ids), Task.enabled == 1)))
        .add_columns(text("task.id"))
        .all()
    )

    for task in tasks:
        requests.get(app.config["SCHEUDULER_HOST"] + "/run/" + str(task[0]))


# pylint: disable=W0613
def run_active_tasks(*args):
    """Rerun all running tasks."""
    tasks = (
        db.session.query()
        .select_from(Task)
        .filter(or_(Task.status_id == 1, Task.enabled == 1))  # 1 = running
        .add_columns(text("task.id"))
        .all()
    )

    for task in tasks:
        requests.get(app.config["SCHEUDULER_HOST"] + "/run/" + str(task[0]))
