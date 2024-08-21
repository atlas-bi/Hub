"""Task web views."""

import requests
from flask import Blueprint
from flask import current_app as app
from flask import flash, jsonify, redirect, url_for
from flask_login import current_user, login_required
from RelativeToNow import relative_to_now
from werkzeug.wrappers import Response

from web import db, redis_client
from web.model import Task, TaskFile, TaskLog, TaskParam
from web.web import submit_executor

task_controls_bp = Blueprint("task_controls_bp", __name__)


@task_controls_bp.route("/task/<task_id>/run")
@login_required
def run_task(task_id: int) -> Response:
    """Run a task."""
    task = Task.query.filter_by(id=task_id).first()
    redis_client.delete("runner_" + str(task_id) + "_attempt")
    if task:
        # if the task is a sequence and enabled
        # then kick off all other tasks with same rank.
        if task.project.sequence_tasks == 1 and task.enabled == 1:
            tasks = db.session.execute(
                db.select(Task).filter_by(project_id=task.project_id, enabled=1, order=task.order)
            ).scalars()
            for tsk in tasks:
                try:
                    requests.get(app.config["SCHEDULER_HOST"] + "/run/" + str(tsk.id), timeout=60)
                    log = TaskLog(  # type: ignore[call-arg]
                        task_id=tsk.id,
                        status_id=7,
                        message=(current_user.full_name or "none") + ": Task manually run.",
                    )
                    db.session.add(log)
                    db.session.commit()
                    flash("Task run started.")
                # pylint: disable=broad-except
                except BaseException as e:
                    log = TaskLog(  # type: ignore[call-arg]
                        status_id=7,
                        error=1,
                        task_id=tsk.id,
                        message=(
                            (current_user.full_name or "none")
                            + ": Failed to manually run task. ("
                            + str(tsk.id)
                            + ")\n"
                            + str(e)
                        ),
                    )
                    db.session.add(log)
                    db.session.commit()
                    flash("Failed to run task.")
        else:
            try:
                requests.get(app.config["SCHEDULER_HOST"] + "/run/" + str(task_id), timeout=60)
                log = TaskLog(  # type: ignore[call-arg]
                    task_id=task.id,
                    status_id=7,
                    message=(current_user.full_name or "none") + ": Task manually run.",
                )
                db.session.add(log)
                db.session.commit()
                flash("Task run started.")
            # pylint: disable=broad-except
            except BaseException as e:
                log = TaskLog(  # type: ignore[call-arg]
                    status_id=7,
                    error=1,
                    task_id=task_id,
                    message=(
                        (current_user.full_name or "none")
                        + ": Failed to manually run task. ("
                        + str(task_id)
                        + ")\n"
                        + str(e)
                    ),
                )
                db.session.add(log)
                db.session.commit()
                flash("Failed to run task.")

        return redirect(url_for("task_bp.one_task", task_id=task_id))

    flash("Task does not exist.")
    return redirect(url_for("task_bp.all_tasks"))


@task_controls_bp.route("/task/<task_id>/schedule")
@login_required
def schedule_task(task_id: int) -> Response:
    """Add a task to scheduler."""
    submit_executor("enable_task", task_id)

    flash("Scheduling task.")

    return redirect(url_for("task_bp.one_task", task_id=task_id))


@task_controls_bp.route("/task/<task_id>/enable")
@login_required
def enable_task(task_id: int) -> str:
    """Enable a task."""
    submit_executor("enable_task", task_id)

    return "enabling task"


@task_controls_bp.route("/task/<task_id>/disable")
@login_required
def disable_task(task_id: int) -> str:
    """Disable a task."""
    submit_executor("disable_task", task_id)

    return "disabling task"


@task_controls_bp.route("/task/<task_id>/duplicate")
@login_required
def duplicate_task(task_id: int) -> Response:
    """Duplicate a task."""
    my_task = Task.query.filter_by(id=task_id).first()
    if my_task:
        new_task = Task()

        # pylint: disable=protected-access
        for key in my_task.__table__.columns.keys():
            if key not in ["id", "last_run", "last_run_job_id", "status_id"]:
                setattr(new_task, key, getattr(my_task, key))

        new_task.enabled = 0
        new_task.creator_id = current_user.id
        new_task.updater_id = current_user.id
        new_task.status_id = None
        new_task.name = str(my_task.name or "") + " - Duplicated"

        db.session.add(new_task)
        db.session.commit()

        # copy parameters
        for my_param in TaskParam.query.filter_by(task_id=task_id).all():
            if my_param:
                new_param = TaskParam()
                for key in my_param.__table__.columns.keys():
                    if key not in ["id", "task_id"]:
                        setattr(new_param, key, getattr(my_param, key))

                new_param.task_id = new_task.id
                db.session.add(new_param)
                db.session.commit()

        return redirect(url_for("task_edit_bp.task_edit_get", task_id=new_task.id))

    flash("Task does not exist.")
    return redirect(url_for("task_bp.all_tasks"))


@task_controls_bp.route("/task/<task_id>/hello")
@login_required
def task_status(task_id: int) -> Response:
    """Get basic task info."""
    task = Task.query.filter_by(id=task_id).first()

    if task:
        attempt = redis_client.zincrby("runner_" + str(task_id) + "_attempt", 0, "inc") or 0

        return jsonify(
            {
                "status": (
                    task.status.name
                    + (
                        " (attempt %d of %d)" % (attempt, task.max_retries)
                        if attempt > 0 and task.status.name == "Running"
                        else ""
                    )
                    if task.status
                    else ""
                ),
                "next_run": (
                    relative_to_now(task.next_run.astimezone())
                    if task.next_run  # and task.next_run > datetime.datetime.now()
                    else "N/A"
                ),
                "next_run_abs": (
                    " (%s)" % task.next_run.astimezone().strftime("%a, %b %-d, %Y %H:%M:%S")
                    if task.next_run  # and task.next_run > datetime.datetime.now()
                    else ""
                ),
                "last_run": (relative_to_now(task.last_run.astimezone()) if task.last_run else ""),
                "last_run_abs": (
                    " (%s)" % task.last_run.astimezone().strftime("%a, %b %-d, %Y %H:%M:%S")
                    if task.last_run
                    else ""
                ),
            }
        )

    return jsonify({})


@task_controls_bp.route("/task/<task_id>/delete")
@login_required
def delete_task(task_id: int) -> Response:
    """Delete a task."""
    task = Task.query.filter_by(id=task_id).first()

    if task:
        project_id = task.project_id

        submit_executor("disable_task", task_id)

        TaskLog.query.filter_by(task_id=task_id).delete()
        db.session.commit()
        TaskFile.query.filter_by(task_id=task_id).delete()
        db.session.commit()
        TaskParam.query.filter_by(task_id=task_id).delete()
        db.session.commit()
        Task.query.filter_by(id=task_id).delete()
        db.session.commit()

        log = TaskLog(  # type: ignore[call-arg]
            status_id=7,
            message=(current_user.full_name or "none") + ": Task deleted. (" + str(task_id) + ")",
        )
        db.session.add(log)
        db.session.commit()

        flash("Deleting task.")

        return redirect(url_for("project_bp.one_project", project_id=project_id))

    flash("Task does not exist.")
    return redirect(url_for("task_bp.all_tasks"))


@task_controls_bp.route("/task/<task_id>/endretry")
@login_required
def task_endretry(task_id: int) -> Response:
    """Stop a task from performing the scheduled retry.

    First, remove the redis key for reruns
    Then, force the task to reschedule, which will
    clear any scheduled jobs that do not belong to
    the primary schedule.
    """
    task = Task.query.filter_by(id=task_id).first()
    if task:
        if task.enabled == 1:
            submit_executor("enable_task", task_id)
        else:
            submit_executor("disable_task", task_id)

        log = TaskLog(  # type: ignore[call-arg]
            status_id=7,
            task_id=task_id,
            message="%s: Task retry canceled." % (current_user.full_name or "none"),
        )
        db.session.add(log)
        db.session.commit()

        return redirect(url_for("task_bp.one_task", task_id=task_id))

    flash("Task does not exist.")
    return redirect(url_for("task_bp.all_tasks"))


@task_controls_bp.route("/task/<task_id>/reset")
@login_required
def reset_task(task_id: int) -> Response:
    """Reset a task status to completed."""
    task = Task.query.filter_by(id=task_id).first()
    if task:
        task.status_id = 4
        db.session.commit()

        log = TaskLog(  # type: ignore[call-arg]
            task_id=task.id,
            status_id=7,
            message=(current_user.full_name or "none") + ": Reset task status to completed.",
        )
        db.session.add(log)
        db.session.commit()
        flash("Task has been reset to completed.")
        return redirect(url_for("task_bp.one_task", task_id=task_id))
    flash("Task does not exist.")
    return redirect(url_for("task_bp.all_tasks"))
