"""Jobs to run through exectutor."""

import json
import logging
import sys
from asyncio import Future
from functools import partial
from pathlib import Path
from typing import Any, List

import requests
import urllib3
from flask import Blueprint
from flask import current_app as app
from flask import jsonify
from flask_login import current_user, login_required
from sqlalchemy import and_, or_
from werkzeug import Response

from web import db, executor, redis_client
from web.model import Project, Task, TaskLog

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from error_print import full_stack

executors_bp = Blueprint("executors_bp", __name__)


@executors_bp.route("/executor/status")
@login_required
def executor_status() -> Response:
    """Get list of active executor jobs."""
    active_executors = json.loads(
        redis_client.get(f"atlas_hub_executors-{current_user.id}") or json.dumps({})
    )

    redis_client.set(f"atlas_hub_executors-{current_user.id}", json.dumps({}))

    return jsonify(active_executors)


def submit_executor(name: str, *args: Any) -> None:
    """Task Executor.

    Redis is used to track current executors. When an executor is launched
    it is added to Redis["executors"].

    The webapp can query /executor/status to get a listing of running
    tasks.
    """
    # get list of active executors
    active_executors = json.loads(
        redis_client.get(f"atlas_hub_executors-{current_user.id}") or json.dumps({})
    )

    # remove duplicate job
    if name in active_executors or executor.futures.done(name) is not None:
        executor.futures.pop(name)

    # launch job
    possibles = globals().copy()
    possibles.update(locals())
    method = possibles.get(name)
    active_executors[name] = method.__doc__
    func = partial(executor_finished, name)

    future = executor.submit_stored(name, method, args)
    future.add_done_callback(func)

    # update active executor list
    redis_client.set(f"atlas_hub_executors-{current_user.id}", json.dumps(active_executors))


def executor_finished(name: str, future: Future) -> None:
    """Set status with default callback for executors."""
    active_executors = json.loads(
        redis_client.get(f"atlas_hub_executors-{current_user.id}") or json.dumps({})
    )
    active_executors[name + "-done"] = future.result()
    redis_client.set(f"atlas_hub_executors-{current_user.id}", json.dumps(active_executors))


def send_task_to_scheduler(task_id: int) -> None:
    """Silently send task or raise an error."""
    try:
        requests.get(app.config["SCHEDULER_HOST"] + "/add/" + str(task_id), timeout=60)
        log = TaskLog(
            task_id=task_id,
            status_id=7,
            message=(current_user.full_name or "none") + ": Task scheduled.",
        )
        db.session.add(log)
        db.session.commit()

    # pylint: disable=broad-except
    except (requests.exceptions.ConnectionError, urllib3.exceptions.NewConnectionError):
        # set task to disabled.
        Task.query.filter_by(id=task_id).first().enabled = 0
        db.session.commit()

        log = TaskLog(
            status_id=7,
            error=1,
            task_id=task_id,
            message=(
                (current_user.full_name or "none")
                + ": Failed to schedule task. ("
                + str(task_id)
                + ")\nScheduler is offline."
            ),
        )
        db.session.add(log)
        db.session.commit()
        # pylint: disable=W0707
        raise ValueError("Failed to schedule, scheduler is offline.")


def send_task_to_runner(task_id: int) -> None:
    """Silently send task or raise an error."""
    task = Task.query.filter_by(id=task_id).first()

    # task only runs if not sequence, or first in sequence.
    try:
        if task.project and task.project.sequence_tasks == 1:
            # only add job if its first in sequence
            if (
                Task.query.filter_by(project_id=task.project_id)
                .filter_by(enabled=1)
                .order_by(Task.order.asc(), Task.name.asc())  # type: ignore[union-attr]
                .first()
            ).id == int(task_id):
                requests.get(app.config["SCHEDULER_HOST"] + "/run/" + str(task.id), timeout=60)

                log = TaskLog(
                    task_id=task_id,
                    status_id=7,
                    message=(current_user.full_name or "none") + ": Task sent to runner.",
                )
                db.session.add(log)
                db.session.commit()

            else:
                log = TaskLog(
                    task_id=task_id,
                    status_id=7,
                    message=(current_user.full_name or "none")
                    + ": Task not sent to runner - it is a sequence task that should not run first.",
                )
                db.session.add(log)
                db.session.commit()
                raise ValueError("Task was not scheduled. It is not the first sequence task.")
        else:
            requests.get(app.config["SCHEDULER_HOST"] + "/run/" + str(task.id), timeout=60)

    except (requests.exceptions.ConnectionError, urllib3.exceptions.NewConnectionError):
        logging.error({"empty_msg": "Error - Scheduler offline."})
        log = TaskLog(
            task_id=task_id,
            status_id=7,
            error=1,
            message=(current_user.full_name or "none") + ": Failed to send task to runner.",
        )
        db.session.add(log)
        db.session.commit()
        # pylint: disable=W0707
        raise ValueError("Error - Scheduler offline.")


def sub_enable_task(task_id: int) -> None:
    """Shared function for enabling a task."""
    redis_client.delete("runner_" + str(task_id) + "_attempt")
    task = Task.query.filter_by(id=task_id).first()

    # task only goes to scheduler if not sequence, or first in sequence.
    if task.project and task.project.sequence_tasks == 1:
        # only add job if its first in sequence
        if Task.query.filter(
            or_(  # type: ignore[type-var]
                and_(Task.c.project_id == task.project_id, Task.c.enabled == 1),
                Task.c.id == task_id,
            )
        ).order_by(
            Task.order.asc(), Task.name.asc()  # type: ignore[union-attr]
        ).first() is not None and (
            Task.query.filter(
                or_(  # type: ignore[type-var]
                    and_(Task.c.project_id == task.project_id, Task.c.enabled == 1),
                    Task.c.id == task_id,
                )
            )
            .order_by(Task.order.asc(), Task.name.asc())  # type: ignore[union-attr]
            .first()
        ).id == int(
            task_id
        ):
            send_task_to_scheduler(task_id)
        else:
            # make sure it is not in the scheduler.
            requests.get(app.config["SCHEDULER_HOST"] + "/delete/" + str(task_id), timeout=60)
    else:
        send_task_to_scheduler(task_id)

    # show as enabled only if we made it to scheduler
    task.enabled = 1
    db.session.commit()

    log = TaskLog(
        task_id=task_id,
        status_id=7,
        message=(current_user.full_name or "none") + ": Task enabled.",
    )
    db.session.add(log)
    db.session.commit()


def enable_task(task_list: List[int]) -> str:
    """Enabling task."""
    task_id: int = task_list[0]

    # if task is part of a sequence then reschedule the full project.
    task = Task.query.filter_by(id=task_id).first()
    task.enabled = 1
    db.session.commit()

    if task.project and task.project.sequence_tasks == 1:
        # reschedule all tasks in project
        tasks = Task.query.filter(
            or_(  # type: ignore[type-var]
                and_(Task.c.project_id == task.project_id, Task.c.enabled == 1),
                Task.c.id == task_id,
            )
        )
        try:
            for task in tasks:
                sub_enable_task(task.id)
        # pylint: disable=W0703
        except BaseException as e:
            print(full_stack())  # noqa: T201
            return str(e)
        return "Task added, sequence updated."

    try:
        sub_enable_task(task_id)
        return "Task added."
    # pylint: disable=W0703
    except BaseException as e:
        return str(e)


def run_project(project_list: List[int]) -> str:
    """Running enabled project tasks."""
    project_id: int = project_list[0]
    project = Project.query.filter_by(id=project_id).first()

    tasks = Task.query.filter_by(project_id=project_id, enabled=1).order_by(
        Task.order.asc(), Task.name.asc()  # type: ignore[union-attr]
    )

    if project.sequence_tasks == 1:
        # run first enabled, order by rank, name
        send_task_to_runner(tasks.first().id)
        log = TaskLog(
            task_id=tasks.first().id,
            status_id=7,
            message=(current_user.full_name or "none") + ": Task manually run.",
        )
        db.session.add(log)
        db.session.commit()
        return "Project sequence run started."

    for task in tasks:
        send_task_to_runner(task.id)
        log = TaskLog(
            task_id=task.id,
            status_id=7,
            message=(current_user.full_name or "none") + ": Task manually run.",
        )
        db.session.add(log)
        db.session.commit()

    if len(tasks.all()):
        return "Run started."

    return "No enabled tasks to run."


def disable_project(project_list: List[int]) -> str:
    """Disabling project."""
    project_id = project_list[0]
    tasks = Task.query.filter_by(project_id=project_id).all()

    try:
        for task in tasks:
            sub_disable_task(task.id)

            log = TaskLog(
                task_id=task.id,
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
                + str(task.id)
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()
        return "Failed to disable project, see task logs."

    return "Project disabled."


def schedule_project(project_list: List[int]) -> str:
    """Scheduling project."""
    project_id = project_list[0]
    tasks = Task.query.filter_by(project_id=project_id, enabled=1).all()
    try:
        # first enable all, so we get sequence right
        for task in tasks:
            task.enabled = 1
            db.session.commit()

        for task in tasks:
            sub_enable_task(task.id)

    # pylint: disable=broad-except
    except BaseException as e:
        task.enabled = 0
        db.session.commit()
        log = TaskLog(
            status_id=7,
            error=1,
            message=((current_user.full_name or "none") + ": Failed to schedule task.\n" + str(e)),
        )
        db.session.add(log)
        db.session.commit()
        return "Failed to schedule project, see task logs."

    return "Project scheduled."


def enable_project(project_list: List[int]) -> str:
    """Enabling project."""
    project_id = project_list[0]
    tasks = Task.query.filter_by(project_id=project_id).all()

    try:
        # first enable all, so we get sequence right
        for task in tasks:
            task.enabled = 1
            db.session.commit()

        for task in tasks:
            sub_enable_task(task.id)

    # pylint: disable=broad-except
    except BaseException as e:
        task.enabled = 0
        db.session.commit()
        log = TaskLog(
            status_id=7,
            error=1,
            message=(
                (current_user.full_name or "none") + ": Failed to enable project.\n" + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()
        return "Failed to enable project, see task logs."

    return "Project enabled."


def sub_disable_task(task_id: int) -> None:
    """Shared function for disabling a task."""
    try:
        requests.get(app.config["SCHEDULER_HOST"] + "/delete/" + str(task_id), timeout=60)

        # also clear retry counter
        redis_client.delete(f"runner_{task_id}_attempt")

        task = Task.query.filter_by(id=task_id).first()
        task.enabled = 0
        task.next_run = None
        db.session.commit()
    except BaseException as e:
        db.session.rollback()
        raise e


def disable_task(task_list: List[int]) -> str:
    """Disabling task."""
    task_id: int = task_list[0]
    try:
        sub_disable_task(task_id)

        task = Task.query.filter_by(id=task_id).first()
        log = TaskLog(
            task_id=task_id,
            status_id=7,
            message=(current_user.full_name or "none") + ": Task disabled.",
        )
        db.session.add(log)
        db.session.commit()

        if task.project and task.project.sequence_tasks == 1:
            # update sequence
            for task in Task.query.filter_by(project_id=task.project_id, enabled=1).all():
                sub_enable_task(task.id)
            return "Task disabled, sequence updated."

        return "Task disabled."

    # pylint: disable=broad-except
    except BaseException as e:
        db.session.rollback()
        log = TaskLog(
            status_id=7,
            error=1,
            message=(
                (current_user.full_name or "none")
                + ": Failed to disable task. ("
                + str(task_id)
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()
        return "Failed to disable task."


# pylint: disable=W0613
def schedule_enabled_tasks(*args: Any) -> str:
    """Sending enabled tasks to scheduler."""
    try:
        for task in Task.query.filter_by(enabled=1).all():
            sub_enable_task(task.id)

        return "Tasks sent to scheduler."
    # pylint: disable=W0703
    except BaseException as e:
        return str(e)


# pylint: disable=W0613
def run_scheduled_tasks(*args: Any) -> None:
    """Running all scheduled tasks."""  # noqa: D401
    tasks = Task.query.filter(enabled=1).all()

    for task in tasks:
        send_task_to_runner(task.id)


# pylint: disable=W0613
def disabled_scheduled_tasks(*args: Any) -> str:
    """Disabling scheduled tasks."""
    # Basically dump the scheduler and set all tasks to disabled.

    try:
        requests.get(app.config["SCHEDULER_HOST"] + "/delete", timeout=60)

        tasks = Task.query.filter_by(enabled=1).all()

        for task in tasks:
            task.enabled = 0
            db.session.commit()

            log = TaskLog(
                task_id=task.id,
                status_id=7,
                message=(current_user.full_name or "none") + ": Task disabled.",
            )
            db.session.add(log)
            db.session.commit()
        return "Disabled scheduled tasks."
    except (requests.exceptions.ConnectionError, urllib3.exceptions.NewConnectionError):
        logging.error({"empty_msg": "Error - Scheduler offline."})

        return "Failed to disable, Scheduler is offline."


# pylint: disable=W0613
def run_errored_tasks(*args: Any) -> str:
    """Running all errored tasks."""  # noqa: D401
    tasks = Task.query.filter_by(status_id=2, enabled=1).all()

    try:
        for task in tasks:
            if task.project.cron == 1 or task.project.intv == 1:
                send_task_to_runner(task.id)
        return "Started running all errored tasks that have a schedule."
    except ValueError:
        return "Failed to run errored tasks, Scheduler is offline."


def refresh_cache(task_list: List[int]) -> str:
    """Refreshing task cache."""
    task_id: int = task_list[0]
    try:
        return requests.get(
            f"{app.config['RUNNER_HOST']}/task/{task_id}/refresh_cache", timeout=60
        ).text

    except BaseException:
        return "Failed to refresh cache."
