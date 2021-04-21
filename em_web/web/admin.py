"""Admin web views."""
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
import sys
from pathlib import Path

import requests
from flask import Blueprint
from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from em_web import db
from em_web.model import Task, TaskLog

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from error_print import full_stack

admin_bp = Blueprint("admin_bp", __name__)


@admin_bp.route("/admin")
@login_required
def admin():
    """Admin home page.

    :url: /admin
    :returns: html webpage.
    """
    message = request.args.get("message")
    if message:
        flash(message)
    return render_template("pages/admin.html.j2", title="Admin Area")


@admin_bp.route("/admin/emptyScheduler")
@login_required
def admin_empty_scheduler():
    """Remove all jobs from scheduler.

    :url: /admin/emptyScheduler
    :returns: redirects to admin homepage with message.
    """
    try:
        output = json.loads(
            requests.get(app.config["SCHEUDULER_HOST"] + "/delete").text
        )
        if output.get("error"):
            raise ValueError(output["error"])

        msg = output["message"]
        add_user_log(msg, 0)

    except ValueError as e:
        msg = str(e)
        add_user_log(msg, 1)

    except requests.exceptions.ConnectionError:
        msg = "Failed to remove jobs from scheduler. EM_Scheduler offline."
        add_user_log(msg, 1)

    flash(msg)
    return redirect(url_for("admin_bp.admin"))


@admin_bp.route("/admin/reloadJobs")
@login_required
def admin_reload_scheduler():
    """Emtpy scheduler and re-add all enabled jobs."""
    # pylint: disable=broad-except
    try:
        output = json.loads(
            requests.get(app.config["SCHEUDULER_HOST"] + "/delete").text
        )
        if output.get("error"):
            raise ValueError(output["error"])

        msg = output["message"]
        add_user_log(msg, 0)

    except ValueError as e:
        msg = str(e)
        add_user_log(msg, 1)

    except requests.exceptions.ConnectionError:
        msg = "Failed to remove jobs from scheduler. EM_Scheduler offline."
        add_user_log(msg, 1)

    tasks = Task.query.filter_by(enabled=1).all()

    try:
        for task in tasks:
            requests.get(app.config["SCHEUDULER_HOST"] + "/add/" + str(task.id))

        msg = msg + "\nEnabled tasks added to scheduler."
    except BaseException as e:
        msg = msg + "\nFailed to add enabled tasks to scheduler.\n" + str(e)

    flash(msg)
    return redirect(url_for("admin_bp.admin"))


@admin_bp.route("/admin/resetTasks")
@login_required
def admin_reset_tasks():
    """Reset all tasks to complete.

    :url: /admin/resetTasks
    :returns: redirects to admin homepage with message.
    """
    Task.query.update({Task.status_id: 4}, synchronize_session=False)
    db.session.commit()

    msg = "All task reset to 'completed' status."

    add_user_log(msg, 0)
    flash(msg)

    return redirect(url_for("admin_bp.admin"))


@admin_bp.route("/admin/whoami")
@login_required
def admin_whoami():
    """Run `whoami` command on server.

    .. code-block:: console

        /bin/whoami

    Calls runner function :obj:`em_runner.web.web.whoami`

    :url: /admin/whoami
    :returns: redirects to admin homepage with message.
    """
    try:
        output = json.loads(requests.get(app.config["RUNNER_HOST"] + "/whoami").text)
        if output.get("error"):
            raise ValueError(output["error"])

        msg = output["message"]
        add_user_log(msg, 0)

    except ValueError as e:
        msg = str(e)
        add_user_log(msg, 1)

    except requests.exceptions.ConnectionError:
        msg = "Whomai failed. EM_Runner offline."
        add_user_log(msg, 1)

    flash(msg)

    return redirect(url_for("admin_bp.admin"))


@admin_bp.route("/admin/reloadDaemon")
@login_required
def admin_reload_daemon():
    """Reload web service on server.

    .. code-block:: console

        /bin/sudo /bin/systemctl daemon-reload

    Calls runner function :obj:`em_runner.web.web.reload_daemon`

    :url: /admin/reloadDaemon

    :returns: redirects to admin homepage with message.
    """
    try:
        output = json.loads(
            requests.get(app.config["RUNNER_HOST"] + "/reloadDaemon").text
        )

        if output.get("error"):
            raise ValueError(output["error"])

        msg = output["message"]
        add_user_log(msg, 0)

    except ValueError as e:
        msg = str(e)
        add_user_log(msg, 1)

    except requests.exceptions.ConnectionError:
        msg = "Failed to reload web service. EM_Runner offline."
        add_user_log(msg, 1)

    flash(msg)

    return redirect(url_for("admin_bp.admin"))


@admin_bp.route("/admin/restartDaemon")
@login_required
def admin_restart_daemon():
    """Restart web service on server.

    .. code-block:: console

        /bin/sudo /bin/systemctl restart

     Calls runner function :obj:`em_runner.web.web.restart_daemon`

    :url: /admin/restartDaemon
    :returns: redirects to admin homepage with message.
    """
    try:
        output = json.loads(
            requests.get(app.config["RUNNER_HOST"] + "/restartDaemon").text
        )

        if output.get("error"):
            raise ValueError(output["error"])

        msg = output["message"]
        add_user_log(msg, 0)

    except ValueError as e:
        msg = str(e)
        add_user_log(msg, 1)

    except requests.exceptions.ConnectionError:
        msg = "Failed to restart web service. EM_Runner offline."
        add_user_log(msg, 1)

    flash(msg)

    return redirect(url_for("admin_bp.admin"))


@admin_bp.route("/admin/clearlog")
@login_required
def admin_clear_log():
    """Clear all logs.

    :url: /admin/clearlog
    :returns: redirects to admin homepage with message.
    """
    TaskLog.query.delete()
    db.session.commit()
    add_user_log("All logs deleted.", 0)

    return redirect(url_for("admin_bp.admin", message="Logs deleted!"))


@admin_bp.route("/admin/pauseJobs")
@login_required
def admin_pause_jobs():
    """Stop all jobs from future runs.

    :url: /admin/pauseJobs
    :returns: redirects to admin homepage with message.
    """
    # pylint: disable=broad-except
    try:
        output = json.loads(requests.get(app.config["SCHEUDULER_HOST"] + "/pause").text)
        if output.get("error"):
            raise ValueError(output["error"])

        msg = output["message"]
        add_user_log(msg, 0)

    except ValueError as e:
        msg = str(e)
        add_user_log(str(e), 1)

    except requests.exceptions.ConnectionError:
        msg = "Failed to pause scheduler. EM_Scheduler offline."
        add_user_log(msg, 1)

    except BaseException:
        msg = "Scheduler failed to pause.\n" + str(full_stack())
        add_user_log(msg, 1)

    flash(msg)

    return redirect(url_for("admin_bp.admin"))


@admin_bp.route("/admin/resumeJobs")
@login_required
def admin_resume_jobs():
    """Resume all paused jobs.

    :url: /admin/resumeJobs
    :returns: redirects to admin homepage with message.
    """
    # pylint: disable=broad-except
    try:
        output = json.loads(
            requests.get(app.config["SCHEUDULER_HOST"] + "/resume").text
        )
        if output.get("error"):
            raise ValueError(output["error"])

        msg = output["message"]
        add_user_log(msg, 0)

    except ValueError as e:
        msg = str(e)
        add_user_log(msg, 1)

    except requests.exceptions.ConnectionError:
        msg = "Failed to resume scheduler. EM_Scheduler offline."
        add_user_log(msg, 1)

    except BaseException:
        msg = "Scheduler failed to resume.\n" + str(full_stack())
        add_user_log(msg, 1)

    flash(msg)

    return redirect(url_for("admin_bp.admin"))


@admin_bp.route("/admin/stopJobs")
@login_required
def admin_stop_jobs():
    """Gracefully shutdown scheduler.

    :url: /admin/stopJobs
    :returns: redirects to admin homepage with message.
    """
    # pylint: disable=broad-except
    try:
        output = json.loads(
            requests.get(app.config["SCHEUDULER_HOST"] + "/shutdown").text
        )

        if output.get("error"):
            raise ValueError(output["error"])

        msg = output["message"]
        add_user_log(msg, 0)

    except ValueError as e:
        msg = str(e)
        add_user_log(msg, 1)

    except requests.exceptions.ConnectionError:
        msg = "Failed to stop scheduler. EM_Scheduler offline."
        add_user_log(msg, 1)

    except BaseException:
        msg = "Scheduler failed to gracefully shutdown.\n" + str(full_stack())
        add_user_log(msg, 1)

    flash(msg)

    return redirect(url_for("admin_bp.admin"))


@admin_bp.route("/admin/killJobs")
@login_required
def admin_kill_jobs():
    """Kill the scheduler.

    :url: /admin/killJobs
    :returns: redirects to admin homepage with message.
    """
    # pylint: disable=broad-except
    try:
        output = json.loads(requests.get(app.config["SCHEUDULER_HOST"] + "/kill").text)
        if output.get("error"):
            raise ValueError(output["error"])

        msg = output["message"]
        add_user_log(msg, 0)

    except ValueError as e:
        msg = str(e)
        add_user_log(msg, 1)

    except requests.exceptions.ConnectionError:
        msg = "Failed to kill scheduler. EM_Scheduler offline."
        add_user_log(msg, 1)

    except BaseException:
        msg = "Scheduler failed to kill.\n" + str(full_stack())
        add_user_log(msg, 1)

    flash(msg)

    return redirect(url_for("admin_bp.admin"))


def add_user_log(message, error_code):
    """Add log entry prefixed by username.

    :param message str: message to save
    :param error_code: 1 (error) or 0 (no error)
    """
    log = TaskLog(
        status_id=7,
        error=error_code,
        message=(current_user.full_name or "none") + ": " + message,
    )
    db.session.add(log)
    db.session.commit()
