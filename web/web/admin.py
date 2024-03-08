"""Admin web views."""

import json
import platform
from pathlib import Path

import requests

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

from flask import Blueprint
from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug import Response

from web import db
from web.model import Task, TaskLog
from web.web import submit_executor

admin_bp = Blueprint("admin_bp", __name__)


@admin_bp.route("/admin/version")
@login_required
def version() -> str:
    """Check installed version."""
    installed_version = tomllib.loads(
        Path(Path.cwd() / "pyproject.toml").read_text(encoding="utf8")
    )["tool"]["poetry"]["version"]
    upgrade_version = None
    try:
        response = requests.get(
            "https://api.github.com/repos/atlas-bi/Hub/releases/latest", timeout=10
        )
        upgrade_version = response.json()["name"].replace("v", "")
    except:  # noqa: E722
        pass

    return render_template(
        "pages/version.html.j2",
        installed_version=installed_version,
        upgrade_version=upgrade_version,
    )


@admin_bp.route("/admin")
@login_required
def admin() -> str:
    """Admin home page."""
    message = request.args.get("message")
    if message:
        flash(message)
    return render_template("pages/admin.html.j2", title="Admin Area")


@admin_bp.route("/admin/reschedule_tasks")
@login_required
def reschedule_tasks() -> Response:
    """Emtpy scheduler and re-add all enabled jobs."""
    try:
        output = json.loads(
            requests.get(app.config["SCHEDULER_HOST"] + "/delete", timeout=60).text
        )

        msg = output["message"]
        add_user_log(msg, 0)

    except requests.exceptions.ConnectionError:
        msg = "Failed to remove jobs from scheduler. Scheduler offline."
        add_user_log(msg, 1)

    submit_executor("schedule_enabled_tasks")

    flash(msg)
    return redirect(url_for("admin_bp.admin"))


@admin_bp.route("/admin/reset_tasks")
@login_required
def reset_tasks() -> Response:
    """Reset all tasks to complete."""
    Task.query.update({Task.status_id: 4}, synchronize_session=False)
    db.session.commit()

    msg = "All task reset to 'completed' status."

    add_user_log(msg, 0)
    flash(msg)

    return redirect(url_for("admin_bp.admin"))


@admin_bp.route("/admin/pause_scheduler")
@login_required
def pause_scheduler() -> Response:
    """Stop all jobs from future runs."""
    try:
        output = json.loads(requests.get(app.config["SCHEDULER_HOST"] + "/pause", timeout=60).text)

        if output.get("error"):
            msg = output["error"]
            add_user_log(msg, 1)

        else:
            msg = output["message"]
            add_user_log(msg, 0)

    except requests.exceptions.ConnectionError:
        msg = "Failed to pause scheduler. Scheduler offline."
        add_user_log(msg, 1)

    flash(msg)

    return redirect(url_for("admin_bp.admin"))


@admin_bp.route("/admin/resume_scheduler")
@login_required
def resume_scheduler() -> Response:
    """Resume all paused jobs."""
    try:
        output = json.loads(
            requests.get(app.config["SCHEDULER_HOST"] + "/resume", timeout=60).text
        )

        if output.get("error"):
            msg = output["error"]
            add_user_log(msg, 1)

        else:
            msg = output["message"]
            add_user_log(msg, 0)

    except requests.exceptions.ConnectionError:
        msg = "Failed to resume scheduler. Scheduler offline."
        add_user_log(msg, 1)

    flash(msg)

    return redirect(url_for("admin_bp.admin"))


@admin_bp.route("/admin/kill_scheduler")
@login_required
def kill_scheduler() -> Response:
    """Kill the scheduler."""
    try:
        output = json.loads(requests.get(app.config["SCHEDULER_HOST"] + "/kill", timeout=60).text)

        msg = output["message"]
        add_user_log(msg, 0)

    except requests.exceptions.ConnectionError:
        msg = "Failed to kill scheduler. Scheduler offline."
        add_user_log(msg, 1)

    flash(msg)

    return redirect(url_for("admin_bp.admin"))


def add_user_log(message: str, error_code: int) -> None:
    """Add log entry prefixed by username.

    :param message str: message to save
    :param error_code: 1 (error) or 0 (no error)
    """
    log = TaskLog(
        status_id=7,
        error=error_code,
        message=(current_user.full_name or "none") + ": " + message,
    )  # type: ignore
    db.session.add(log)
    db.session.commit()
