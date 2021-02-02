"""Table API.

All routes return a json string to be build into a table by javascript.

All tables accept request parameters of:

* p: page number
* s: sort order ex: "Name.asc", "Name.desc"


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

import datetime
import html
import json

import requests
from em_web import db, ldap
from em_web.model import (
    ConnectionDatabase,
    ConnectionFtp,
    ConnectionSftp,
    ConnectionSmb,
    ConnectionSsh,
    Login,
    LoginType,
    Project,
    Task,
    TaskFile,
    TaskLog,
    TaskStatus,
    User,
)
from flask import Blueprint
from flask import current_app as app
from flask import jsonify, request, session
from sqlalchemy import and_, text

table_bp = Blueprint("table_bp", __name__)


@table_bp.route("/table/project/<my_type>")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def project_list(my_type="all"):
    """Build json dataset for ajax tables.

    :url: /table/project/<my_type>
    :param my_type: type of list (mine or all)

    :returns: json for ajax table.
    """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Name.asc", type=str)
    split_sort = sort.split(".")

    page -= 1

    cols = {
        "Project Id": "project.id",
        "Name": "project.name",
        "Owner Id": '"user".id',
        "Owner": '"user".full_name',
        "Last Run": "max(task.last_run)",
        "Next Run": "max(task.next_run)",
        "Tasks": "count(*)",
        "Enabled Tasks": "sum(case when task.enabled = 1 then 1 else 0 end )",
        "Running Tasks": "sum(case when task.status_id = 1 then 1 else 0 end)",
        "Errored Tasks": "sum(case when task.status_id = 2 then 1 else 0 end)",
        "Last Edited": "coalesce(project.updated,project.created)",
    }

    groups = {
        "Project Id": "project.id",
        "Name": "project.name",
        "Owner Id": '"user".id',
        "Last Edited": "coalesce(project.updated,project.created)",
    }

    projects = (
        db.session.query()
        .select_from(Project)
        .outerjoin(Task, Task.project_id == Project.id)
        .outerjoin(User, User.id == Project.owner_id)
        .add_columns(*cols.values())
        .order_by(text(cols[split_sort[0]] + " " + split_sort[1]))
        .group_by(*groups.values())
    )

    if my_type.isdigit():

        projects = projects.filter(User.id == int(my_type))

    elif my_type != "all":
        projects = projects.filter(User.user_id == session.get("user_id"))

    me = [
        {
            "head": '["Name","Owner","Last Run","Next Run","Last Edited",'
            + '"Tasks","Enabled Tasks","Running Tasks","Errored Tasks"]'
        }
    ]

    me.append({"total": projects.count() or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No projects."})

    for proj in projects.limit(10).offset(page * 10).all():
        proj = dict(zip(cols.keys(), proj))

        me.append(
            {
                "Name": '<a class="em-link" href="/project/'
                + str(proj["Project Id"])
                + '">'
                + proj["Name"]
                + "</a>",
                "Owner": (
                    "<a href='/project/user/"
                    + str(proj["Owner Id"])
                    + "' class='em-link'>"
                    + proj["Owner"]
                    + "</a>"
                    if proj["Owner"]
                    else "N/A"
                ),
                "Last Run": datetime.datetime.strftime(
                    proj["Last Run"],
                    "%a, %b %-d, %Y %H:%M:%S",
                )
                if proj["Last Run"]
                else "Never",
                "Next Run": datetime.datetime.strftime(
                    proj["Next Run"], "%a, %b %-d, %Y %H:%M:%S"
                )
                if proj["Next Run"]
                else "N/A",
                "Last Edited": datetime.datetime.strftime(
                    proj["Last Edited"], "%a, %b %-d, %Y %H:%M:%S"
                )
                if proj["Last Edited"]
                else "Never",
                "Tasks": proj["Tasks"],
                "Enabled Tasks": proj["Enabled Tasks"],
                "Running Tasks": proj["Running Tasks"],
                "Errored Tasks": proj["Errored Tasks"],
                "class": "error" if proj["Errored Tasks"] > 0 else "",
            }
        )

    return jsonify(me)


@table_bp.route("/table/tasklog/userevents")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def table_tasklog_userevents():
    """Table of all user events.

    :url: /table/tasklog/userevents

    :returns: json output of all user events.
    """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status Date.desc", type=str)
    split_sort = sort.split(".")

    page = page - 1

    cols = {
        "Log Id": "task_log.id",
        "Task Id": "task.id",
        "Job Id": "task_log.job_id",
        "Task Name": "task.name",
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
        .filter(TaskLog.status_id == 7)
        .add_columns(*cols.values())
        .order_by(text(cols[split_sort[0]] + " " + split_sort[1]))
    )

    me = [{"head": '["Task Name", "Run Id", "Status Date", "Message"]'}]

    me.append({"total": logs.count() or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No log messages."})

    for log in logs.limit(10).offset(page * 10).all():
        log = dict(zip(cols.keys(), log))

        me.append(
            {
                "Task Name": '<a class="em-link" href="/task/'
                + str(log["Log Id"])
                + '">'
                + log["Task Name"]
                + "</a>"
                if log["Task Name"]
                else "N/A",
                "Run Id": (
                    "<a class='em-link' href='/task/"
                    + str(log["Task Id"])
                    + "/log/"
                    + str(log["Job Id"])
                    + "'>"
                    + str(log["Job Id"])
                    + "</a>"
                    if log["Job Id"]
                    else ""
                ),
                "Status Date": datetime.datetime.strftime(
                    log["Status Date"],
                    "%a, %b %-d, %Y %H:%M:%S.%f",
                )
                if log["Status Date"]
                else "None",
                "Message": log["Message"],
                "class": "error" if log["Status Id"] == 2 or log["Error"] == 1 else "",
            }
        )

    return jsonify(me)


@table_bp.route("/table/user/auth")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def table_user_auth():
    """Table of all user login events.

    :url: /table/user/auth

    :returns: json output of all user events.
    """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Login Date.desc", type=str)
    split_sort = sort.split(".")

    page = page - 1

    cols = {
        "User": "login.username",
        "Login Date": "login.login_date",
        "Login Type Id": "login.type_id",
        "Login Type": "login_type.name",
    }

    logs = (
        db.session.query()
        .select_from(Login)
        .join(LoginType, LoginType.id == Login.type_id)
        .add_columns(*cols.values())
        .order_by(text(cols[split_sort[0]] + " " + split_sort[1]))
    )

    me = [{"head": '["User", "Login Date", "Action"]'}]

    me.append({"total": logs.count() or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No log messages."})

    for log in logs.limit(10).offset(page * 10).all():
        log = dict(zip(cols.keys(), log))

        me.append(
            {
                "User": log["User"],
                "Login Date": datetime.datetime.strftime(
                    log["Login Date"],
                    "%a, %b %-d, %Y %H:%M:%S.%f",
                )
                if log["Login Date"]
                else "None",
                "Action": log["Login Type"] if log["Login Type"] else "None",
                "class": "error" if log["Login Type Id"] == 3 else "",
            }
        )

    return jsonify(me)


@table_bp.route("/table/connection/<connection_id>/tasks")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_task(connection_id):
    """Get a table of any tasks associated with the connection.

    :url: /table/connection/<connection_id>/tasks
    :param connection_id: id of connection in question

    :returns: json output of associated tasks.
    """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status.desc", type=str)
    split_sort = sort.split(".")

    page -= 1

    cols = {
        "Task Id": "task.id",
        "Task Name": "task.name",
        "Project Id": "task.project_id",
        "Project Name": "project.name",
        "Enabled": "task.enabled",
        "Connection": "connection_sftp_name",
        "Last Run": "task.last_run",
        "Next Run": "task.next_run",
        "Status": "task_status.name",
        "Status Id": "task_status.id",
    }

    s_sftp = (
        db.session.query(Task.id, ConnectionSftp.name)
        .select_from(Task)
        .join(ConnectionSftp, ConnectionSftp.id == Task.source_sftp_id)
        .filter(ConnectionSftp.connection_id == connection_id)
    )
    d_sftp = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionSftp, ConnectionSftp.id == Task.destination_sftp_id)
        .filter(ConnectionSftp.connection_id == connection_id)
        .add_columns(Task.id, ConnectionSftp.name)
    )
    q_sftp = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionSftp, ConnectionSftp.id == Task.query_sftp_id)
        .filter(ConnectionSftp.connection_id == connection_id)
        .add_columns(Task.id, ConnectionSftp.name)
    )

    s_ssh = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionSsh, ConnectionSsh.id == Task.source_ssh_id)
        .filter(ConnectionSsh.connection_id == connection_id)
        .add_columns(Task.id, ConnectionSsh.name)
    )

    s_ftp = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionFtp, ConnectionFtp.id == Task.source_ftp_id)
        .filter(ConnectionFtp.connection_id == connection_id)
        .add_columns(Task.id, ConnectionFtp.name)
    )
    d_ftp = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionFtp, ConnectionFtp.id == Task.destination_ftp_id)
        .filter(ConnectionFtp.connection_id == connection_id)
        .add_columns(Task.id, ConnectionFtp.name)
    )
    q_ftp = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionFtp, ConnectionFtp.id == Task.query_ftp_id)
        .filter(ConnectionFtp.connection_id == connection_id)
        .add_columns(Task.id, ConnectionFtp.name)
    )

    s_smb = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionSmb, ConnectionSmb.id == Task.source_smb_id)
        .filter(ConnectionSmb.connection_id == connection_id)
        .add_columns(Task.id, ConnectionSmb.name)
    )
    d_smb = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionSmb, ConnectionSmb.id == Task.destination_smb_id)
        .filter(ConnectionSmb.connection_id == connection_id)
        .add_columns(Task.id, ConnectionSmb.name)
    )
    q_smb = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionSmb, ConnectionSmb.id == Task.query_smb_id)
        .filter(ConnectionSmb.connection_id == connection_id)
        .add_columns(Task.id, ConnectionSmb.name)
    )

    s_database = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionDatabase, ConnectionDatabase.id == Task.source_database_id)
        .filter(ConnectionDatabase.connection_id == connection_id)
        .add_columns(Task.id, ConnectionDatabase.name)
    )

    summary = s_sftp.union_all(
        d_sftp, q_sftp, s_ssh, s_ftp, d_ftp, q_ftp, s_smb, d_smb, q_smb, s_database
    ).subquery()

    tasks = (
        db.session.query()
        .select_from(Task)
        .join(summary, summary.c.task_id == Task.id)
        .outerjoin(Project, Project.id == Task.project_id)
        .outerjoin(TaskStatus, TaskStatus.id == Task.status_id)
        .add_columns(*cols.values())
        .order_by(text(cols[split_sort[0]] + " " + split_sort[1]))
    )

    me = [
        {
            "head": '["Task Name", "Project Name",\
                "Status", "Connection", "Enabled",\
                "Last Run", "Next Run"]'
        }
    ]

    me.append({"total": tasks.count() or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No tasks associated with this connection."})

    for task in tasks.limit(10).offset(page * 10).all():
        task = dict(zip(cols.keys(), task))

        me.append(
            {
                "Task Name": '<a class="em-link" href="/task/'
                + str(task["Task Id"])
                + '">'
                + task["Task Name"]
                + "</a>",
                "Project Name": '<a class="em-link" href="/project/'
                + str(task["Project Id"])
                + '">'
                + task["Project Name"]
                + "</a>"
                if task["Project Id"]
                else "Orphan :'(",
                "Connection": task["Connection"],
                "Enabled": "<a class='em-link' href=/task/"
                + str(task["Task Id"])
                + "/disable>Disable</a>"
                if task["Enabled"] == 1
                else "<a class='em-link' href=/task/"
                + str(task["Task Id"])
                + "/enable>Enable</a>",
                "Last Run": datetime.datetime.strftime(
                    task["Last Run"], "%a, %b %-d, %Y %H:%M:%S"
                )
                if task["Last Run"]
                else "Never",
                "Run Now": "<a class='em-link' href='/task/"
                + str(task["Task Id"])
                + "/run'>Run Now</a>",
                "Status": task["Status"] if task["Status"] else "None",
                "Next Run": datetime.datetime.strftime(
                    task["Next Run"], "%a, %b %-d, %Y %H:%M:%S"
                )
                if task["Next Run"]
                else "N/A",
                "class": "error"
                if task["Status Id"] == 2
                or (not task["Next Run"] and task["Enabled"] == 1)
                else "",
            }
        )

    return jsonify(me)


@table_bp.route("/table/jobs/orphans")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def table_jobs_orphans():
    """Get a table of any jobs without a linked task.

    :url: /table/jobs/orphans

    :returns: json output of associated jobs.
    """
    active_tasks = [
        x[0] for x in db.session.query().select_from(Task).add_columns("task.id").all()
    ]

    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Name.desc", type=str)
    split_sort = sort.split(".")

    page -= 1

    me = [{"head": '["Action", "Name", "Id", "Next Run Time", "Args"]'}]

    table = []

    try:
        for job in json.loads(
            requests.get(app.config["SCHEUDULER_HOST"] + "/details").text
        ):
            if int(job["id"]) not in active_tasks:
                table.append(
                    {
                        "Action": "<a class='em-link' href='/task/"
                        + job["id"]
                        + "/delete'>Delete</a>",
                        "Name": job["name"],
                        "Id": job["id"],
                        "Next Run": job["next_run_time"],
                        "Args": job["id"],
                        "class": "error",
                    }
                )
        table = (
            sorted(table, key=lambda k: k[split_sort[0]])
            if split_sort[1] == "desc"
            else sorted(table, key=lambda k: k[split_sort[0]], reverse=True)
        )

        me.append({"empty_msg": "No orphans."})
    except requests.exceptions.ConnectionError:
        table = []
        me.append({"empty_msg": "Error - EM_Scheduler offline."})

    for spage in table[page * 10 : page * 10 + 10]:
        me.append(spage)

    me.append({"total": len(table)})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page

    return jsonify(me)


@table_bp.route("/table/tasks/<task_type>")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def dash_errored(task_type):
    """Get a table of any jobs marked error.

    :url: /table/tasks/<task_type>
    :param task_type: active, errored, or scheduled

    :returns: json output of associated tasks.
    """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Last Run.asc", type=str)
    split_sort = sort.split(".")

    page -= 1

    cols = {
        "Task Id": "task.id",
        "Task Name": "task.name",
        "Project Id": "project.id",
        "Project Name": "project.name",
        "Owner Id": '"user".id',
        "Owner": '"user".full_name',
        "Status Id": "task_status.id",
        "Status": "task_status.name",
        "Last Run": "task.last_run",
        "Enabled": "task.enabled",
        "Next Run": "task.next_run",
    }

    tasks = (
        db.session.query()
        .select_from(Task)
        .outerjoin(TaskStatus, TaskStatus.id == Task.status_id)
        .outerjoin(Project, Project.id == Task.project_id)
        .outerjoin(User, User.id == Project.owner_id)
        .add_columns(*cols.values())
        .order_by(text(cols[split_sort[0]] + " " + split_sort[1]))
    )

    me = [
        {
            "head": '["Action", "Task Name", "Project Name", "Owner", "Last Run", "Next Run"]'
        }
    ]

    if task_type == "errored":
        tasks = tasks.filter(Task.status_id == 2)

    elif task_type == "scheduled":
        try:
            ids = json.loads(
                requests.get(app.config["SCHEUDULER_HOST"] + "/scheduled").text
            )
            tasks = tasks.filter(and_(Task.id.in_(ids), Task.enabled == 1))
        except requests.exceptions.ConnectionError:
            task = tasks.filter_by(id=-1)
            me.append({"empty_msg": "Error EM_Scheduler is offline."})

    elif task_type == "active":
        try:
            tasks = tasks.filter(Task.status_id == 1)  # running
        except requests.exceptions.ConnectionError:
            task = tasks.filter_by(id=-1)
            me.append({"empty_msg": "Error querying active tasks."})

    me.append({"total": tasks.count() or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page

    if "empty_msg" not in me:
        me.append({"empty_msg": "No task meet the criteria specified."})

    for task in tasks.limit(10).offset(page * 10).all():
        task = dict(zip(cols.keys(), task))

        me.append(
            {
                "Task Name": '<a class="em-link" href="/task/'
                + str(task["Task Id"])
                + '">'
                + task["Task Name"]
                + "</a>",
                "Project Name": (
                    (
                        '<a class="em-link" href="/project/'
                        + str(task["Project Id"])
                        + '">'
                        + task["Project Name"]
                        + "</a>"
                    )
                    if task["Project Id"]
                    else "Project Deleted"
                ),
                "Owner": (
                    "<a href='project/user/"
                    + str(task["Owner Id"])
                    + "' class='em-link'>"
                    + task["Owner"]
                    + "</a>"
                    if task["Owner Id"]
                    else "N/A"
                ),
                "Last Run": datetime.datetime.strftime(
                    task["Last Run"], "%a, %b %-d, %Y %H:%M:%S"
                )
                if task["Last Run"]
                else "Never",
                "Next Run": datetime.datetime.strftime(
                    task["Next Run"], "%a, %b %-d, %Y %H:%M:%S"
                )
                if task["Next Run"]
                else "N/A",
                "Action": (
                    (
                        "<a class='em-link' href='/task/"
                        + str(task["Task Id"])
                        + "/run'>Run Now</a><br>"
                        if task_type != "active"
                        else ""
                    )
                    + "<a class='em-link' href='/task/"
                    + str(task["Task Id"])
                    + "/schedule'>Reschedule</a><br><a class='em-link' href=/task/"
                    + str(task["Task Id"])
                    + "/disable>Disable</a>"
                    if task["Enabled"] == 1
                    else "<a class='em-link' href=/task/"
                    + str(task["Task Id"])
                    + "/enable>Enable</a>"
                )
                + (
                    "<br><a class='em-link' href='/task/"
                    + str(task["Task Id"])
                    + "/reset'>Reset</a>"
                    if task["Status Id"] == 2
                    else ""
                ),
                "class": "error" if task["Status Id"] == 2 else "",
            }
        )

    return jsonify(me)


@table_bp.route("/table/tasks/<my_type>/list")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def task_list(my_type):
    """Build json dataset for ajax tables.

    :url: /table/tasks/<my_type>/list
    :param my_type: type of list (mine or all)

    :returns: json for ajax table.
    """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Name.asc", type=str)
    split_sort = sort.split(".")

    page -= 1

    cols = {
        "Task Id": "task.id",
        "Name": "task.name",
        "Project Id": "project.id",
        "Project Name": "project.name",
        "Owner": '"user".full_name',
        "Owner Id": '"user".id',
        "Last Run": "task.last_run",
        "Next Run": "task.next_run",
        "Status Id": "task_status.id",
        "Status": "task_status.name",
        "Enabled": "task.enabled",
        "Last Edited": "coalesce(task.updated,task.created)",
    }

    if my_type == "all":
        tasks = (
            db.session.query()
            .select_from(Task)
            .outerjoin(Project, Project.id == Task.project_id)
            .outerjoin(User, User.id == Project.owner_id)
            .outerjoin(TaskStatus, TaskStatus.id == Task.status_id)
            .add_columns(*cols.values())
            .order_by(text(cols[split_sort[0]] + " " + split_sort[1]))
        )

    elif my_type.isdigit():
        tasks = (
            db.session.query()
            .select_from(Task)
            .outerjoin(Project, Project.id == Task.project_id)
            .outerjoin(User, User.id == Project.owner_id)
            .outerjoin(TaskStatus, TaskStatus.id == Task.status_id)
            .filter(User.id == int(my_type))
            .add_columns(*cols.values())
            .order_by(text(cols[split_sort[0]] + " " + split_sort[1]))
        )

    else:
        tasks = (
            db.session.query()
            .select_from(Task)
            .outerjoin(Project, Project.id == Task.project_id)
            .outerjoin(User, User.id == Project.owner_id)
            .outerjoin(TaskStatus, TaskStatus.id == Task.status_id)
            .filter(User.user_id == session.get("user_id"))
            .add_columns(*cols.values())
            .order_by(text(cols[split_sort[0]] + " " + split_sort[1]))
        )

    me = [
        {
            "head": '["Name","Project","Owner","Enabled","Last Run"'
            + ',"Run Now","Status","Next Run","Last Edited"]'
        }
    ]
    me.append({"total": tasks.count() or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No tasks."})

    for task in tasks.limit(10).offset(page * 10).all():
        task = dict(zip(cols.keys(), task))

        me.append(
            {
                "Name": '<a class="em-link" href="/task/'
                + str(task["Task Id"])
                + '">'
                + task["Name"]
                + "</a>",
                "Project": '<a class="em-link" href="/project/'
                + str(task["Project Id"])
                + '">'
                + task["Project Name"]
                + "</a>"
                if task["Project Id"]
                else "Orphan :'(",
                "Owner": (
                    "<a href='project/user/"
                    + str(task["Owner Id"])
                    + "' class='em-link'>"
                    + task["Owner"]
                    + "</a>"
                    if task["Owner"]
                    else "N/A"
                ),
                "Enabled": "<a class='em-link' href=/task/"
                + str(task["Task Id"])
                + "/disable>Disable</a>"
                if task["Enabled"] == 1
                else "<a class='em-link' href=/task/"
                + str(task["Task Id"])
                + "/enable>Enable</a>",
                "Last Run": datetime.datetime.strftime(
                    task["Last Run"], "%a, %b %-d, %Y %H:%M:%S"
                )
                if task["Last Run"]
                else "Never",
                "Last Edited": datetime.datetime.strftime(
                    task["Last Edited"], "%a, %b %-d, %Y %H:%M:%S"
                )
                if task["Last Edited"]
                else "Never",
                "Run Now": "<a class='em-link' href='/task/"
                + str(task["Task Id"])
                + "/run'>Run Now</a>",
                "Status": task["Status"] if task["Status"] else "None",
                "Next Run": datetime.datetime.strftime(
                    task["Next Run"], "%a, %b %-d, %Y %H:%M:%S"
                )
                if task["Next Run"]
                else "None",
                "class": "error" if task["Status Id"] == 2 else "",
            }
        )

    return jsonify(me)


@table_bp.route("/table/project/<project_id>/task")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def project_task_all(project_id):
    """Build json dataset for ajax tables of tasks for a project.

    :url: /table/project/<project_id>/task
    :param project_id: id of project owning the tasks

    :returns: json for ajax table.
    """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status.desc", type=str)
    split_sort = sort.split(".")

    page -= 1

    cols = {
        "Task Id": "task.id",
        "Name": "task.name",
        "Last Edited": "task.updated",
        "Last Run": "task.last_run",
        "Next Run": "task.next_run",
        "Status Id": "task_status.id",
        "Status": "task_status.name",
        "Enabled": "task.enabled",
    }

    tasks = (
        db.session.query()
        .select_from(Task)
        .outerjoin(TaskStatus, TaskStatus.id == Task.status_id)
        .filter(Task.project_id == project_id)
        .add_columns(*cols.values())
        .order_by(text(cols[split_sort[0]] + " " + split_sort[1]))
    )

    me = [
        {
            "head": '["Name","Enabled","Last Run","Run Now","Status","Next Run","Last Edited"]'
        }
    ]

    me.append({"total": tasks.count() or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No tasks."})

    for task in tasks.limit(10).offset(page * 10).all():
        task = dict(zip(cols.keys(), task))

        me.append(
            {
                "Name": '<a class="em-link" href="/task/'
                + str(task["Task Id"])
                + '">'
                + task["Name"]
                + "</a>",
                "Enabled": "<a class='em-link' href=/task/"
                + str(task["Task Id"])
                + "/disable>Disable</a>"
                if task["Enabled"] == 1
                else "<a class='em-link' href=/task/"
                + str(task["Task Id"])
                + "/enable>Enable</a>",
                "Last Run": datetime.datetime.strftime(
                    task["Last Run"], "%a, %b %-d, %Y %H:%M:%S"
                )
                if task["Last Run"]
                else "Never",
                "Run Now": "<a class='em-link' href='/task/"
                + str(task["Task Id"])
                + "/run'>Run Now</a>",
                "Status": task["Status"] if task["Status"] else "None",
                "Next Run": datetime.datetime.strftime(
                    task["Next Run"], "%a, %b %-d, %Y %H:%M:%S"
                )
                if task["Next Run"]
                else "None",
                "class": "error" if task["Status Id"] == 2 else "",
                "Last Edited": datetime.datetime.strftime(
                    task["Last Edited"], "%a, %b %-d, %Y %H:%M:%S"
                )
                if task["Last Edited"]
                else "Never",
            }
        )

    return jsonify(me)


@table_bp.route("/table/project/<project_id>/tasklog")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def project_task_log_all(project_id):
    """Build project tasklog json dataset for ajax tables.

    :url: /table/project/<project_id>/tasklog
    :param project_id: id of project owning the tasklog

    :returns: json for ajax table.
    """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status Date.desc", type=str)
    split_sort = sort.split(".")

    page = page - 1

    cols = {
        "Log Id": "task_log.id",
        "Task Id": "task.id",
        "Job Id": "task_log.job_id",
        "Task Name": "task.name",
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
        .filter(Task.project_id == project_id)
        .add_columns(*cols.values())
        .order_by(text(cols[split_sort[0]] + " " + split_sort[1]))
    )

    me = [{"head": '["Task Name", "Run Id", "Status", "Status Date", "Message"]'}]

    me.append({"total": logs.count() or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No log messages."})

    for log in logs.limit(10).offset(page * 10).all():

        log = dict(zip(cols.keys(), log))

        me.append(
            {
                "Task Name": '<a class="em-link" href="/task/'
                + str(log["Task Id"])
                + '">'
                + log["Task Name"]
                + "</a>"
                if log["Task Name"]
                else "N/A",
                "Run Id": (
                    "<a class='em-link' href='/task/"
                    + str(log["Task Id"])
                    + "/log/"
                    + str(log["Job Id"])
                    + "'>"
                    + str(log["Job Id"])
                    + "</a>"
                    if log["Job Id"]
                    else ""
                ),
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


@table_bp.route("/table/task/<task_id>/log")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def task_log(task_id):
    """Build tasklog json dataset for ajax tables.

    :url: /table/task/<task_id>/log

    :param task_id: id of task owning the tasklog

    :returns: json for ajax table.
    """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status Date.desc", type=str)
    split_sort = sort.split(".")

    page = page - 1

    cols = {
        "Log Id": "task_log.id",
        "Task Id": "task.id",
        "Job Id": "task_log.job_id",
        "Task Name": "task.name",
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
        .filter(Task.id == task_id)
        .add_columns(*cols.values())
        .order_by(text(cols[split_sort[0]] + " " + split_sort[1]))
    )

    me = [{"head": '["Run Id", "Status", "Status Date", "Message"]'}]

    me.append({"total": logs.count() or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No log messages."})

    for log in logs.limit(10).offset(page * 10).all():

        log = dict(zip(cols.keys(), log))

        me.append(
            {
                "Run Id": (
                    "<a class='em-link' href='/task/"
                    + str(log["Task Id"])
                    + "/log/"
                    + str(log["Job Id"])
                    + "'>"
                    + str(log["Job Id"])
                    + "</a>"
                    if log["Job Id"]
                    else ""
                ),
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


@table_bp.route("/table/tasks/log")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def dash_log():
    """Get a table of all task logs.

    :url: /table/tasks/log

    :returns: json output of associated logs.
    """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status Date.desc", type=str)
    split_sort = sort.split(".")

    page = page - 1

    cols = {
        "Log Id": "task_log.id",
        "Task Id": "task.id",
        "Job Id": "task_log.job_id",
        "Task Name": "task.name",
        "Project Id": "project.id",
        "Project Name": "project.name",
        "Owner Id": '"user".id',
        "Owner": '"user".full_name',
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
        .outerjoin(Project, Project.id == Task.project_id)
        .outerjoin(User, User.id == Project.owner_id)
        .outerjoin(TaskStatus, TaskStatus.id == TaskLog.status_id)
        .add_columns(*cols.values())
        .order_by(text(cols[split_sort[0]] + " " + split_sort[1]))
    )

    me = [
        {
            "head": '["Task Name", "Project Name", "Owner", "Status", "Status Date", "Message"]'
        }
    ]
    me.append({"total": logs.count() or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No log messages."})

    for log in logs.limit(10).offset(page * 10).all():
        log = dict(zip(cols.keys(), log))

        me.append(
            {
                "Task Name": '<a class="em-link" href="/task/'
                + str(log["Task Id"])
                + '">'
                + log["Task Name"]
                + "</a>"
                if log["Task Name"]
                else "N/A",
                "Project Name": (
                    '<a class="em-link" href="/project/'
                    + str(log["Project Id"])
                    + '">'
                    + log["Project Name"]
                    + "</a>"
                )
                if log["Project Id"]
                else "N/A",
                "Owner": (
                    "<a href='project/user/"
                    + str(log["Owner Id"])
                    + "' class='em-link'>"
                    + log["Owner"]
                    + "</a>"
                    if log["Owner"]
                    else "N/A"
                ),
                "Status Date": datetime.datetime.strftime(
                    log["Status Date"],
                    "%a, %b %-d, %Y %H:%M:%S.%f",
                )
                if log["Status Date"]
                else "None",
                "my_date_sort": log["Status Date"],
                "Status": log["Status"] if log["Status"] else "None",
                "Message": (
                    "Run: <a class='em-link' href='/task/"
                    + str(log["Task Id"])
                    + "/log/"
                    + log["Job Id"]
                    + "'>"
                    + log["Job Id"]
                    + ".</a> "
                    if log["Job Id"]
                    else ""
                )
                + html.escape(log["Message"]),
                "class": "error" if log["Status Id"] == 2 or log["Error"] == 1 else "",
            }
        )

    return jsonify(me)


@table_bp.route("/table/tasks/errorLog")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def dash_error_log():
    """Get a table of all task error logs.

    :url: /table/tasks/errorLog

    :returns: json output of associated logs.
    """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status Date.desc", type=str)
    split_sort = sort.split(".")

    page = page - 1

    cols = {
        "Log Id": "task_log.id",
        "Task Id": "task.id",
        "Job Id": "task.last_run_job_id",
        "Task Name": "task.name",
        "Project Id": "project.id",
        "Project Name": "project.name",
        "Owner Id": '"user".id',
        "Owner": '"user".full_name',
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
        .join(Project, Project.id == Task.project_id)
        .join(User, User.id == Project.owner_id)
        .join(TaskStatus, TaskStatus.id == TaskLog.status_id)
        .filter(TaskLog.error == 1)
        .add_columns(*cols.values())
        .order_by(text(cols[split_sort[0]] + " " + split_sort[1]))
    )

    me = [
        {
            "head": '["Task Name", "Project Name", "Owner", "Status", "Status Date", "Message"]'
        }
    ]
    me.append({"total": logs.count() or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No log messages."})

    for log in logs.limit(10).offset(page * 10).all():
        log = dict(zip(cols.keys(), log))

        me.append(
            {
                "Task Name": '<a class="em-link" href="/task/'
                + str(log["Task Id"])
                + '">'
                + log["Task Name"]
                + "</a>"
                if log["Task Name"]
                else "N/A",
                "Project Name": (
                    '<a class="em-link" href="/project/'
                    + str(log["Project Id"])
                    + '">'
                    + log["Project Name"]
                    + "</a>"
                )
                if log["Project Id"]
                else "N/A",
                "Owner": (
                    "<a href='project/user/"
                    + str(log["Owner Id"])
                    + "' class='em-link'>"
                    + log["Owner"]
                    + "</a>"
                    if log["Owner"]
                    else "N/A"
                ),
                "Status Date": datetime.datetime.strftime(
                    log["Status Date"],
                    "%a, %b %-d, %Y %H:%M:%S.%f",
                )
                if log["Status Date"]
                else "None",
                "my_date_sort": log["Status Date"],
                "Status": log["Status"] if log["Status"] else "None",
                "Message": (
                    "Run: <a class='em-link' href='/task/"
                    + str(log["Task Id"])
                    + "/log/"
                    + log["Job Id"]
                    + "'>"
                    + log["Job Id"]
                    + ".</a> "
                    if log["Job Id"]
                    else ""
                )
                + html.escape(log["Message"]),
                "class": "error" if log["Status Id"] == 2 or log["Error"] == 1 else "",
            }
        )

    return jsonify(me)


@table_bp.route("/table/task/<task_id>/files")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def get_task_files(task_id):
    """Build backup files associated with task as json dataset.

    :url: /table/task/<task_id>/files
    :param task_id: id of task owning the tasklog

    :returns: json for ajax table.
    """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Created.desc", type=str)
    split_sort = sort.split(".")

    page -= 1

    cols = {
        "File Id": "task_file.id",
        "Run Id": "task_file.job_id",
        "File Name": "task_file.name",
        "File Size": "task_file.size",
        "Created": "task_file.created",
    }

    my_files = (
        db.session.query()
        .select_from(TaskFile)
        .filter(TaskFile.task_id == task_id)
        .add_columns(*cols.values())
        .order_by(text(cols[split_sort[0]] + " " + split_sort[1]))
    )

    me = [{"head": '["File Name", "Run Id", "Created", "File Size", "Action"]'}]
    me.append({"total": my_files.count() or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No files available."})

    task = Task.query.filter_by(id=task_id)
    if task.count() > 0:
        task = task.first()
        for my_file in my_files.limit(10).offset(page * 10).all():
            my_file = dict(zip(cols.keys(), my_file))

            me.append(
                {
                    "File Name": my_file["File Name"],
                    "Run Id": "<a class='em-link' href='/task/"
                    + str(task_id)
                    + "/log/"
                    + str(my_file["Run Id"])
                    + "'>"
                    + str(my_file["Run Id"])
                    + "</a>",
                    "Created": (
                        datetime.datetime.strftime(
                            my_file["Created"],
                            "%a, %b %-d, %Y %H:%M:%S.%f",
                        )
                        if my_file["Created"]
                        else "N/A"
                    ),
                    "File Size": my_file["File Size"],
                    "Action": (
                        (
                            "<a href='/task/"
                            + str(task_id)
                            + "/file/"
                            + str(my_file["File Id"])
                            + "/sendSftp' class='em-link'>Send to SFTP</a>\n"
                            if task.destination_sftp == 1
                            else ""
                        )
                        + (
                            "<a href='/task/"
                            + str(task_id)
                            + "/file/"
                            + str(my_file["File Id"])
                            + "/sendFtp' class='em-link'>Send to FTP</a>\n"
                            if task.destination_ftp == 1
                            else ""
                        )
                        + (
                            "<a href='/task/"
                            + str(task_id)
                            + "/file/"
                            + str(my_file["File Id"])
                            + "/sendSmb' class='em-link'>Send to SMB</a>\n"
                            if task.destination_smb == 1
                            else ""
                        )
                        + (
                            "<a href='/task/"
                            + str(task_id)
                            + "/file/"
                            + str(my_file["File Id"])
                            + "/sendEmail' class='em-link'>Send to Email</a>\n"
                            if task.email_completion_file == 1
                            else ""
                        )
                        + (
                            "<a href='/file/"
                            + str(my_file["File Id"])
                            + "' class='em-link'>Download File</a>\n"
                        )
                    ),
                }
            )

    return jsonify(me)
