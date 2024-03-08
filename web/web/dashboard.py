"""Dashboard web views."""

import json
import logging
from typing import Union

import requests
from flask import Blueprint
from flask import current_app as app
from flask import flash, jsonify, redirect, render_template, url_for
from flask_login import current_user, login_required
from werkzeug.wrappers import Response

from web import db
from web.model import (
    Connection,
    ConnectionDatabase,
    ConnectionFtp,
    ConnectionGpg,
    ConnectionSftp,
    ConnectionSmb,
    ConnectionSsh,
    Project,
    Task,
    TaskLog,
    User,
)
from web.web import submit_executor

dashboard_bp = Blueprint("dashboard_bp", __name__)


@dashboard_bp.route("/search")
@login_required
def search() -> dict:
    """Search data."""
    my_json = {}

    tasks = db.session.query(Task.id, Task.name).order_by(Task.name).all()
    task_json = {}
    for t_id, t_name in tasks:
        task_json[url_for("task_bp.one_task", task_id=t_id)] = t_name

    project_json = {}
    projects = db.session.query(Project.id, Project.name).order_by(Project.name).all()
    for t_id, t_name in projects:
        project_json[url_for("project_bp.one_project", project_id=t_id)] = t_name

    user_json = {}
    users = db.session.query(User.id, User.full_name).order_by(User.full_name).all()
    for t_id, t_name in users:
        user_json[url_for("project_bp.user_projects", user_id=t_id)] = t_name

    connection_json = {}
    connections = (
        db.session.query(
            Connection.id,
            Connection.name,
            Connection.description,
            Connection.address,
            Connection.primary_contact,
            Connection.primary_contact_email,
            Connection.primary_contact_phone,
        )
        .order_by(Connection.name)
        .all()
    )
    for row in connections:
        connection_json[url_for("connection_bp.one_connection", connection_id=row[0])] = (
            " / ".join([x for x in row[1:] if x.strip()])
        )

    connection_sftp = {}
    sftp_connections = db.session.query(
        ConnectionSftp.connection_id,
        ConnectionSftp.id,
        ConnectionSftp.name,
        ConnectionSftp.address,
    )
    for row in sftp_connections.all():
        connection_sftp[
            url_for("connection_bp.one_connection", connection_id=row[0]) + f"?s={row[1]}"
        ] = " / ".join([x for x in row[2:] if x.strip()])
    connection_ftp = {}
    ftp_connections = db.session.query(
        ConnectionFtp.connection_id,
        ConnectionFtp.id,
        ConnectionFtp.name,
        ConnectionFtp.address,
    )
    for row in ftp_connections.all():
        connection_ftp[
            url_for("connection_bp.one_connection", connection_id=row[0]) + f"?s={row[1]}"
        ] = " / ".join([x for x in row[2:] if x.strip()])
    connection_database = {}
    database_connections = db.session.query(
        ConnectionDatabase.connection_id, ConnectionDatabase.id, ConnectionDatabase.name
    )
    for row in database_connections.all():
        connection_database[
            url_for("connection_bp.one_connection", connection_id=row[0]) + f"?s={row[1]}"
        ] = " / ".join([x for x in row[2:] if x.strip()])
    connection_smb = {}
    smb_connections = db.session.query(
        ConnectionSmb.connection_id,
        ConnectionSmb.id,
        ConnectionSmb.name,
        ConnectionSmb.server_name,
        ConnectionSmb.server_ip,
        ConnectionSmb.share_name,
    )
    for row in smb_connections.all():
        connection_smb[
            url_for("connection_bp.one_connection", connection_id=row[0]) + f"?s={row[1]}"
        ] = " / ".join([x for x in row[2:] if x.strip()])
    connection_ssh = {}
    ssh_connections = db.session.query(
        ConnectionSsh.connection_id,
        ConnectionSsh.id,
        ConnectionSsh.name,
        ConnectionSsh.address,
    )
    for row in ssh_connections.all():
        connection_ssh[
            url_for("connection_bp.one_connection", connection_id=row[0]) + f"?s={row[1]}"
        ] = " / ".join([x for x in row[2:] if x.strip()])
    connection_gpg = {}
    gpg_connections = db.session.query(
        ConnectionGpg.connection_id, ConnectionGpg.id, ConnectionGpg.name
    )
    for row in gpg_connections.all():
        connection_gpg[
            url_for("connection_bp.one_connection", connection_id=row[0]) + f"?s={row[1]}"
        ] = " / ".join([x for x in row[2:] if x.strip()])

    my_json["connection"] = connection_json
    my_json["sftp connection"] = connection_sftp
    my_json["ftp connection"] = connection_ftp
    my_json["database connection"] = connection_database
    my_json["smb connection"] = connection_smb
    my_json["ssh connection"] = connection_ssh
    my_json["gpg connection"] = connection_gpg
    my_json["task"] = task_json
    my_json["project"] = project_json
    my_json["user"] = user_json

    return jsonify(my_json)


@dashboard_bp.route("/")
@login_required
def home() -> Union[Response, str]:
    """Return default landing page.

    If user has projects, they will direct to that screen.
    """
    if (
        db.session.query()
        .select_from(Project)
        .add_columns(Project.id)
        .filter(Project.owner_id == current_user.id)
        .first()
    ):
        return render_template(
            "pages/project/all.html.j2",
            title=current_user.full_name + "'s Projects",
            username=current_user.full_name,
            user_id=current_user,
            user=current_user,
        )

    return redirect(url_for("dashboard_bp.dash"))


@dashboard_bp.route("/dashboard")
@login_required
def dash() -> str:
    """Dashboard page."""
    return render_template(
        "pages/dashboard/dashboard.html.j2",
        title="Dashboard",
    )


@dashboard_bp.route("/schedule")
@login_required
def active_schedule() -> str:
    """Graph showing current run schedule for next 12 hrs."""
    try:
        schedule = json.loads(
            requests.get(app.config["SCHEDULER_HOST"] + "/schedule", timeout=60).text
        )

        max_index = max(map(lambda x: x.get("count"), schedule))
        index = (
            [
                max_index,
                int(round(max_index * 0.75, 0)),
                int(round(max_index * 0.5, 0)),
                int(round(max_index * 0.25, 0)),
            ]
            if max_index > 4
            else [max_index]
        )
        return render_template(
            "pages/dashboard/schedule.html.j2",
            schedule=schedule,
            schedule_index=index,
        )

    # pylint: disable=broad-except
    except BaseException as e:
        logging.error(str(e))
        return ""


@dashboard_bp.route("/dash/orphans/delete")
@login_required
def dash_orphans_delete() -> Response:
    """Button to delete any jobs without a linked tasks."""
    try:
        output = json.loads(
            requests.get(app.config["SCHEDULER_HOST"] + "/delete-orphans", timeout=60).text,
        )
        msg = output["message"]
        add_user_log(msg, 0)

    except requests.exceptions.ConnectionError:
        msg = "Failed to delete orphans. Scheduler offline."
        add_user_log(msg, 1)

    flash(msg)

    return redirect(url_for("dashboard_bp.dash"))


@dashboard_bp.route("/dash/errored/run")
@login_required
def dash_errored_run() -> Response:
    """Button to run all errored tasks."""
    submit_executor("run_errored_tasks")

    return redirect(url_for("dashboard_bp.dash"))


@dashboard_bp.route("/dash/scheduled/run")
@login_required
def dash_scheduled_run() -> Response:
    """Button to run all scheduled tasks."""
    submit_executor("run_scheduled_tasks")

    return redirect(url_for("dashboard_bp.dash"))


@dashboard_bp.route("/dash/scheduled/disable")
@login_required
def dash_scheduled_disable() -> Response:
    """Button to disable all scheduled tasks."""
    submit_executor("disabled_scheduled_tasks")

    return redirect(url_for("dashboard_bp.dash"))


def add_user_log(message: str, error_code: int) -> None:
    """Add log entry prefixed by username."""
    log = TaskLog(  # type: ignore[call-arg]
        status_id=7,
        error=error_code,
        message=(current_user.full_name or "none") + ": " + message,
    )
    db.session.add(log)
    db.session.commit()
