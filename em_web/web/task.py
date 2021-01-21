"""Task web views."""
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
import html
import json
import os

import requests
from em_web import db, ldap
from em_web.model import (
    Connection,
    ConnectionDatabase,
    ConnectionFtp,
    ConnectionSftp,
    ConnectionSmb,
    ConnectionSsh,
    Project,
    QuoteLevel,
    Task,
    TaskDestinationFileType,
    TaskFile,
    TaskLog,
    TaskProcessingType,
    TaskSourceQueryType,
    TaskSourceType,
    TaskStatus,
    User,
)
from flask import Blueprint, Response
from flask import current_app as app
from flask import jsonify, redirect, render_template, request, session, url_for
from RelativeToNow import relative_to_now
from sqlalchemy import and_, text

task_bp = Blueprint("task_bp", __name__)


@task_bp.route("/task/<task_id>/duplicate")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_duplicate(task_id):
    """Duplicate a task.

    :url: /task/<task_id>/duplicate
    :param task_id: id of task to duplicate

    :returns: html view of new task.
    """
    whoami = User.query.filter_by(user_id=session.get("user_id")).first()
    my_task = Task.query.filter_by(id=task_id).first()

    new_task = Task()

    # pylint: disable=protected-access
    for key in my_task.__table__.columns._data.keys():
        if key not in ["id", "last_run", "last_run_job_id", "status_id"]:
            setattr(new_task, key, getattr(my_task, key))

    new_task.enabled = 0
    new_task.creator_id = whoami.id
    new_task.updater_id = whoami.id
    new_task.status_id = None
    new_task.name = new_task.name + " (Duplicated)"

    db.session.add(new_task)
    db.session.commit()

    return render_template(
        "pages/task/details.html.j2",
        t=new_task,
        r="None",
        r_relative="None",
        l=(
            datetime.datetime.strftime(new_task.last_run, "%a, %b %-d, %Y %H:%M:%S")
            if new_task.last_run
            else ""
        )
        if new_task.last_run
        else "Never",
        l_relative=(
            relative_to_now(new_task.last_run) if new_task.last_run else "Never"
        ),
        title=new_task.name,
    )


@task_bp.route("/task/<task_id>/hello")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_hello(task_id):
    """Get basic task info.

    :param task_id: id of task to query

    :returns json of task details
    """
    task = Task.query.filter_by(id=task_id).first()

    return jsonify(
        {
            "status": (task.status.name if task.status else ""),
            "next_run": (
                relative_to_now(task.next_run.replace(tzinfo=None))
                if task.next_run
                else ""
            ),
            "last_run": (
                relative_to_now(task.last_run.replace(tzinfo=None))
                if task.last_run
                else ""
            ),
        }
    )


@task_bp.route("/task/<task_id>/delete")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_delete(task_id):
    """Delete a task.

    :url: /task/<task_id>/delete
    :param task_id: id of task to delete

    :returns: redirects back to project or dashboard.
    """
    task = Task.query.filter_by(id=task_id).first()
    project = task.project if task else None

    try:
        requests.get(app.config["SCHEUDULER_HOST"] + "/delete/" + str(task.id))

        TaskLog.query.filter_by(task_id=task_id).delete()
        db.session.commit()
        TaskFile.query.filter_by(task_id=task_id).delete()
        db.session.commit()
        Task.query.filter_by(id=task_id).delete()
        db.session.commit()

        log = TaskLog(
            status_id=7,
            message=session.get("user_full_name")
            + ": Task deleted. ("
            + str(task_id)
            + ")",
        )
        db.session.add(log)
        db.session.commit()

    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            error=1,
            message=(
                session.get("user_full_name")
                + ": Failed to delete task. ("
                + task_id
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()

    if project:
        return redirect(url_for("project_bp.project_get", project_id=project.id))
    return redirect(url_for("dash"))


@task_bp.route("/task")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_all():
    """Page for all tasks.

    :url: /task
    :returns: html of task page.
    """
    me = Task.query.count()
    if me < 1:
        return redirect(url_for("project_bp.project"))
    return render_template("pages/task/all.html.j2", title="Tasks")


@task_bp.route("/task/mine")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_mine():
    """Page for my tasks.

    :url: /task/mine
    :returns: html of task page.
    """
    me = (
        Task.query.join(Project)
        .join(User, User.id == Project.owner_id)
        .filter(User.user_id == session.get("user_id"))
        .count()
    )
    if me < 1:
        return redirect(url_for("project_bp.project"))
    return render_template(
        "pages/task/all.html.j2", mine=session.get("user_full_name"), title="My Tasks"
    )


@task_bp.route("/task/user/<user_id>")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_user(user_id):
    """Page for tasks for a specific user.

    :url: /task/user/<user_id>
    :param user_id: id of task owner

    :returns: html of task page.
    """
    me = (
        Task.query.join(Project)
        .join(User, User.id == Project.owner_id)
        .filter(User.id == user_id)
        .count()
    )
    my_user = User.query.filter_by(id=user_id).first()

    if me < 1:
        return redirect(url_for("project_bp.project"))
    return render_template(
        "pages/task/all.html.j2",
        mine=my_user.full_name,
        title="My Tasks",
        user_id=user_id,
    )


@task_bp.route("/project/<project_id>/task/new", methods=["GET", "POST"])
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_new(project_id):
    """Create a new task.

    :url: /project/<project_id>/task/new
    :param project_id: id of project owning the new task

    :returns: redirects to task page.
    """
    if request.method == "GET":
        source_type = TaskSourceType.query.order_by(TaskSourceType.name).all()
        source_query_type = TaskSourceQueryType.query.order_by(
            TaskSourceQueryType.name
        ).all()
        source = ConnectionDatabase.query.order_by(ConnectionDatabase.name).all()
        conn = Connection.query.order_by(Connection.name).all()
        file_type = TaskDestinationFileType.query.order_by(
            TaskDestinationFileType.id
        ).all()
        processing_type = TaskProcessingType.query.order_by(
            TaskProcessingType.name
        ).all()
        quote_level = QuoteLevel.query.order_by(QuoteLevel.id).all()

        return render_template(
            "pages/task/new.html.j2",
            p=Project.query.filter_by(id=project_id).first(),
            source_type=source_type,
            source_query_type=source_query_type,
            processing_type=processing_type,
            quote_level=quote_level,
            source=source,
            conn=conn,
            title="New Task",
            t=Task.query.filter_by(id=0).first(),
            file_type=file_type,
        )

    # create tasks
    form = request.form

    tme = Task(name=form["name"].strip())
    tme.project_id = project_id

    whoami = User.query.filter_by(user_id=session.get("user_id")).first()

    tme.creator_id = whoami.id
    tme.updater_id = whoami.id

    # source options
    if "sourceType" in form:
        tme.source_type_id = form["sourceType"]

        # database
        tme.source_database_id = (
            form["task-source-database"]
            if form["sourceType"] == "1" and "task-source-database" in form
            else None
        )

        tme.source_query_include_header = (
            form["task_include_query_headers"]
            if "task_include_query_headers" in form
            else None
        )

        # smb
        tme.source_smb_id = (
            form["task-source-smb"]
            if form["sourceType"] == "2" and "task-source-smb" in form
            else None
        )
        tme.source_smb_file = (
            form["sourceSmbFile"]
            if form["sourceType"] == "2" and "sourceSmbFile" in form
            else None
        )

        # smb delimiter
        tme.source_smb_ignore_delimiter = (
            1
            if (
                form["sourceType"] == "2"
                and "task_smb_ignore_delimiter" in form
                and str(form["task_smb_ignore_delimiter"]) == "1"
            )
            else None
        )

        tme.source_smb_delimiter = (
            form["sourceSmbDelimiter"]
            if form["sourceType"] == "2" and "sourceSmbDelimiter" in form
            else None
        )

        # sftp

        tme.source_sftp_id = (
            form["task-source-sftp"]
            if (form["sourceType"] == "3" and "task-source-sftp" in form)
            else None
        )

        tme.source_sftp_file = (
            form["sourceSftpFile"]
            if (form["sourceType"] == "3" and "sourceSftpFile" in form)
            else None
        )

        # sftp delimiter
        tme.source_sftp_ignore_delimiter = (
            1
            if form["sourceType"] == "3"
            and "task_sftp_ignore_delimiter" in form
            and str(form["task_sftp_ignore_delimiter"]) == "1"
            else None
        )

        tme.source_sftp_delimiter = (
            form["sourceSftpDelimiter"]
            if form["sourceType"] == "3" and "sourceSftpDelimiter" in form
            else None
        )
        # ftp

        tme.source_ftp_id = (
            form["task-source-ftp"]
            if (form["sourceType"] == "4" and "task-source-ftp" in form)
            else None
        )

        tme.source_ftp_file = (
            form["sourceFtpFile"]
            if (form["sourceType"] == "4" and "sourceFtpFile" in form)
            else None
        )

        # ftp delimiter
        tme.source_ftp_ignore_delimiter = (
            1
            if form["sourceType"] == "4"
            and "task_ftp_ignore_delimiter" in form
            and str(form["task_ftp_ignore_delimiter"]) == "1"
            else None
        )

        tme.source_ftp_delimiter = (
            form["sourceFtpDelimiter"]
            if form["sourceType"] == "4" and "sourceFtpDelimiter" in form
            else None
        )

        # ssh
        tme.source_ssh_id = (
            form["task-source-ssh"]
            if (form["sourceType"] == "6" and "task-source-ssh" in form)
            else None
        )

        tme.source_ssh_command = (
            form["sourceSshCommand"]
            if "sourceSshCommand" in form and form["sourceType"] == "6"
            else None
        )

        # query options
    if "sourceQueryType" in form:
        tme.source_query_type_id = form["sourceQueryType"]
        tme.query_params = form["queryParams"] if "queryParams" in form else ""
        tme.source_git = form["sourceGit"] if form["sourceQueryType"] == "1" else None

        # smb file
        tme.query_smb_file = (
            form["sourceQuerySmbFile"] if form["sourceQueryType"] == "2" else None
        )
        tme.query_smb_id = (
            form["task-query-smb"]
            if form["sourceQueryType"] == "2" and "task-query-smb" in form
            else None
        )

        # sftp file
        tme.query_sftp_file = (
            form["sourceQuerySftpFile"] if form["sourceQueryType"] == "5" else None
        )
        tme.query_sftp_id = (
            form["task-query-sftp"]
            if form["sourceQueryType"] == "5" and "task-query-sftp" in form
            else None
        )

        # ftp file
        tme.query_ftp_file = (
            form["sourceQueryFtpFile"] if form["sourceQueryType"] == "6" else None
        )
        tme.query_ftp_id = (
            form["task-query-ftp"]
            if form["sourceQueryType"] == "6" and "task-query-ftp" in form
            else None
        )

        tme.source_url = form["sourceURL"] if form["sourceQueryType"] == "3" else None
        tme.source_code = form["sourceCode"] if form["sourceQueryType"] == "4" else None

    # processing script

    if "processingType" in form:

        tme.processing_type_id = (
            form["processingType"] if str(form["processingType"]) != "none" else None
        )

        if str(form["processingType"]) == "1":  # smb
            tme.processing_smb_file = (
                form["processingSmbFile"] if "processingSmbFile" in form else ""
            )
        elif str(form["processingType"]) == "2":  # sftp
            tme.processing_sftp_file = (
                form["processingSftpFile"] if "processingSftpFile" in form else ""
            )
        elif str(form["processingType"]) == "3":  # ftp
            tme.processing_ftp_file = (
                form["processingFtpFile"] if "processingFtpFile" in form else ""
            )
        elif str(form["processingType"]) == "4":  # git url
            tme.processing_git = (
                form["processingGit"] if "processingGit" in form else ""
            )
        elif str(form["processingType"]) == "5":  # other url
            tme.processing_url = (
                form["processingUrl"] if "processingUrl" in form else ""
            )
        elif str(form["processingType"]) == "6":  # raw code
            tme.processing_code = (
                form["processingCode"] if "processingCode" in form else ""
            )

        tme.processing_command = (
            form["processingCommand"] if "processingCommand" in form else None
        )
    else:
        tme.processing_type_id = None

    tme.destination_quote_level_id = form["quoteLevel"] if "quoteLevel" in form else 3

    tme.destination_file_type_id = (
        form["fileType"] if str(form["fileType"]) != "none" else None
    )
    tme.destination_file_name = form["destinationFileName"]

    tme.destination_create_zip = (
        1
        if ("task_create_zip" in form and str(form["task_create_zip"]) == str("1"))
        else None
    )
    tme.destination_zip_name = (
        form["destinationZipName"]
        if (
            "destinationZipName" in form
            and "task_create_zip" in form
            and str(form["task_create_zip"]) == "1"
        )
        else None
    )

    if form["fileType"] == "2" or form["fileType"] == "4":
        tme.destination_file_delimiter = (
            form["fileDelimiter"] if "fileDelimiter" in form else None
        )
    else:
        tme.destination_file_delimiter = None

    tme.destination_ignore_delimiter = (
        1
        if (form["fileType"] == "2" or form["fileType"] == "4")
        and "task_ignore_file_delimiter" in form
        and str(form["task_ignore_file_delimiter"]) == "1"
        else None
    )
    tme.destination_sftp = form["task_save_sftp"] if "task_save_sftp" in form else 0
    tme.destination_sftp_id = (
        form["task-destination-sftp"] if "task-destination-sftp" in form else None
    )
    tme.destination_sftp_overwrite = (
        form["task_overwrite_sftp"] if "task_overwrite_sftp" in form else None
    )

    tme.destination_ftp = form["task_save_ftp"] if "task_save_ftp" in form else 0
    tme.destination_ftp_id = (
        form["task-destination-ftp"] if "task-destination-ftp" in form else None
    )
    tme.destination_ftp_overwrite = (
        form["task_overwrite_ftp"] if "task_overwrite_ftp" in form else None
    )

    tme.destination_smb = form["task_save_smb"] if "task_save_smb" in form else 0
    tme.smb_id = (
        form["task-destination-smb"] if "task-destination-smb" in form else None
    )
    tme.destination_smb_overwrite = (
        form["task_overwrite_smb"] if "task_overwrite_smb" in form else None
    )

    #  email stuff

    if "task_send_completion_email" in form:
        tme.email_completion = form["task_send_completion_email"]

        tme.email_completion_recipients = (
            form["completionEmailRecip"] if "completionEmailRecip" in form else ""
        )

        tme.email_completion_message = (
            form["completion_email_msg"] if "completion_email_msg" in form else ""
        )

        tme.email_completion_log = (
            form["task_send_completion_email_log"]
            if "task_send_completion_email_log" in form
            else 0
        )

        tme.email_completion_file = (
            form["task_send_output"] if "task_send_output" in form else 0
        )

        tme.email_completion_dont_send_empty_file = (
            form["task_dont_send_empty"] if "task_dont_send_empty" in form else 0
        )

    else:
        tme.email_completion = 0

    if "task_send_error_email" in form:
        tme.email_error = form["task_send_error_email"]

        tme.email_error_recipients = (
            form["errorEmailRecip"] if "errorEmailRecip" in form else ""
        )

        tme.email_error_message = (
            form["errorEmailMsg"] if "errorEmailMsg" in form else ""
        )
    else:
        tme.email_error = 0

    tme.enabled = form["task-ooff"] if "task-ooff" in form else 0

    db.session.add(tme)
    db.session.commit()

    log = TaskLog(
        task_id=tme.id,
        status_id=7,
        message=session.get("user_full_name") + ": Task created.",
    )
    db.session.add(log)
    db.session.commit()

    if tme.enabled == 1:
        try:
            requests.get(app.config["SCHEUDULER_HOST"] + "/add/" + str(tme.id))
            log = TaskLog(
                task_id=tme.id,
                status_id=7,
                message=session.get("user_full_name") + ": Task enabled.",
            )
            db.session.add(log)
            db.session.commit()

        # pylint: disable=broad-except
        except BaseException as e:
            log = TaskLog(
                status_id=7,
                error=1,
                task_id=tme.id,
                message=(
                    session.get("user_full_name")
                    + ": Failed to enable task. ("
                    + tme.id
                    + ")\n"
                    + str(e)
                ),
            )
            db.session.add(log)
            db.session.commit()

    return redirect(url_for("project_bp.project_get", project_id=project_id))


@task_bp.route("/task/<task_id>")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task(task_id):
    """Get task details page.

    :url: /task/<task_id>
    :param task_id: id of the task

    :returns: html for task page.
    """
    task = Task.query.filter_by(id=task_id).first()

    if task:
        return render_template(
            "pages/task/details.html.j2",
            t=task,
            r=(
                task.next_run.astimezone().strftime("%a, %b %-d, %Y %H:%M:%S")
                if task.next_run
                else ""
            )
            if task.last_run
            else "N/A",
            r_relative=(
                relative_to_now(task.next_run.replace(tzinfo=None))
                if task.next_run
                else "N/A"
            ),
            l=(
                task.last_run.strftime("%a, %b %-d, %Y %H:%M:%S")
                if task.last_run
                else ""
            )
            if task.last_run
            else "Never",
            l_relative=(relative_to_now(task.last_run) if task.last_run else "Never"),
            title=task.name,
            language=("bash" if task.source_type_id == 6 else "sql"),
        )

    return render_template("pages/task/details.html.j2", invalid=True, title="Error")


@task_bp.route("/task/<task_id>/edit", methods=["GET"])
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_edit_get(task_id):
    """Task edit page.

    :url: /task/<task_id>/edit
    :param task_id: id of project owning the tasks

    :returns: redirects to the project details page.
    """
    # pylint: disable=too-many-locals
    me = Task.query.filter_by(id=task_id).first()

    if me:
        source_type = TaskSourceType.query.order_by(TaskSourceType.name).all()
        processing_type = TaskProcessingType.query.order_by(
            TaskProcessingType.name
        ).all()
        source_query_type = TaskSourceQueryType.query.order_by(
            TaskSourceQueryType.name
        ).all()

        source = ConnectionDatabase.query.order_by(ConnectionDatabase.name).all()

        conn = Connection.query.order_by(Connection.name).all()

        file_type = TaskDestinationFileType.query.order_by(
            TaskDestinationFileType.id
        ).all()
        sftp_dest = (
            ConnectionSftp.query.filter_by(
                connection_id=me.destination_sftp_conn.connection_id
            ).all()
            if me.destination_sftp_id
            else ""
        )
        ftp_dest = (
            ConnectionFtp.query.filter_by(
                connection_id=me.destination_ftp_conn.connection_id
            ).all()
            if me.destination_ftp_id
            else ""
        )
        smb_dest = (
            ConnectionSmb.query.filter_by(
                connection_id=me.destination_smb_conn.connection_id
            ).all()
            if me.destination_smb_id
            else ""
        )

        sftp_source = (
            ConnectionSftp.query.filter_by(
                connection_id=me.source_sftp_conn.connection_id
            ).all()
            if me.source_sftp_id
            else ""
        )
        sftp_query = (
            ConnectionSftp.query.filter_by(
                connection_id=me.query_sftp_conn.connection_id
            ).all()
            if me.query_sftp_id
            else ""
        )
        ssh_source = (
            ConnectionSsh.query.filter_by(
                connection_id=me.source_ssh_conn.connection_id
            ).all()
            if me.source_ssh_id
            else ""
        )
        ftp_source = (
            ConnectionFtp.query.filter_by(
                connection_id=me.source_ftp_conn.connection_id
            ).all()
            if me.source_ftp_id
            else ""
        )
        ftp_query = (
            ConnectionFtp.query.filter_by(
                connection_id=me.query_ftp_conn.connection_id
            ).all()
            if me.query_ftp_id
            else ""
        )
        smb_source = (
            ConnectionSmb.query.filter_by(
                connection_id=me.source_smb_conn.connection_id
            ).all()
            if me.source_smb_id
            else ""
        )
        smb_query = (
            ConnectionSmb.query.filter_by(
                connection_id=me.query_smb_conn.connection_id
            ).all()
            if me.query_smb_id
            else ""
        )
        database_source = (
            ConnectionDatabase.query.filter_by(
                connection_id=me.source_database_conn.connection_id
            ).all()
            if me.source_database_id
            else ""
        )

        sftp_processing = (
            ConnectionSftp.query.filter_by(
                connection_id=me.processing_sftp_conn.connection_id
            ).all()
            if me.processing_sftp_id
            else ""
        )
        ftp_processing = (
            ConnectionFtp.query.filter_by(
                connection_id=me.processing_ftp_conn.connection_id
            ).all()
            if me.processing_ftp_id
            else ""
        )
        smb_processing = (
            ConnectionSmb.query.filter_by(
                connection_id=me.processing_smb_conn.connection_id
            ).all()
            if me.processing_smb_id
            else ""
        )

        quote_level = QuoteLevel.query.order_by(QuoteLevel.id).all()

        return render_template(
            "pages/task/new.html.j2",
            t=me,
            title="Editing " + me.name,
            source_type=source_type,
            processing_type=processing_type,
            source_query_type=source_query_type,
            source=source,
            sftp_dest=sftp_dest,
            ftp_dest=ftp_dest,
            smb_dest=smb_dest,
            conn=conn,
            sftp_source=sftp_source,
            ftp_source=ftp_source,
            smb_source=smb_source,
            ssh_source=ssh_source,
            sftp_query=sftp_query,
            ftp_query=ftp_query,
            smb_query=smb_query,
            sftp_processing=sftp_processing,
            ftp_processing=ftp_processing,
            smb_processing=smb_processing,
            database_source=database_source,
            file_type=file_type,
            quote_level=quote_level,
        )

    return render_template("pages/task/details.html.j2", invalid=True, title="Error")


@task_bp.route("/task/<task_id>/git")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_get_git_code(task_id):
    """Get git code for a task.

    :url: /task/<task_id>/git
    :param task_id: id of task

    :returns: html page with source code.
    """
    try:
        code = json.loads(
            requests.get(app.config["RUNNER_HOST"] + "/" + task_id + "/git").text
        )["code"]
    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            error=1,
            task_id=task_id,
            message=(
                session.get("user_full_name")
                + ": Failed to get git code. ("
                + task_id
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


@task_bp.route("/task/<task_id>/source")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_get_source_code(task_id):
    """Get git code for a task.

    :url: /task/<task_id>/git
    :param task_id: id of task

    :returns: html page with source code.
    """
    try:
        code = json.loads(
            requests.get(app.config["RUNNER_HOST"] + "/" + task_id + "/source").text
        )["code"]
    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            error=1,
            task_id=task_id,
            message=(
                session.get("user_full_name")
                + ": Failed to get source code. ("
                + task_id
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


@task_bp.route("/task/<task_id>/url")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_get_url_code(task_id):
    """Get non-git source code for a task.

    :url: /task/<task_id>/url
    :param task_id: id of task

    :returns: html page with source code.
    """
    try:
        code = json.loads(
            requests.get(app.config["RUNNER_HOST"] + "/" + task_id + "/url").text
        )["code"]
    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            error=1,
            task_id=task_id,
            message=(
                session.get("user_full_name")
                + ": Failed to get url code. ("
                + task_id
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


@task_bp.route("/task/<task_id>/processing_git")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_get_processing_git_code(task_id):
    """Get git code for a task.

    :url: /task/<task_id>/processing_git
    :param task_id: id of task

    :returns: html page with source code.
    """
    try:
        code = json.loads(
            requests.get(
                app.config["RUNNER_HOST"] + "/" + task_id + "/processing_git"
            ).text
        )["code"]
    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            error=1,
            task_id=task_id,
            message=(
                session.get("user_full_name")
                + ": Failed to get processing_git code. ("
                + task_id
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


@task_bp.route("/task/<task_id>/processing_url")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_get_processing_url_code(task_id):
    """Get non-git code for a task.

    :url: /task/<task_id>/processing_url
    :param task_id: id of task

    :returns: html page with source code.
    """
    try:
        code = json.loads(
            requests.get(
                app.config["RUNNER_HOST"] + "/" + task_id + "/processing_url"
            ).text
        )["code"]
    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            error=1,
            task_id=task_id,
            message=(
                session.get("user_full_name")
                + ": Failed to get processing_url code. ("
                + task_id
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


@task_bp.route("/task/<task_id>/edit", methods=["POST"])
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_edit_post(task_id):
    """Save task edits.

    :url: /task/<task_id>/edit
    :param task_id: id of task

    :returns: redirect to task details page.
    """
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    form = request.form
    whoami = User.query.filter_by(user_id=session.get("user_id")).first()

    tme = Task.query.filter_by(id=task_id).first()

    tme.name = form["name"].strip()
    tme.updater_id = whoami.id
    # source options
    if "sourceType" in form:
        tme.source_type_id = form["sourceType"]

        # database
        tme.source_database_id = (
            form["task-source-database"]
            if form["sourceType"] == "1" and "task-source-database" in form
            else None
        )

        tme.source_query_include_header = (
            form["task_include_query_headers"]
            if "task_include_query_headers" in form
            else None
        )

        # smb
        tme.source_smb_id = (
            form["task-source-smb"]
            if form["sourceType"] == "2" and "task-source-smb" in form
            else None
        )
        tme.source_smb_file = (
            form["sourceSmbFile"]
            if form["sourceType"] == "2" and "sourceSmbFile" in form
            else None
        )

        # smb delimiter
        tme.source_smb_ignore_delimiter = (
            1
            if (
                form["sourceType"] == "2"
                and "task_smb_ignore_delimiter" in form
                and str(form["task_smb_ignore_delimiter"]) == "1"
            )
            else None
        )

        tme.source_smb_delimiter = (
            form["sourceSmbDelimiter"]
            if form["sourceType"] == "2" and "sourceSmbDelimiter" in form
            else None
        )

        # sftp

        tme.source_sftp_id = (
            form["task-source-sftp"]
            if (form["sourceType"] == "3" and "task-source-sftp" in form)
            else None
        )

        tme.source_sftp_file = (
            form["sourceSftpFile"]
            if (form["sourceType"] == "3" and "sourceSftpFile" in form)
            else None
        )

        # sftp delimiter
        tme.source_sftp_ignore_delimiter = (
            1
            if form["sourceType"] == "3"
            and "task_sftp_ignore_delimiter" in form
            and str(form["task_sftp_ignore_delimiter"]) == "1"
            else None
        )

        tme.source_sftp_delimiter = (
            form["sourceSftpDelimiter"]
            if form["sourceType"] == "3" and "sourceSftpDelimiter" in form
            else None
        )
        # ftp

        tme.source_ftp_id = (
            form["task-source-ftp"]
            if (form["sourceType"] == "4" and "task-source-ftp" in form)
            else None
        )

        tme.source_ftp_file = (
            form["sourceFtpFile"]
            if (form["sourceType"] == "4" and "sourceFtpFile" in form)
            else None
        )

        # ftp delimiter
        tme.source_ftp_ignore_delimiter = (
            1
            if form["sourceType"] == "4"
            and "task_ftp_ignore_delimiter" in form
            and str(form["task_ftp_ignore_delimiter"]) == "1"
            else None
        )

        tme.source_ftp_delimiter = (
            form["sourceFtpDelimiter"]
            if form["sourceType"] == "4" and "sourceFtpDelimiter" in form
            else None
        )

        # ssh
        tme.source_ssh_id = (
            form["task-source-ssh"]
            if (form["sourceType"] == "6" and "task-source-ssh" in form)
            else None
        )

        tme.source_ssh_command = (
            form["sourceSshCommand"]
            if "sourceSshCommand" in form and form["sourceType"] == "6"
            else None
        )

        # query options
    if "sourceQueryType" in form:
        tme.source_query_type_id = form["sourceQueryType"]
        tme.query_params = form["queryParams"] if "queryParams" in form else ""
        tme.source_git = form["sourceGit"] if form["sourceQueryType"] == "1" else None

        # smb file
        tme.query_smb_file = (
            form["sourceQuerySmbFile"] if form["sourceQueryType"] == "2" else None
        )
        tme.query_smb_id = (
            form["task-query-smb"]
            if form["sourceQueryType"] == "2" and "task-query-smb" in form
            else None
        )

        # sftp file
        tme.query_sftp_file = (
            form["sourceQuerySftpFile"] if form["sourceQueryType"] == "5" else None
        )
        tme.query_sftp_id = (
            form["task-query-sftp"]
            if form["sourceQueryType"] == "5" and "task-query-sftp" in form
            else None
        )

        # ftp file
        tme.query_ftp_file = (
            form["sourceQueryFtpFile"] if form["sourceQueryType"] == "6" else None
        )
        tme.query_ftp_id = (
            form["task-query-ftp"]
            if form["sourceQueryType"] == "6" and "task-query-ftp" in form
            else None
        )

        tme.source_url = form["sourceURL"] if form["sourceQueryType"] == "3" else None
        tme.source_code = form["sourceCode"] if form["sourceQueryType"] == "4" else None

    # processing script

    if "processingType" in form:

        tme.processing_type_id = (
            form["processingType"] if str(form["processingType"]) != "none" else None
        )

        if str(form["processingType"]) == "1":  # smb
            tme.processing_smb_file = (
                form["processingSmbFile"] if "processingSmbFile" in form else ""
            )
        elif str(form["processingType"]) == "2":  # sftp
            tme.processing_sftp_file = (
                form["processingSftpFile"] if "processingSftpFile" in form else ""
            )
        elif str(form["processingType"]) == "3":  # ftp
            tme.processing_ftp_file = (
                form["processingFtpFile"] if "processingFtpFile" in form else ""
            )
        elif str(form["processingType"]) == "4":  # git url
            tme.processing_git = (
                form["processingGit"] if "processingGit" in form else ""
            )
        elif str(form["processingType"]) == "5":  # other url
            tme.processing_url = (
                form["processingUrl"] if "processingUrl" in form else ""
            )
        elif str(form["processingType"]) == "6":  # raw code
            tme.processing_code = (
                form["processingCode"] if "processingCode" in form else ""
            )

        tme.processing_command = (
            form["processingCommand"] if "processingCommand" in form else None
        )
    else:
        tme.processing_type_id = None

    tme.destination_quote_level_id = form["quoteLevel"] if "quoteLevel" in form else 3

    tme.destination_file_type_id = (
        form["fileType"] if str(form["fileType"]) != "none" else None
    )
    tme.destination_file_name = form["destinationFileName"]

    tme.destination_create_zip = (
        1
        if ("task_create_zip" in form and str(form["task_create_zip"]) == str("1"))
        else None
    )
    tme.destination_zip_name = (
        form["destinationZipName"]
        if (
            "destinationZipName" in form
            and "task_create_zip" in form
            and str(form["task_create_zip"]) == "1"
        )
        else None
    )

    if form["fileType"] == "2" or form["fileType"] == "4":
        tme.destination_file_delimiter = (
            form["fileDelimiter"] if "fileDelimiter" in form else None
        )
    else:
        tme.destination_file_delimiter = None

    tme.destination_ignore_delimiter = (
        1
        if (form["fileType"] == "2" or form["fileType"] == "4")
        and "task_ignore_file_delimiter" in form
        and str(form["task_ignore_file_delimiter"]) == "1"
        else None
    )

    tme.destination_sftp = form["task_save_sftp"] if "task_save_sftp" in form else 0
    tme.destination_sftp_id = (
        form["task-destination-sftp"] if "task-destination-sftp" in form else None
    )
    tme.destination_sftp_overwrite = (
        form["task_overwrite_sftp"] if "task_overwrite_sftp" in form else None
    )

    tme.destination_ftp = form["task_save_ftp"] if "task_save_ftp" in form else 0
    tme.destination_ftp_id = (
        form["task-destination-ftp"] if "task-destination-ftp" in form else None
    )
    tme.destination_ftp_overwrite = (
        form["task_overwrite_ftp"] if "task_overwrite_ftp" in form else None
    )

    tme.destination_smb = form["task_save_smb"] if "task_save_smb" in form else 0
    tme.smb_id = (
        form["task-destination-smb"] if "task-destination-smb" in form else None
    )
    tme.destination_smb_overwrite = (
        form["task_overwrite_smb"] if "task_overwrite_smb" in form else None
    )

    #  email stuff

    if "task_send_completion_email" in form:
        tme.email_completion = form["task_send_completion_email"]

        tme.email_completion_recipients = (
            form["completionEmailRecip"] if "completionEmailRecip" in form else ""
        )

        tme.email_completion_message = (
            form["completion_email_msg"] if "completion_email_msg" in form else ""
        )

        tme.email_completion_log = (
            form["task_send_completion_email_log"]
            if "task_send_completion_email_log" in form
            else 0
        )

        tme.email_completion_file = (
            form["task_send_output"] if "task_send_output" in form else 0
        )

        tme.email_completion_dont_send_empty_file = (
            form["task_dont_send_empty"] if "task_dont_send_empty" in form else 0
        )
    else:
        tme.email_completion = 0

    if "task_send_error_email" in form:
        tme.email_error = form["task_send_error_email"]

        tme.email_error_recipients = (
            form["errorEmailRecip"] if "errorEmailRecip" in form else ""
        )

        tme.email_error_message = (
            form["errorEmailMsg"] if "errorEmailMsg" in form else ""
        )
    else:
        tme.email_error = 0

    tme.enabled = form["task-ooff"] if "task-ooff" in form else 0

    db.session.add(tme)
    db.session.commit()

    log = TaskLog(
        task_id=tme.id,
        status_id=7,
        message=session.get("user_full_name") + ": Task edited.",
    )
    db.session.add(log)
    db.session.commit()

    if tme.enabled == 1:
        log = TaskLog(
            task_id=tme.id,
            status_id=7,
            message=session.get("user_full_name") + ": Task enabled.",
        )
        db.session.add(log)
        db.session.commit()

        try:
            requests.get(app.config["SCHEUDULER_HOST"] + "/add/" + str(tme.id))
        # pylint: disable=broad-except
        except BaseException as e:
            log = TaskLog(
                status_id=7,
                error=1,
                task_id=task_id,
                message=(
                    session.get("user_full_name")
                    + ": Failed to add job to scheduler. ("
                    + str(tme.id)
                    + ")\n"
                    + str(e)
                ),
            )
            db.session.add(log)
            db.session.commit()

    else:
        try:
            requests.get(app.config["SCHEUDULER_HOST"] + "/delete/" + str(tme.id))
        # pylint: disable=broad-except
        except BaseException as e:
            log = TaskLog(
                status_id=7,
                error=1,
                task_id=task_id,
                message=(
                    session.get("user_full_name")
                    + ": Failed to delete job from scheduler. ("
                    + str(tme.id)
                    + ")\n"
                    + str(e)
                ),
            )
            db.session.add(log)
            db.session.commit()

    return redirect(url_for("task_bp.get_task", task_id=task_id))


@task_bp.route("/task/<task_id>/run")
@ldap.login_required
@ldap.group_required(["Analytics"])
def run_task_now(task_id):
    """Run a task.

    :url: /task/<task_id>/run
    :param task_id: id of task

    :returns: redirect to task details page.
    """
    task = Task.query.filter_by(id=task_id).first()
    if task:
        try:
            requests.get(app.config["SCHEUDULER_HOST"] + "/run/" + str(task_id))
            log = TaskLog(
                task_id=task.id,
                status_id=7,
                message=session.get("user_full_name") + ": Task manually run.",
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
                    session.get("user_full_name")
                    + ": Failed to manually run task. ("
                    + task_id
                    + ")\n"
                    + str(e)
                ),
            )
            db.session.add(log)
            db.session.commit()

    return redirect(url_for("task_bp.get_task", task_id=task_id))


@task_bp.route("/task/<task_id>/schedule")
@ldap.login_required
@ldap.group_required(["Analytics"])
def schedule_task(task_id):
    """Add a task to scheduler.

    :url: /task/<task_id>/schedule
    :param task_id: id of task

    :returns: redirect to task details page.
    """
    try:
        requests.get(app.config["SCHEUDULER_HOST"] + "/add/" + str(task_id))

        log = TaskLog(
            task_id=task_id,
            status_id=7,
            message=session.get("user_full_name") + ": Task scheduled.",
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
                session.get("user_full_name")
                + ": Failed to schedule task. ("
                + task_id
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()

    return redirect(url_for("task_bp.get_task", task_id=task_id))


@task_bp.route("/task/<task_id>/enable")
@ldap.login_required
@ldap.group_required(["Analytics"])
def enable_task(task_id):
    """Enable a task.

    :url: /task/<task_id>/enable
    :param task_id: id of task

    :returns: redirect to task details page.
    """
    task = Task.query.filter_by(id=task_id).first()
    task.enabled = 1
    db.session.commit()

    log = TaskLog(
        task_id=task_id,
        status_id=7,
        message=session.get("user_full_name") + ": Task enabled.",
    )
    db.session.add(log)
    db.session.commit()

    try:
        requests.get(app.config["SCHEUDULER_HOST"] + "/add/" + str(task_id))
        log = TaskLog(
            task_id=task_id,
            status_id=7,
            message=session.get("user_full_name") + ": Task scheduled.",
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
                session.get("user_full_name")
                + ": Failed to schedule task. ("
                + task_id
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()

    return redirect(url_for("task_bp.get_task", task_id=task_id))


@task_bp.route("/task/<task_id>/disable")
@ldap.login_required
@ldap.group_required(["Analytics"])
def disable_task(task_id):
    """Disable a task.

    :url: /task/<task_id>/disable
    :param task_id: id of task

    :returns: redirect to task details page.
    """
    try:
        requests.get(app.config["SCHEUDULER_HOST"] + "/delete/" + str(task_id))

        task = Task.query.filter_by(id=task_id).first()
        task.enabled = 0
        task.next_run = None
        db.session.commit()

        log = TaskLog(
            task_id=task_id,
            status_id=7,
            message=session.get("user_full_name") + ": Task disabled.",
        )
        db.session.add(log)
        db.session.commit()

    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            error=1,
            message=(
                session.get("user_full_name")
                + ": Failed to disable task. ("
                + task_id
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()

    return redirect(url_for("task_bp.get_task", task_id=task_id))


@task_bp.route("/task/<task_id>/log/<run_id>")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task_run(task_id, run_id):
    """Get task run details.

    :url: /task/<task_id>/log/<run_id>
    :param task_id: id of task owning the tasklog
    :param run_id: id of the run

    :returns: html of run details
    """
    task = Task.query.filter_by(id=task_id).first()

    if task:
        return render_template(
            "pages/task/runDetails.html.j2",
            run=run_id,
            t=task,
            title=run_id,
        )

    return render_template("pages/task/runDetails.html.j2", invalid=True, title="Error")


@task_bp.route("/task/<task_id>/file/<file_id>/sendSftp")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task_file_send_sftp(task_id, file_id):
    """Reload task SFTP output.

    :url: /task/<task_id>/file/<run_id>/<file_id>/sendSftp
    :param task_id: id of task owning the tasklog
    :param run_id: id of the run
    :param file_id: id of file to load

    :returns: redirect to task details.
    """
    try:
        run_id = TaskFile.query.filter_by(id=file_id).first().job_id
        requests.get(
            app.config["RUNNER_HOST"]
            + "/send_sftp/"
            + task_id
            + "/"
            + run_id
            + "/"
            + file_id
        )
        task = Task.query.filter_by(id=task_id).first()

        log = TaskLog(
            task_id=task.id,
            job_id=run_id,
            status_id=7,
            message="("
            + session.get("user_full_name")
            + ") Manually sending file to SFTP server: "
            + task.destination_sftp_conn.path
            + file_id,
        )
        db.session.add(log)
        db.session.commit()

    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            task_id=task_id,
            job_id=run_id,
            error=1,
            message=(
                session.get("user_full_name")
                + ": Failed to send file to SFTP server. ("
                + task_id
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()

    return redirect(url_for("task_bp.get_task", task_id=task_id))


@task_bp.route("/task/<task_id>/file/<file_id>/sendFtp")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task_file_send_ftp(task_id, file_id):
    """Reload task FTP output.

    :url: /task/<task_id>/file/<run_id>/<file_id>/sendFtp
    :param task_id: id of task owning the tasklog
    :param run_id: id of the run
    :param file_id: id of file to load

    :returns: redirect to task details.
    """
    try:
        run_id = TaskFile.query.filter_by(id=file_id).first().job_id
        requests.get(
            app.config["RUNNER_HOST"]
            + "/send_ftp/"
            + task_id
            + "/"
            + run_id
            + "/"
            + file_id
        )

        task = Task.query.filter_by(id=task_id).first()

        log = TaskLog(
            task_id=task.id,
            job_id=run_id,
            status_id=7,
            message="("
            + session.get("user_full_name")
            + ") Manually sending file to FTP server: "
            + task.destination_ftp_conn.path
            + "/"
            + file_id,
        )
        db.session.add(log)
        db.session.commit()

    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            task_id=task_id,
            job_id=run_id,
            error=1,
            message=(
                session.get("user_full_name")
                + ": Failed to send file to FTP server. ("
                + task_id
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()

    return redirect(url_for("task_bp.get_task", task_id=task_id))


@task_bp.route("/task/<task_id>/file/<file_id>/sendSmb")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task_file_send_smb(task_id, file_id):
    """Reload task SMB output.

    :url: /task/<task_id>/file/<run_id>/<file_id>/sendSmb
    :param task_id: id of task owning the tasklog
        run_id: id of the run
        file_id: id of file to load

    :returns: redirect to task details.
    """
    try:
        run_id = TaskFile.query.filter_by(id=file_id).first().job_id
        requests.get(
            app.config["RUNNER_HOST"]
            + "/send_smb/"
            + task_id
            + "/"
            + run_id
            + "/"
            + file_id
        )

        task = Task.query.filter_by(id=task_id).first()

        log = TaskLog(
            task_id=task.id,
            job_id=run_id,
            status_id=7,
            message="("
            + session.get("user_full_name")
            + ") Manually sending file to SMB server: "
            + task.destination_smb_conn.path
            + "/"
            + file_id,
        )
        db.session.add(log)
        db.session.commit()
    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            task_id=task_id,
            job_id=run_id,
            error=1,
            message=(
                session.get("user_full_name")
                + ": Failed to send file to SMB server. ("
                + task_id
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()

    return redirect(url_for("task_bp.get_task", task_id=task_id))


@task_bp.route("/task/<task_id>/file/<file_id>/sendEmail")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task_file_send_email(task_id, file_id):
    """Resend task email output.

    :url: /task/<task_id>/file/<run_id>/<file_id>/sendEmail
    :param task_id: id of task owning the tasklog
    :param run_id: id of the run
    :param file_id: id of file to load

    :returns: redirect to task details.
    """
    try:
        run_id = TaskFile.query.filter_by(id=file_id).first().job_id
        requests.get(
            app.config["RUNNER_HOST"]
            + "/send_email/"
            + task_id
            + "/"
            + run_id
            + "/"
            + file_id
        )

        task = Task.query.filter_by(id=task_id).first()

        log = TaskLog(
            task_id=task.id,
            job_id=run_id,
            status_id=7,
            message="("
            + session.get("user_full_name")
            + ") Manually sending email with file: "
            + file_id,
        )
        db.session.add(log)
        db.session.commit()
    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            task_id=task_id,
            job_id=run_id,
            error=1,
            message=(
                session.get("user_full_name")
                + ": Failed to send email with file. ("
                + task_id
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()

    return redirect(url_for("task_bp.get_task", task_id=task_id))


@task_bp.route("/file/<file_id>")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task_file_download(file_id):
    """Download task backup file.

    :url: /task/<task_id>/file/<run_id>/<file_id>/download
    :param task_id: id of task owning the tasklog
    :param run_id: id of the run
    :param file_id: id of file to load

    :returns: redirect to task details.
    """
    my_file = TaskFile.query.filter_by(id=file_id)

    if my_file.count() > 0:
        my_file = my_file.first()
        log = TaskLog(
            task_id=my_file.task_id,
            job_id=my_file.job_id,
            status_id=7,
            message=(
                "(%s) Manually downloading file. %s"
                % (session.get("user_full_name"), file_id)
            ),
        )
        db.session.add(log)
        db.session.commit()

        source_file = json.loads(
            requests.get("%s/file/%s" % (app.config["RUNNER_HOST"], file_id)).text
        ).get("message")

        file_handle = open(source_file, "r")  # noqa:SIM115

        def stream_and_remove_file():
            yield from file_handle
            os.remove(source_file)

        return Response(
            stream_and_remove_file(),
            mimetype="text",
            headers={"Content-disposition": "attachment; filename=" + my_file.name},
        )

    return jsonify({"error": "no such file."})


@task_bp.route("/task/<task_id>/runlog/<run_id>")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task_run_log(task_id, run_id):
    """Build json dataset for ajax tables of tasklog.

    :url: /task/<task_id>/runlog/<run_id>
    :param task_id: id of task
    :param run_id: id of run

    :returns: json for ajax table.
    """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status Date.asc", type=str)
    split_sort = sort.split(".")

    page = page - 1

    cols = {
        "Status Id": "task_status.id",
        "Status": "task_status.name",
        "Status Date": "task_log.status_date",
        "Message": "task_log.message",
        "Error": "task_log.error",
    }

    logs = (
        db.session.query()
        .select_from(TaskLog)
        .join(Task, Task.id == TaskLog.task_id)
        .outerjoin(TaskStatus, TaskStatus.id == TaskLog.status_id)
        .filter(and_(Task.id == task_id, TaskLog.job_id == run_id))
        .add_columns(*cols.values())
        .order_by(text(cols[split_sort[0]] + " " + split_sort[1]))
    )

    me = [{"head": '["Status", "Status Date", "Message"]'}]

    me.append({"total": logs.count() or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No log messages."})

    for log in logs.limit(10).offset(page * 10).all():

        log = dict(zip(cols.keys(), log))

        me.append(
            {
                "Status Date": datetime.datetime.strftime(
                    log["Status Date"],
                    "%a, %b %-d, %Y %H:%M:%S.%f",
                )
                if log["Status Date"]
                else "None",
                "Status": log["Status"] if log["Status"] else "None",
                "Message": html.escape(log["Message"]),
                "class": "error" if log["Status Id"] == 2 or log["Error"] == 1 else "",
            }
        )

    return jsonify(me)


@task_bp.route("/task/sftp-dest")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_sftp_dest():
    """Template to add sftp destination to a task.

    :url: /task/sftp-dest
    :returns: html page.
    """
    org = request.args.get("org", default=1, type=int)
    dest = (
        ConnectionSftp.query.filter_by(connection_id=org)
        .order_by(ConnectionSftp.name)
        .all()
    )
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/dest/sftp_dest.html.j2",
        org=org,
        sftp_dest=dest,
        title="Connections",
    )


@task_bp.route("/task/sftp-source")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_sftp_source():
    """Template to add sftp source to a task.

    :url: /task/sftp-source
    :returns: html page.
    """
    org = request.args.get("org", default=1, type=int)
    dest = (
        ConnectionSftp.query.filter_by(connection_id=org)
        .order_by(ConnectionSftp.name)
        .all()
    )
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/source/sftp_source.html.j2",
        org=org,
        sftp_source=dest,
        title="Connections",
    )


@task_bp.route("/task/ssh-source")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_ssh_source():
    """Template to add ssh source to a task.

    :url: /task/ssh-source
    :returns: html page.
    """
    org = request.args.get("org", default=1, type=int)
    dest = (
        ConnectionSsh.query.filter_by(connection_id=org)
        .order_by(ConnectionSsh.name)
        .all()
    )
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/source/ssh_source.html.j2",
        org=org,
        ssh_source=dest,
        title="Connections",
    )


@task_bp.route("/task/sftp-query")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_sftp_query():
    """Template to add sftp query source to a task.

    :url: /task/sftp-query
    :returns: html page.
    """
    org = request.args.get("org", default=1, type=int)
    dest = (
        ConnectionSftp.query.filter_by(connection_id=org)
        .order_by(ConnectionSftp.name)
        .all()
    )
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/query/sftp_query.html.j2",
        org=org,
        sftp_query=dest,
        title="Connections",
    )


@task_bp.route("/task/sftp-processing")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_sftp_processing():
    """Template to add sftp processing source to a task.

    :url: /task/sftp-processing
    :returns: html page.
    """
    org = request.args.get("org", default=1, type=int)
    dest = (
        ConnectionSftp.query.filter_by(connection_id=org)
        .order_by(ConnectionSftp.name)
        .all()
    )

    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/processing/sftp_processing.html.j2",
        org=org,
        sftp_processing=dest,
        title="Connections",
    )


@task_bp.route("/task/ftp-dest")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_ftp_dest():
    """Template to add ftp destination to a task.

    :url: /task/ftp-dest
    :returns: html page.
    """
    org = request.args.get("org", default=1, type=int)
    dest = (
        ConnectionFtp.query.filter_by(connection_id=org)
        .order_by(ConnectionFtp.name)
        .all()
    )
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/dest/ftp_dest.html.j2", org=org, ftp_dest=dest, title="Connections"
    )


@task_bp.route("/task/ftp-source")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_ftp_source():
    """Template to add ftp source to a task.

    :url: /task/ftp-source
    :returns: html page.
    """
    org = request.args.get("org", default=1, type=int)
    dest = (
        ConnectionFtp.query.filter_by(connection_id=org)
        .order_by(ConnectionFtp.name)
        .all()
    )
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/source/ftp_source.html.j2",
        org=org,
        ftp_source=dest,
        title="Connections",
    )


@task_bp.route("/task/ftp-processing")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_ftp_processing():
    """Template to add ftp processing source to a task.

    :url: /task/ftp-processing
    :returns: html page.
    """
    org = request.args.get("org", default=1, type=int)
    dest = (
        ConnectionFtp.query.filter_by(connection_id=org)
        .order_by(ConnectionFtp.name)
        .all()
    )
    org = Connection.query.filter_by(id=org).first()
    return render_template(
        "pages/task/processing/ftp_processing.html.j2",
        org=org,
        ftp_processing=dest,
        title="Connections",
    )


@task_bp.route("/task/ftp-query")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_ftp_query():
    """Template to add ftp query source to a task.

    :url: /task/ftp-query
    :returns: html page.
    """
    org = request.args.get("org", default=1, type=int)
    dest = (
        ConnectionFtp.query.filter_by(connection_id=org)
        .order_by(ConnectionFtp.name)
        .all()
    )
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/query/ftp_query.html.j2",
        org=org,
        ftp_query=dest,
        title="Connections",
    )


@task_bp.route("/task/smb-source")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_smb_source():
    """Template to add smb source to a task.

    :url: /task/smb-source
    :returns: html page.
    """
    org = request.args.get("org", default=1, type=int)
    dest = (
        ConnectionSmb.query.filter_by(connection_id=org)
        .order_by(ConnectionSmb.name)
        .all()
    )
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/source/smb_source.html.j2",
        org=org,
        smb_source=dest,
        title="Connections",
    )


@task_bp.route("/task/smb-dest")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_smb_dest():
    """Template to add smb destination to a task.

    :url: /task/smb-dest
    :returns: html page.
    """
    org = request.args.get("org", default=1, type=int)
    dest = (
        ConnectionSmb.query.filter_by(connection_id=org)
        .order_by(ConnectionSmb.name)
        .all()
    )
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/dest/smb_dest.html.j2", org=org, smb_dest=dest, title="Connections"
    )


@task_bp.route("/task/smb-query")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_smb_query():
    """Template to add smb query source to a task.

    :url: /task/smb-query
    :returns: html page.
    """
    org = request.args.get("org", default=1, type=int)
    query = (
        ConnectionSmb.query.filter_by(connection_id=org)
        .order_by(ConnectionSmb.name)
        .all()
    )
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/query/smb_query.html.j2",
        org=org,
        smb_query=query,
        title="Connections",
    )


@task_bp.route("/task/smb-processing")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_smb_processing():
    """Template to add smb processing source to a task.

    :url: /task/smb-processing
    :returns: html page.
    """
    org = request.args.get("org", default=1, type=int)
    processing = (
        ConnectionSmb.query.filter_by(connection_id=org)
        .order_by(ConnectionSmb.name)
        .all()
    )
    org = Connection.query.filter_by(id=org).first()

    return render_template(
        "pages/task/processing/smb_processing.html.j2",
        org=org,
        smb_processing=processing,
        title="Connections",
    )


@task_bp.route("/task/database-source")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_database_source():
    """Template to add database source to a task.

    :url: /task/database-source
    :returns: html page.
    """
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


@task_bp.route("/task/<task_id>/reset")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_reset(task_id):
    """Reset a task status to completed.

    :url: /task/<task_id>/reset
    :param task_id: id of task to reset

    :returns: redirects to task details.
    """
    task = Task.query.filter_by(id=task_id).first()
    task.status_id = 4
    db.session.commit()

    log = TaskLog(
        task_id=task.id,
        status_id=7,
        message=session.get("user_full_name") + ": Reset task status to completed.",
    )
    db.session.add(log)
    db.session.commit()

    return redirect(url_for("task_bp.get_task", task_id=task_id))
