"""
    webapp view for tasks

    Extract Management 2.0
    Copyright (C) 2020  Riverside Healthcare, Kankakee, IL

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

import time
import datetime
import hashlib
import tempfile
import os
from pathlib import Path
from flask import request, render_template, redirect, url_for, jsonify, g, Response

from jinja2 import Environment, PackageLoader, select_autoescape

from em import app, ldap, db
from ..model.model import (
    TaskSourceType,
    TaskSourceQueryType,
    Project,
    QuoteLevel,
    TaskLog,
    Connection,
    ConnectionSftp,
    ConnectionFtp,
    ConnectionSmb,
    ConnectionDatabase,
    TaskDestinationFileType,
    TaskProcessingType,
    Task,
    User,
)
from ..scripts.runner import Runner
from ..scripts.crypto import em_encrypt
from ..scripts.source_code import SourceCode
from ..scripts.smb import Smb
from ..scripts.sftp import Sftp
from ..scripts.ftp import Ftp
from ..scripts.smtp import Smtp
from .filters import datetime_format

env = Environment(
    loader=PackageLoader("em", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)

env.filters["datetime_format"] = datetime_format


@app.route("/task/<my_id>/duplicate")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_duplicate(my_id):
    whoami = User.query.filter_by(user_id=g.user_id).first()
    my_task = Task.query.filter_by(id=my_id).first()

    new_task = Task()

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
        l=datetime.datetime.strftime(new_task.last_run, "%a, %b %-d, %Y %H:%M:%S")
        if new_task.last_run
        else "Never",
        title=new_task.name,
    )


@app.route("/task/<my_id>/delete")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_delete(my_id):
    """ delete a task """
    task = Task.query.filter_by(id=my_id).first()
    project = task.project if task else None

    jobs = app.apscheduler.get_jobs()
    for job in jobs:
        if str(job.args[0]) == str(task.id):
            job.remove()

    TaskLog.query.filter_by(task_id=my_id).delete()
    db.session.commit()
    Task.query.filter_by(id=my_id).delete()
    db.session.commit()

    log = TaskLog(
        status_id=7, message=g.user_full_name + ": Task deleted. (" + my_id + ")"
    )
    db.session.add(log)
    db.session.commit()

    if project:
        return redirect(url_for("project_get", my_id=project.id))
    return redirect(url_for("dash"))


@app.route("/job/<my_id>/delete")
@ldap.login_required
@ldap.group_required(["Analytics"])
def job_delete(my_id):
    """ delete a job from scheduler """
    app.apscheduler.get_job(my_id).remove()

    log = TaskLog(
        task_id=my_id, status_id=7, message=g.user_full_name + ": Orphan job deleted."
    )
    db.session.add(log)
    db.session.commit()

    return redirect(url_for("dash"))


@app.route("/task")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_all():
    """ view for all tasks """
    me = Task.query.all()
    if len(me) < 1:
        return redirect(url_for("project"))
    return render_template("pages/task/all.html.j2", title="Tasks")


@app.route("/task/mine")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_mine():
    """ view for must my tasks """
    me = (
        Task.query.join(Project)
        .join(User, User.id == Project.owner_id)
        .filter(User.user_id == g.user_id)
        .all()
    )
    if len(me) < 1:
        return redirect(url_for("project"))
    return render_template(
        "pages/task/all.html.j2", mine=g.user_full_name, title="My Tasks"
    )


@app.route("/task/user/<my_user_id>")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_user(my_user_id):
    """ view for must my tasks """
    me = (
        Task.query.join(Project)
        .join(User, User.id == Project.owner_id)
        .filter(User.id == my_user_id)
        .all()
    )
    my_user = User.query.filter_by(id=my_user_id).first()

    if len(me) < 1:
        return redirect(url_for("project"))
    return render_template(
        "pages/task/all.html.j2",
        mine=my_user.full_name,
        title="My Tasks",
        user_id=my_user_id,
    )


@app.route("/task/<my_type>/list")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_list(my_type):
    """ return table of tasks """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Name.desc", type=str)
    split_sort = sort.split(".")

    page -= 1

    if my_type == "all":
        tasks = Task.query.all()
    elif my_type.isdigit():
        tasks = (
            Task.query.join(Project)
            .join(User, User.id == Project.owner_id)
            .filter(User.id == int(my_type))
            .all()
        )

    else:
        tasks = (
            Task.query.join(Project)
            .join(User, User.id == Project.owner_id)
            .filter(User.user_id == g.user_id)
            .all()
        )

    head = [
        "Name",
        "Project",
        "Enabled",
        "Last Active",
        "Run Now",
        "Status",
        "Next Run Date",
    ]

    me = [{"head": str(head)}]
    table = []

    [
        table.append(
            {
                "Name": '<a class="em-link" href="/task/'
                + str(task.id)
                + '">'
                + task.name
                + "</a>",
                "Project": '<a class="em-link" href="/project/'
                + str(task.project.id)
                + '">'
                + task.project.name
                + "</a>"
                if task.project
                else "Orphan :'(",
                "Enabled": "<a class='em-link' href=/task/"
                + str(task.id)
                + "/disable>Disable</a>"
                if task.enabled == 1
                else "<a class='em-link' href=/task/"
                + str(task.id)
                + "/enable>Enable</a>",
                "Last Active": datetime.datetime.strftime(
                    task.last_run, "%a, %b %-d, %Y %H:%M:%S"
                )
                if task.last_run
                else "Never",
                "Run Now": "<a class='em-link' href='/task/"
                + str(task.id)
                + "/run'>Run Now</a>",
                "Status": task.status.name if task.status_id else "None",
                "Next Run Date": "Error: Task must be <a class='em-link' href='/task/"
                + str(task.id)
                + "/schedule'>rescheduled</a> to run."
                if (
                    len(
                        [
                            job.next_run_time
                            for job in app.apscheduler.get_jobs()
                            if str(job.args[0]) == str(task.id)
                            and job.next_run_time is not None
                        ]
                        or []
                    )
                    == 0
                    and task.enabled == 1
                )
                else (
                    datetime.datetime.strftime(
                        min(
                            [
                                job.next_run_time
                                for job in app.apscheduler.get_jobs()
                                if str(job.args[0]) == str(task.id)
                                and job.next_run_time is not None
                            ]
                        ),
                        "%a, %b %-d, %Y %H:%M:%S",
                    )
                    if [
                        job.next_run_time
                        for job in app.apscheduler.get_jobs()
                        if str(job.args[0]) == str(task.id)
                        and job.next_run_time is not None
                    ]
                    else "None"
                ),
                "class": "error"
                if task.status_id == 2
                or (
                    len(
                        [
                            job.next_run_time
                            for job in app.apscheduler.get_jobs()
                            if str(job.args[0]) == str(task.id)
                            and job.next_run_time is not None
                        ]
                        or []
                    )
                    == 0
                    and task.enabled == 1
                )
                else "",
            }
        )
        for task in tasks
    ]

    table = (
        sorted(table, key=lambda k: k[split_sort[0]])
        if split_sort[1] == "desc"
        else sorted(table, key=lambda k: k[split_sort[0]], reverse=True)
    )
    [me.append(s) for s in table[page * 10 : page * 10 + 10]]

    me.append({"total": len(table) or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page

    return jsonify(me)


@app.route("/project/<my_id>/task")
@ldap.login_required
@ldap.group_required(["Analytics"])
def project_task_all(my_id):
    """ return table of all tasks for a project """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status.desc", type=str)
    split_sort = sort.split(".")

    page -= 1

    tasks = Task.query.filter_by(project_id=my_id).all()

    head = [
        "Name",
        "Enabled",
        "Last Active",
        "Run Now",
        "Status",
        "Next Run Date",
    ]

    me = [{"head": str(head)}]
    table = []

    [
        table.append(
            {
                "Name": '<a class="em-link" href="/task/'
                + str(task.id)
                + '">'
                + task.name
                + "</a>",
                "Enabled": "<a class='em-link' href=/task/"
                + str(task.id)
                + "/disable>Disable</a>"
                if task.enabled == 1
                else "<a class='em-link' href=/task/"
                + str(task.id)
                + "/enable>Enable</a>",
                "Last Active": datetime.datetime.strftime(
                    task.last_run, "%a, %b %-d, %Y %H:%M:%S"
                )
                if task.last_run
                else "Never",
                "Run Now": "<a class='em-link' href='/task/"
                + str(task.id)
                + "/run'>Run Now</a>",
                "Status": task.status.name if task.status_id else "None",
                "Next Run Date": "Error: Task must be <a class='em-link' href='/task/"
                + str(task.id)
                + "/schedule'>rescheduled</a> to run."
                if (
                    len(
                        [
                            job.next_run_time
                            for job in app.apscheduler.get_jobs()
                            if str(job.args[0]) == str(task.id)
                            and job.next_run_time is not None
                        ]
                        or []
                    )
                    == 0
                    and task.enabled == 1
                )
                else (
                    datetime.datetime.strftime(
                        min(
                            [
                                job.next_run_time
                                for job in app.apscheduler.get_jobs()
                                if str(job.args[0]) == str(task.id)
                                and job.next_run_time is not None
                            ]
                        ),
                        "%a, %b %-d, %Y %H:%M:%S",
                    )
                    if [
                        job.next_run_time
                        for job in app.apscheduler.get_jobs()
                        if str(job.args[0]) == str(task.id)
                        and job.next_run_time is not None
                    ]
                    else "None"
                ),
                "class": "error"
                if task.status_id == 2
                or (
                    len(
                        [
                            job.next_run_time
                            for job in app.apscheduler.get_jobs()
                            if str(job.args[0]) == str(task.id)
                            and job.next_run_time is not None
                        ]
                        or []
                    )
                    == 0
                    and task.enabled == 1
                )
                else "",
            }
        )
        for task in tasks
    ]

    table = (
        sorted(table, key=lambda k: k[split_sort[0]])
        if split_sort[1] == "desc"
        else sorted(table, key=lambda k: k[split_sort[0]], reverse=True)
    )
    [me.append(s) for s in table[page * 10 : page * 10 + 10]]

    me.append({"total": len(table) or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page

    return jsonify(me)


@app.route("/project/<my_id>/tasklog")
@ldap.login_required
@ldap.group_required(["Analytics"])
def project_task_log_all(my_id):
    """ return table of projects' task log """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status Date.asc", type=str)
    split_sort = sort.split(".")

    page -= 1

    logs = (
        TaskLog.query.join(Task)
        .filter(Task.project_id == my_id)
        .order_by(TaskLog.status_date)
        .all()
    )

    head = ["Task Name", "Run Id", "Status", "Status Date", "Message"]

    me = [{"head": str(head)}]
    table = []

    [
        table.append(
            {
                "Task Name": '<a class="em-link" href="/task/'
                + str(log.task.id)
                + '">'
                + log.task.name
                + "</a>",
                "Run Id": (
                    "<a class='em-link' href='/task/"
                    + str(log.task.id)
                    + "/log/"
                    + str(log.job_id)
                    + "'>"
                    + str(log.job_id)
                    + "</a>"
                    if log.job_id
                    else ""
                ),
                "Status Date": datetime.datetime.strftime(
                    log.status_date,
                    "%a, %b %-d, %Y %H:%M:%S.%f",
                )
                if log.status_date
                else "None",
                "Status": log.status.name if log.status else "None",
                "Message": log.message,
                "class": "error" if log.status_id == 2 or log.error == 1 else "",
            }
        )
        for log in logs
    ]

    table = (
        sorted(table, key=lambda k: k[split_sort[0]])
        if split_sort[1] == "desc"
        else sorted(table, key=lambda k: k[split_sort[0]], reverse=True)
    )

    [me.append(s) for s in table[page * 10 : page * 10 + 10]]

    me.append({"total": len(table) or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No log messages."})

    return jsonify(me)


@app.route("/project/<my_id>/task/new", methods=["GET", "POST"])
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_new(my_id):
    """ add a new task """
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
            p=Project.query.filter_by(id=my_id).first(),
            source_type=source_type,
            source_query_type=source_query_type,
            processing_type=processing_type,
            quote_level=quote_level,
            source=source,
            conn=conn,
            title="New Task",
            t=Task.query.filter(1 == 2).first(),
            file_type=file_type,
        )

    # create tasks
    form = request.form

    tme = Task(name=form["name"].strip())
    tme.project_id = my_id

    whoami = User.query.filter_by(user_id=g.user_id).first()

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
        task_id=tme.id, status_id=7, message=g.user_full_name + ": Task created."
    )
    db.session.add(log)
    db.session.commit()

    if tme.enabled == 1:
        log = TaskLog(
            task_id=tme.id, status_id=7, message=g.user_full_name + ": Task enabled."
        )
        db.session.add(log)
        db.session.commit()

        add_task_to_engine(tme.id)

    return redirect(url_for("project_get", my_id=my_id))


@app.route("/project/<my_id>/task/disable")
@ldap.login_required
@ldap.group_required(["Analytics"])
def disable_all_project_tasks(my_id):
    """ disables all tasks for a given project """
    tasks = Task.query.filter_by(project_id=my_id).all()
    for task in tasks:
        task.enabled = 0
        db.session.commit()

        log = TaskLog(
            task_id=task.id, status_id=7, message=g.user_full_name + ": Task disabled."
        )
        db.session.add(log)
        db.session.commit()

        jobs = app.apscheduler.get_jobs()
        for job in jobs:

            if str(job.args[0]) == str(my_id):
                job.remove()

    return redirect(url_for("project_get", my_id=my_id))


@app.route("/project/<my_id>/task/enable")
@ldap.login_required
@ldap.group_required(["Analytics"])
def enable_all_project_tasks(my_id):
    """ enable all tasks for a given project """
    tasks = Task.query.filter_by(project_id=my_id).all()
    for task in tasks:

        log = TaskLog(
            task_id=task.id, status_id=7, message=g.user_full_name + ": Task enabled."
        )
        db.session.add(log)
        db.session.commit()

        add_task_to_engine(task.id)

    return redirect(url_for("project_get", my_id=my_id))


@app.route("/project/<my_id>/task/run")
@ldap.login_required
@ldap.group_required(["Analytics"])
def run_all_project_tasks(my_id):
    """ run all tasks for a given project now """
    tasks = Task.query.filter_by(project_id=my_id).all()
    for task in tasks:
        log = TaskLog(
            task_id=task.id,
            status_id=7,
            message=g.user_full_name + ": Task manually run.",
        )
        db.session.add(log)
        db.session.commit()

        my_hash = hashlib.sha256()
        my_hash.update(str(time.time() * 1000).encode("utf-8"))

        app.apscheduler.add_job(
            func=Runner,
            trigger="date",
            run_date=datetime.datetime.now(),
            args=[
                str(task.id),
                #   str(job.project.id) + "-" + str(job.id) + "-" + hash.hexdigest()[:10],
            ],
            id=str(task.project.id)
            + "-"
            + str(task.id)
            + "-"
            + my_hash.hexdigest()[:10],
            name="(one off - manual run) project: "
            + task.project.name
            + " task: "
            + task.name,
        )

    return redirect(url_for("project_get", my_id=my_id))


@app.route("/task/<my_id>")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task(my_id):
    """ get details for a task """
    task = Task.query.filter_by(id=my_id).first()
    run = None
    jobs = app.apscheduler.get_jobs()

    for job in jobs:
        if str(job.args[0]) == str(my_id) and job.next_run_time is not None:
            run = min(run or job.next_run_time, job.next_run_time)
    if task:
        return render_template(
            "pages/task/details.html.j2",
            t=task,
            r=datetime.datetime.strftime(run, "%a, %b %-d, %Y %H:%M:%S")
            if run
            else "None",
            l=datetime.datetime.strftime(task.last_run, "%a, %b %-d, %Y %H:%M:%S")
            if task.last_run
            else "Never",
            title=task.name,
        )

    return render_template("pages/task/details.html.j2", invalid=True, title="Error")


@app.route("/task/<my_id>/edit", methods=["GET"])
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_edit_get(my_id):
    """ open task editor form """
    me = Task.query.filter_by(id=my_id).first()

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


@app.route("/task/<my_id>/git")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_get_git_code(my_id):
    """ get the remote code for viewing """
    task = Task.query.filter_by(id=my_id).first()

    return render_template(
        "pages/task/code.html.j2", code=SourceCode(task, task.source_git).gitlab()
    )


@app.route("/task/<my_id>/url")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_get_url_code(my_id):
    """ get the remote code for viewing """
    task = Task.query.filter_by(id=my_id).first()

    return render_template(
        "pages/task/code.html.j2", code=SourceCode(task, task.source_url).web_url()
    )


@app.route("/task/<my_id>/processing_git")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_get_processing_git_code(my_id):
    """ get the remote code for viewing """
    task = Task.query.filter_by(id=my_id).first()

    return render_template(
        "pages/task/code.html.j2", code=SourceCode(task, task.processing_git).gitlab()
    )


@app.route("/task/<my_id>/processing_url")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_get_processing_url_code(my_id):
    """ get the remote code for viewing """
    task = Task.query.filter_by(id=my_id).first()

    return render_template(
        "pages/task/code.html.j2", code=SourceCode(task, task.processing_url).web_url()
    )


@app.route("/task/<my_id>/edit", methods=["POST"])
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_edit_post(my_id):
    """ save task edits """
    # create tasks
    form = request.form
    whoami = User.query.filter_by(user_id=g.user_id).first()

    tme = Task.query.filter_by(id=my_id).first()

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
        task_id=tme.id, status_id=7, message=g.user_full_name + ": Task edited."
    )
    db.session.add(log)
    db.session.commit()

    if tme.enabled == 1:
        log = TaskLog(
            task_id=tme.id, status_id=7, message=g.user_full_name + ": Task enabled."
        )
        db.session.add(log)
        db.session.commit()

        add_task_to_engine(tme.id)
    else:
        jobs = app.apscheduler.get_jobs()
        for j in jobs:
            if str(j.args[0]) == str(tme.id):
                j.remove()

    return redirect(url_for("get_task", my_id=my_id))


@app.route("/task/<my_id>/run")
@ldap.login_required
@ldap.group_required(["Analytics"])
def run_task_now(my_id):
    """ run a speicieid task now """
    task = Task.query.filter_by(id=my_id).first()
    if task:
        log = TaskLog(
            task_id=task.id,
            status_id=7,
            message=g.user_full_name + ": Task manually run.",
        )
        db.session.add(log)
        db.session.commit()

        my_hash = hashlib.sha256()
        my_hash.update(str(time.time()).encode("utf-8"))

        app.apscheduler.add_job(
            func=Runner,
            trigger="date",
            run_date=datetime.datetime.now(),
            args=[
                str(my_id),
                #    str(t.project.id) + "-" + str(t.id) + "-" + hash.hexdigest()[:10],
            ],
            id=str(task.project.id)
            + "-"
            + str(task.id)
            + "-"
            + my_hash.hexdigest()[:10],
            name="(one off - manual run) project: "
            + task.project.name
            + " task: "
            + task.name,
        )

    return redirect(url_for("get_task", my_id=my_id))


@app.route("/task/<my_id>/schedule")
@ldap.login_required
@ldap.group_required(["Analytics"])
def schedule_task(my_id):
    """ add task to scheduler """
    log = TaskLog(
        task_id=my_id, status_id=7, message=g.user_full_name + ": Task scheduled."
    )
    db.session.add(log)
    db.session.commit()

    add_task_to_engine(my_id)

    return redirect(url_for("get_task", my_id=my_id))


@app.route("/task/<my_id>/enable")
@ldap.login_required
@ldap.group_required(["Analytics"])
def enable_task(my_id):
    """ enable task """
    log = TaskLog(
        task_id=my_id, status_id=7, message=g.user_full_name + ": Task scheduled."
    )
    db.session.add(log)
    db.session.commit()

    add_task_to_engine(my_id)

    return redirect(url_for("get_task", my_id=my_id))


@app.route("/task/<my_id>/disable")
@ldap.login_required
@ldap.group_required(["Analytics"])
def disable_task(my_id):
    """ disable task """
    task = Task.query.filter_by(id=my_id).first()
    task.enabled = 0
    db.session.commit()

    log = TaskLog(
        task_id=my_id, status_id=7, message=g.user_full_name + ": Task disabled."
    )
    db.session.add(log)
    db.session.commit()

    jobs = app.apscheduler.get_jobs()
    for job in jobs:
        if str(job.args[0]) == str(my_id):
            job.remove()

    return redirect(url_for("get_task", my_id=my_id))


@app.route("/task/<my_id>/log")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_log(my_id):
    """ return table with task log """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status Date.asc", type=str)
    split_sort = sort.split(".")

    page -= 1

    logs = (
        TaskLog.query.join(Task)
        .filter(Task.id == my_id)
        .order_by(TaskLog.status_date)
        .all()
    )

    head = ["Status", "Run Id", "Status Date", "Message"]

    me = [{"head": str(head)}]
    table = []

    [
        table.append(
            {
                "Status Date": datetime.datetime.strftime(
                    log.status_date,
                    "%a, %b %-d, %Y %H:%M:%S.%f",
                )
                if log.status_date
                else "None",
                "my_date_sort": log.status_date,
                "Run Id": "<a class='em-link' href='/task/"
                + str(log.task.id)
                + "/log/"
                + str(log.job_id)
                + "'>"
                + str(log.job_id)
                + "</a>"
                if log.job_id
                else "",
                "Status": log.status.name if log.status else "None",
                "Message": log.message,
                "class": "error" if log.status_id == 2 or log.error == 1 else "",
            }
        )
        for log in logs
    ]

    table = (
        sorted(
            table, key=lambda k: k[split_sort[0].replace("Status Date", "my_date_sort")]
        )
        if split_sort[1] == "desc"
        else sorted(
            table,
            key=lambda k: k[split_sort[0].replace("Status Date", "my_date_sort")],
            reverse=True,
        )
    )

    [me.append(s) for s in table[page * 10 : page * 10 + 10]]

    me.append({"total": len(table) or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No log messages."})

    return jsonify(me)


@app.route("/task/<my_id>/log/<run_id>")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task_run(my_id, run_id):
    """ return page for a specific task run """
    task = Task.query.filter_by(id=my_id).first()
    run = None
    jobs = app.apscheduler.get_jobs()
    for job in jobs:
        if str(job.args[0]) == str(my_id) and job.next_run_time is not None:
            run = min(run or job.next_run_time, job.next_run_time)
    if task:
        return render_template(
            "pages/task/runDetails.html.j2",
            run=run_id,
            t=task,
            title=run_id,
        )

    return render_template("pages/task/runDetails.html.j2", invalid=True, title="Error")


@app.route("/task/<my_id>/file")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task_files(my_id):
    """ return table with a task run log """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Created.asc", type=str)
    split_sort = sort.split(".")

    page -= 1

    # try to get file listing from smb server
    task = Task.query.filter_by(id=my_id).first()

    try:
        my_files = Smb(
            task, "default", None, "", task.project.name + "/" + task.name + "/"
        ).list_dir()
    except:
        my_files = []

    # get contents of the folders
    to_remove = []
    for folder in my_files:
        if folder.isDirectory == True and folder.filename not in ["..", "."]:

            to_remove.append(folder)

            sub_files = Smb(
                task,
                "default",
                None,
                "",
                task.project.name + "/" + task.name + "/" + folder.filename + "/",
            ).list_dir()

            # update file name with folder
            for file in sub_files:

                if file.isDirectory == False:
                    file.filename = folder.filename + "/" + file.filename

            [my_files.append(x) for x in sub_files if x.isDirectory == False]

    for folder in to_remove:
        my_files.remove(folder)

    head = ["File Name", "Run Id", "Created", "File Size", "Action"]
    me = [{"head": str(head)}]

    table = []

    [
        table.append(
            {
                "File Name": (
                    file.filename.split("/")[1]
                    if len(file.filename.split("/")) > 1
                    else file.filename
                ),
                "Run Id": "<a class='em-link' href='/task/"
                + str(task.id)
                + "/log/"
                + (
                    file.filename.split("/")[0]
                    if len(file.filename.split("/")) > 1
                    else file.filename
                )
                + "'>"
                + (
                    file.filename.split("/")[0]
                    if len(file.filename.split("/")) > 1
                    else file.filename
                )
                + "</a>",
                "Created": datetime.datetime.strftime(
                    datetime.datetime.fromtimestamp(file.create_time),
                    "%a, %b %-d, %Y %H:%M:%S.%f",
                ),
                "File Size": str(file.file_size) + "b",
                "Action": (
                    (
                        "<a href='/task/"
                        + str(task.id)
                        + "/file/"
                        + str(file.filename)
                        + "/sendSftp' class='em-link'>Send to SFTP</a>\n"
                        if task.destination_sftp == 1
                        else ""
                    )
                    + (
                        "<a href='/task/"
                        + str(task.id)
                        + "/file/"
                        + str(file.filename)
                        + "/sendFtp' class='em-link'>Send to FTP</a>\n"
                        if task.destination_ftp == 1
                        else ""
                    )
                    + (
                        "<a href='/task/"
                        + str(task.id)
                        + "/file/"
                        + str(file.filename)
                        + "/sendSmb' class='em-link'>Send to SMB</a>\n"
                        if task.destination_smb == 1
                        else ""
                    )
                    + (
                        "<a href='/task/"
                        + str(task.id)
                        + "/file/"
                        + str(file.filename)
                        + "/sendEmail' class='em-link'>Send to Email</a>\n"
                        if task.email_completion_file == 1
                        else ""
                    )
                    + (
                        "<a href='/task/"
                        + str(task.id)
                        + "/file/"
                        + str(file.filename)
                        + "/download' class='em-link'>Download File</a>\n"
                    )
                ),
                "Created_time": file.create_time,
            }
        )
        for file in my_files
        if file.filename not in [".", ".."]
    ]

    table = (
        sorted(table, key=lambda k: k[split_sort[0].replace("Created", "Created_time")])
        if split_sort[1] == "desc"
        else sorted(
            table,
            key=lambda k: k[split_sort[0].replace("Created", "Created_time")],
            reverse=True,
        )
    )

    [me.append(s) for s in table[page * 10 : page * 10 + 10]]

    me.append({"total": len(table) or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No files available."})
    return jsonify(me)


@app.route("/task/<my_id>/file/<run_id>/<file_id>/sendSftp")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task_file_send_sftp(my_id, run_id, file_id):
    # get task
    task = Task.query.filter_by(id=my_id).first()

    log = TaskLog(
        task_id=task.id,
        job_id=run_id,
        status_id=7,
        message="("
        + g.user_full_name
        + ") Manually sending file to SFTP server: "
        + task.destination_sftp_conn.path
        + file_id,
    )
    db.session.add(log)
    db.session.commit()

    task.last_run_job_id = run_id
    # get file from smb
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
        temp.write(
            Smb(
                task,
                "default",
                None,
                "",
                task.project.name + "/" + task.name + "/" + run_id + "/" + file_id,
            ).read()
        )

    # save file
    Sftp(
        task,
        task.destination_sftp_conn,
        1,
        file_id,
        temp.name,  # is full path
    ).save()
    os.remove(temp.name)

    return redirect(url_for("get_task", my_id=my_id))


@app.route("/task/<my_id>/file/<run_id>/<file_id>/sendFtp")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task_file_send_ftp(my_id, run_id, file_id):
    # get task
    task = Task.query.filter_by(id=my_id).first()

    log = TaskLog(
        task_id=task.id,
        job_id=run_id,
        status_id=7,
        message="("
        + g.user_full_name
        + ") Manually sending file to FTP server: "
        + task.destination_ftp_conn.path
        + "/"
        + file_id,
    )
    db.session.add(log)
    db.session.commit()

    task.last_run_job_id = run_id
    # get file from smb
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
        temp.write(
            Smb(
                task,
                "default",
                None,
                "",
                task.project.name + "/" + task.name + "/" + run_id + "/" + file_id,
            ).read()
        )

    # save file
    Ftp(
        task,
        task.destination_ftp_conn,
        1,
        file_id,
        temp.name,
    ).save()  # is full path
    os.remove(temp.name)

    return redirect(url_for("get_task", my_id=my_id))


@app.route("/task/<my_id>/file/<run_id>/<file_id>/sendSmb")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task_file_send_smb(my_id, run_id, file_id):
    # get task
    task = Task.query.filter_by(id=my_id).first()

    log = TaskLog(
        task_id=task.id,
        job_id=run_id,
        status_id=7,
        message="("
        + g.user_full_name
        + ") Manually sending file to SMB server: "
        + task.destination_smb_conn.path
        + "/"
        + file_id,
    )
    db.session.add(log)
    db.session.commit()

    task.last_run_job_id = run_id
    # get file from smb
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
        temp.write(
            Smb(
                task,
                "default",
                None,
                "",
                task.project.name + "/" + task.name + "/" + run_id + "/" + file_id,
            ).read()
        )

    # save file
    Smb(
        task,
        task.destination_smb_conn,
        1,
        file_id,
        temp.name,
    ).save()  # is full path
    os.remove(temp.name)

    return redirect(url_for("get_task", my_id=my_id))


@app.route("/task/<my_id>/file/<run_id>/<file_id>/sendEmail")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task_file_send_email(my_id, run_id, file_id):
    task = Task.query.filter_by(id=my_id).first()

    log = TaskLog(
        task_id=task.id,
        job_id=run_id,
        status_id=7,
        message="("
        + g.user_full_name
        + ") Manually sending file to completion email: "
        + file_id,
    )
    db.session.add(log)
    db.session.commit()

    task.last_run_job_id = run_id
    date = str(datetime.datetime.now())

    template = env.get_template("email/email.html.j2")

    # get file from smb
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
        temp.write(
            Smb(
                task,
                "default",
                None,
                "",
                task.project.name + "/" + task.name + "/" + run_id + "/" + file_id,
            ).read()
        )

    Smtp(
        task,
        task.email_completion_recipients,
        "(Manual Send) Project: " + task.project.name + " / Task: " + task.name,
        template.render(
            task=task,
            success=1,
            date=date,
            logs=[],
        ),
        temp.name,
        file_id,
    )
    os.remove(temp.name)

    return redirect(url_for("get_task", my_id=my_id))


@app.route("/task/<my_id>/file/<run_id>/<file_id>/download")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task_file_download(my_id, run_id, file_id):
    # get task
    task = Task.query.filter_by(id=my_id).first()

    log = TaskLog(
        task_id=task.id,
        job_id=run_id,
        status_id=7,
        message="(" + g.user_full_name + ") Manually downloading file. " + file_id,
    )
    db.session.add(log)
    db.session.commit()

    task.last_run_job_id = run_id

    return Response(
        Smb(
            task,
            "default",
            None,
            "",
            task.project.name + "/" + task.name + "/" + run_id + "/" + file_id,
        ).read(),
        mimetype="text",
        headers={"Content-disposition": "attachment; filename=" + file_id},
    )


@app.route("/task/<my_id>/runlog/<run_id>")
@ldap.login_required
@ldap.group_required(["Analytics"])
def get_task_run_log(my_id, run_id):
    """ return table with a task run log """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status Date.asc", type=str)
    split_sort = sort.split(".")

    page -= 1

    logs = (
        TaskLog.query.filter_by(job_id=run_id)
        .join(Task)
        .filter(Task.id == my_id)
        .order_by(TaskLog.status_date)
        .all()
    )

    head = ["Status", "Status Date", "Message"]

    me = [{"head": str(head)}]
    table = []

    [
        table.append(
            {
                "Status Date": datetime.datetime.strftime(
                    log.status_date,
                    "%a, %b %-d, %Y %H:%M:%S.%f",
                )
                if log.status_date
                else "None",
                "Status": log.status.name if log.status else "None",
                "Message": log.message,
                "class": "error" if log.status_id == 2 or log.error == 1 else "",
            }
        )
        for log in logs
    ]

    table = (
        sorted(table, key=lambda k: k[split_sort[0]])
        if split_sort[1] == "desc"
        else sorted(table, key=lambda k: k[split_sort[0]], reverse=True)
    )

    [me.append(s) for s in table[page * 10 : page * 10 + 10]]

    me.append({"total": len(table) or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No log messages."})

    return jsonify(me)


@app.route("/task/sftp-dest")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_sftp_dest():
    """ return page to add a task sftp """
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


@app.route("/task/sftp-source")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_sftp_source():
    """ return page to add a task sftp """
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


@app.route("/task/sftp-query")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_sftp_query():
    """ return page to add a task sftp """
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


@app.route("/task/sftp-processing")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_sftp_processing():
    """ return page to add a task sftp """
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


@app.route("/task/ftp-dest")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_ftp_dest():
    """ return page to add a task ftp """
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


@app.route("/task/ftp-source")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_ftp_source():
    """ return page to add a task ftp """
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


@app.route("/task/ftp-processing")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_ftp_processing():
    """ return page to add a task ftp """
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


@app.route("/task/ftp-query")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_ftp_query():
    """ return page to add a task ftp """
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


@app.route("/task/smb-source")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_smb_source():
    """ return page to add a task smb """
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


@app.route("/task/smb-dest")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_smb_dest():
    """ return page to add a task smb """
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


@app.route("/task/smb-query")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_smb_query():
    """ return page to add a task smb """
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


@app.route("/task/smb-processing")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_smb_processing():
    """ return page to add a task smb """
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


@app.route("/task/database-source")
@ldap.login_required
@ldap.group_required(["Analytics"])
def task_database_source():
    """ return page to add a task database """
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


def add_task_to_engine(my_id):
    """
    func = function to run
    trigger = date, interval or cron
    args *optional to call the function w/ (ex db connection, py version, bat (windows/linux), etc)
    karks *optional
    id = used to match job up to db
    name = desc of job
    misfire_grace_time = seconds after job is missed that it wil try to rerun
    coalesce = if there are multiple runs to do (from misfires), merge all into one run
    max_instances = max concurrent runs allowed
    next_run_time = when to start schedule (None = job paused)
    jobstore = alias of jobstore to use
    executor = alias of excutor to use
    replace_existing = true to replace jobs with same ID. keeps run history

    cron
    year (4 dgt), month( 1-12), day (1-31), week (1-53),
    day_of_week (0-6 or mon, tue,wed,thu,fri,sat,sun), hour (0-23), minute (0-59), second (0-59)
    start_date (datetime) = soonest start
    end_date (datetime) = latest run
    timezone
    jitter = seconds early/late to start job

    interval (time between runs)
    weeks, days, hours, minutes, seconds (all int)
    start_date (datetime) = soonest start
    end_date (datetime) = latest run
    timezone
    jitter = seconds early/late to start job

    date (for one off runs)
    run_date = when to run
    timezone

    multiple triggers
    and_trigger(triggers,), or_trigger(triggers,)

    app.apscheduler.add_job(
        func=scheduled_task,
        trigger='interval',
        args=[me.id], seconds=3,
        id=str(me.id),
        name=str(me.id)
        )
    jobstore uses the em Project id as its name. ID' are a hash of the time.
    This is done becasue 1 em job can have up to 3 engine jobs (chron, interval, one off)
    
    """

    # get id's of jobs by name. don't remove one off runs
    for job in app.apscheduler.get_jobs():
        if str(job.args[0]) == str(my_id) and job.trigger != "date":
            job.remove()
    # query job details

    task = Task.query.filter_by(id=my_id).first()
    task.enabled = 1
    project = task.project
    db.session.commit()

    my_hash = hashlib.sha256()

    # schedule cron
    if project.cron == 1:
        my_hash.update(str(time.time()).encode("utf-8"))
        app.apscheduler.add_job(
            func=Runner,
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
                str(my_id),
                # str(project.id) + "-" + str(job.id) + "-" + hash.hexdigest()[:10],
            ],
            id=str(project.id) + "-" + str(task.id) + "-" + my_hash.hexdigest()[:10],
            name="(cron) " + project.name + ": " + task.name,
        )
    # schedule interval
    if project.intv == 1:
        my_hash.update(str(time.time()).encode("utf-8"))
        weeks = project.intv_value or 999 if project.intv_type == "w" else 0
        days = project.intv_value or 999 if project.intv_type == "d" else 0
        hours = project.intv_value or 999 if project.intv_type == "h" else 0
        minutes = project.intv_value or 999 if project.intv_type == "m" else 0
        seconds = project.intv_value or 999 if project.intv_type == "s" else 0

        app.apscheduler.add_job(
            func=Runner,
            trigger="interval",
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            days=days,
            weeks=weeks,
            start_date=project.intv_start_date,
            end_date=project.intv_end_date,
            args=[
                str(my_id),
                # str(project.id) + "-" + str(job.id) + "-" + hash.hexdigest()[:10],
            ],
            id=str(project.id) + "-" + str(task.id) + "-" + my_hash.hexdigest()[:10],
            name="(inverval) " + project.name + ": " + task.name,
        )

    if project.ooff == 1:
        my_hash.update(str(time.time()).encode("utf-8"))
        app.apscheduler.add_job(
            func=Runner,
            trigger="date",
            run_date=project.ooff_date,
            args=[
                str(my_id),
                #  str(project.id) + "-" + str(task.id) + "-" + hash.hexdigest()[:10],
            ],
            id=str(project.id) + "-" + str(task.id) + "-" + my_hash.hexdigest()[:10],
            name="(one off) " + project.name + ": " + task.name,
        )
