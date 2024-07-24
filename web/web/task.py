"""Task web views."""

import json
from typing import Union

import requests
from flask import Blueprint
from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from RelativeToNow import relative_to_now
from sqlalchemy.sql import functions as func
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

task_bp = Blueprint("task_bp", __name__)


@task_bp.route("/task")
@login_required
def all_tasks() -> Union[str, Response]:
    """Page for all tasks."""
    if Task.query.count() < 1:
        return redirect(url_for("project_bp.all_projects"))

    owners = (
        db.session.query()
        .select_from(User)
        .join(Project, Project.owner_id == User.id)
        .join(Task, Task.project_id == Project.id)
        .add_columns(User.full_name, User.id, func.count(Task.id))
        .group_by(User.full_name, User.id)
        .all()
    )

    projects = (
        db.session.query()
        .select_from(Project)
        .join(Task, Task.project_id == Project.id)
        .add_columns(Project.name, Project.id, func.count(Task.id))
        .group_by(Project.name, Project.id)
        .all()
    )
    return render_template(
        "pages/task/all.html.j2", title="Tasks", owners=owners, projects=projects
    )


@task_bp.route("/task/mine")
@login_required
def my_tasks() -> Union[str, Response]:
    """Page for my tasks."""
    me = (
        Task.query.join(Project)
        .join(User, User.id == Project.owner_id)
        .filter(User.id == current_user.id)
        .count()
    )
    if me < 1:
        flash("You don't have any tasks.")
        return redirect(url_for("project_bp.user_projects"))

    projects = (
        db.session.query()
        .select_from(Project)
        .join(User, User.id == Project.owner_id)
        .join(Task, Task.project_id == Project.id)
        .filter(User.id == current_user.id)
        .add_columns(Project.name, Project.id, func.count(Task.id))
        .group_by(Project.name, Project.id)
        .all()
    )

    return render_template(
        "pages/task/all.html.j2",
        title="My Tasks",
        projects=projects,
        user=current_user,
    )


@task_bp.route("/task/user/<user_id>")
@login_required
def user_tasks(user_id: int) -> Union[Response, str]:
    """Page for tasks for a specific user."""
    me = (
        Task.query.join(Project)
        .join(User, User.id == Project.owner_id)
        .filter(User.id == user_id)
        .count()
    )
    my_user = User.query.filter_by(id=user_id).first()

    # pylint: disable=R1705
    if not my_user:
        flash("That user does not exist.")
        return redirect(url_for("project_bp.all_projects"))
    elif me < 1:
        flash(f"{my_user} has no projects.")
        return redirect(url_for("project_bp.all_projects"))

    return render_template(
        "pages/task/all.html.j2",
        title="My Tasks",
        user=my_user,
    )


@task_bp.route("/task/<task_id>")
@login_required
def one_task(task_id: int) -> Union[str, Response]:
    """Get task details page."""
    task = Task.query.filter_by(id=task_id).first()

    if task:
        return render_template(
            "pages/task/one.html.j2",
            t=task,
            r=(
                " (%s)" % task.next_run.strftime("%a, %b %-d, %Y %H:%M:%S")
                if task.next_run  # and task.next_run > datetime.datetime.now()
                else ""
            ),
            r_relative=(
                relative_to_now(task.next_run)
                if task.next_run  # and task.next_run > datetime.datetime.now()
                else "N/A"
            ),
            l=(
                " (%s)" % task.last_run.strftime("%a, %b %-d, %Y %H:%M:%S")
                if task.last_run
                else "Never"
            ),
            l_relative=(relative_to_now(task.last_run) if task.last_run else "Never"),
            title=task.name,
            language=("bash" if task.source_type_id == 6 else "sql"),
            has_secrets=any(p.sensitive == 1 for p in task.params),
        )

    flash("Task does not exist.")
    return redirect(url_for("task_bp.all_tasks"))


@task_bp.route("/task/<task_id>/source_code")
@login_required
def task_get_source_code(task_id: int) -> str:
    """Get source code for a task."""
    try:
        code = json.loads(
            requests.get(
                app.config["RUNNER_HOST"] + "/" + task_id + "/source_code", timeout=60
            ).text
        )["code"]
    # pylint: disable=broad-except
    except BaseException as e:
        if Task.query.filter_by(id=task_id).first():
            log = TaskLog(
                status_id=7,
                error=1,
                task_id=task_id,
                message=(
                    (current_user.full_name or "none")
                    + ": Failed to get source code. ("
                    + str(task_id)
                    + ")\n"
                    + str(e)
                ),
            )
            db.session.add(log)
            db.session.commit()
        code = "error."

    task = Task.query.filter_by(id=task_id).first()
    return render_template(
        "pages/task/code.html.j2",
        code=code,
        cache_enabled=task.enable_source_cache,
        task_id=task_id,
    )


@task_bp.route("/task/<task_id>/refresh_cache")
@login_required
def refresh_cache(task_id: int) -> Response:
    """Get source code for a task."""
    submit_executor("refresh_cache", task_id)
    return redirect(url_for("task_bp.one_task", task_id=task_id))


@task_bp.route("/task/<task_id>/processing_code")
@login_required
def task_get_processing_code(task_id: int) -> str:
    """Get processing code for a task."""
    try:
        code = json.loads(
            requests.get(
                app.config["RUNNER_HOST"] + "/" + task_id + "/processing_code",
                timeout=60,
            ).text
        )["code"]
    # pylint: disable=broad-except
    except BaseException as e:
        if Task.query.filter_by(id=task_id).first():
            log = TaskLog(
                status_id=7,
                error=1,
                task_id=task_id,
                message=(
                    (current_user.full_name or "none")
                    + ": Failed to get processing code. ("
                    + str(task_id)
                    + ")\n"
                    + str(e)
                ),
            )
            db.session.add(log)
            db.session.commit()
        code = "error."

    return render_template(
        "pages/task/code.html.j2",
        code=code,
    )


@task_bp.route("/task/sftp-dest")
@login_required
def task_sftp_dest() -> str:
    """Template to add sftp destination to a task."""
    org = request.args.get("org", default=1, type=int)
    dest = ConnectionSftp.query.filter_by(connection_id=org).order_by(ConnectionSftp.name).all()
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/dest/sftp_dest.html.j2",
        org=org,
        sftp_dest=dest,
        title="Connections",
    )


@task_bp.route("/task/gpg-file")
@login_required
def task_gpg_file() -> str:
    """Template to add gpg encryption to a task."""
    org = request.args.get("org", default=1, type=int)
    dest = ConnectionGpg.query.filter_by(connection_id=org).order_by(ConnectionGpg.name).all()
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/dest/gpg_file.html.j2",
        org=org,
        gpg_file=dest,
        title="Connections",
    )


@task_bp.route("/task/sftp-source")
@login_required
def task_sftp_source() -> str:
    """Template to add sftp source to a task."""
    org = request.args.get("org", default=1, type=int)
    dest = ConnectionSftp.query.filter_by(connection_id=org).order_by(ConnectionSftp.name).all()
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/source/sftp_source.html.j2",
        org=org,
        sftp_source=dest,
        title="Connections",
    )


@task_bp.route("/task/ssh-source")
@login_required
def task_ssh_source() -> str:
    """Template to add ssh source to a task."""
    org = request.args.get("org", default=1, type=int)
    dest = ConnectionSsh.query.filter_by(connection_id=org).order_by(ConnectionSsh.name).all()
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/source/ssh_source.html.j2",
        org=org,
        ssh_source=dest,
        title="Connections",
    )


@task_bp.route("/task/sftp-query")
@login_required
def task_sftp_query() -> str:
    """Template to add sftp query source to a task."""
    org = request.args.get("org", default=1, type=int)
    dest = ConnectionSftp.query.filter_by(connection_id=org).order_by(ConnectionSftp.name).all()
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/query/sftp_query.html.j2",
        org=org,
        sftp_query=dest,
        title="Connections",
    )


@task_bp.route("/task/sftp-processing")
@login_required
def task_sftp_processing() -> str:
    """Template to add sftp processing source to a task."""
    org = request.args.get("org", default=1, type=int)
    dest = ConnectionSftp.query.filter_by(connection_id=org).order_by(ConnectionSftp.name).all()

    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/processing/sftp_processing.html.j2",
        org=org,
        sftp_processing=dest,
        title="Connections",
    )


@task_bp.route("/task/ftp-dest")
@login_required
def task_ftp_dest() -> str:
    """Template to add ftp destination to a task."""
    org = request.args.get("org", default=1, type=int)
    dest = ConnectionFtp.query.filter_by(connection_id=org).order_by(ConnectionFtp.name).all()
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/dest/ftp_dest.html.j2", org=org, ftp_dest=dest, title="Connections"
    )


@task_bp.route("/task/ftp-source")
@login_required
def task_ftp_source() -> str:
    """Template to add ftp source to a task."""
    org = request.args.get("org", default=1, type=int)
    dest = ConnectionFtp.query.filter_by(connection_id=org).order_by(ConnectionFtp.name).all()
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/source/ftp_source.html.j2",
        org=org,
        ftp_source=dest,
        title="Connections",
    )


@task_bp.route("/task/ftp-processing")
@login_required
def task_ftp_processing() -> str:
    """Template to add ftp processing source to a task."""
    org = request.args.get("org", default=1, type=int)
    dest = ConnectionFtp.query.filter_by(connection_id=org).order_by(ConnectionFtp.name).all()
    org = Connection.query.filter_by(id=org).first()
    return render_template(
        "pages/task/processing/ftp_processing.html.j2",
        org=org,
        ftp_processing=dest,
        title="Connections",
    )


@task_bp.route("/task/ftp-query")
@login_required
def task_ftp_query() -> str:
    """Template to add ftp query source to a task."""
    org = request.args.get("org", default=1, type=int)
    dest = ConnectionFtp.query.filter_by(connection_id=org).order_by(ConnectionFtp.name).all()
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/query/ftp_query.html.j2",
        org=org,
        ftp_query=dest,
        title="Connections",
    )


@task_bp.route("/task/smb-source")
@login_required
def task_smb_source() -> str:
    """Template to add smb source to a task."""
    org = request.args.get("org", default=1, type=int)
    dest = ConnectionSmb.query.filter_by(connection_id=org).order_by(ConnectionSmb.name).all()
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/source/smb_source.html.j2",
        org=org,
        smb_source=dest,
        title="Connections",
    )


@task_bp.route("/task/smb-dest")
@login_required
def task_smb_dest() -> str:
    """Template to add smb destination to a task."""
    org = request.args.get("org", default=1, type=int)
    dest = ConnectionSmb.query.filter_by(connection_id=org).order_by(ConnectionSmb.name).all()
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/dest/smb_dest.html.j2", org=org, smb_dest=dest, title="Connections"
    )


@task_bp.route("/task/smb-query")
@login_required
def task_smb_query() -> str:
    """Template to add smb query source to a task."""
    org = request.args.get("org", default=1, type=int)
    query = ConnectionSmb.query.filter_by(connection_id=org).order_by(ConnectionSmb.name).all()
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/query/smb_query.html.j2",
        org=org,
        smb_query=query,
        title="Connections",
    )


@task_bp.route("/task/smb-processing")
@login_required
def task_smb_processing() -> str:
    """Template to add smb processing source to a task."""
    org = request.args.get("org", default=1, type=int)
    processing = (
        ConnectionSmb.query.filter_by(connection_id=org).order_by(ConnectionSmb.name).all()
    )
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/processing/smb_processing.html.j2",
        org=org,
        smb_processing=processing,
        title="Connections",
    )


@task_bp.route("/task/database-source")
@login_required
def task_database_source() -> str:
    """Template to add database source to a task."""
    org = request.args.get("org", default=1, type=int)

    dest = (
        ConnectionDatabase.query.filter_by(connection_id=org)
        .order_by(ConnectionDatabase.name)
        .all()
    )
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/source/database_source.html.j2",
        org=org,
        database_source=dest,
        title="Connections",
    )


@task_bp.route("/task/<task_id>/email_success_subject_preview")
@login_required
def email_success_subject_preview(task_id: int) -> str:
    """Generate a task filename preview."""
    try:
        return requests.get(
            f"{app.config['RUNNER_HOST']}/task/{task_id}/email_success_subject_preview",
            timeout=60,
        ).text
    except BaseException as e:
        return f'<span class="has-tooltip-arrow has-tooltip-right has-tooltip-multiline tag is-danger is-light" data-tooltip="{e}">Offline</span>'


@task_bp.route("/task/<task_id>/email_error_subject_preview")
@login_required
def email_error_subject_preview(task_id: int) -> str:
    """Generate a task filename preview."""
    try:
        return requests.get(
            f"{app.config['RUNNER_HOST']}/task/{task_id}/email_error_subject_preview",
            timeout=60,
        ).text
    except BaseException as e:
        return f'<span class="has-tooltip-arrow has-tooltip-right has-tooltip-multiline tag is-danger is-light" data-tooltip="{e}">Offline</span>'
