"""Table API.

All routes return a json string to be build into a table by javascript.

All tables accept request parameters of:

* p: page number
* s: sort order ex: "Name.asc", "Name.desc"


"""

import datetime
import html
import json

import requests
import urllib3
from flask import Blueprint
from flask import current_app as app
from flask import jsonify, request
from flask_login import current_user, login_required
from RelativeToNow import relative_to_now
from sqlalchemy import and_, text
from werkzeug import Response

from web import db
from web.model import (
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

table_bp = Blueprint("table_bp", __name__)


@table_bp.route("/table/project/<my_type>")
@login_required
def project_list(my_type: str = "all") -> Response:
    """Build json dataset for ajax tables."""
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Name.asc", type=str)
    split_sort = sort.split(".")

    page -= 1

    cols = {
        "Project Id": text("project.id"),
        "Name": text("project.name"),
        "Last Run": text("max(task.last_run)"),
        "Next Run": text("max(task.next_run)"),
        "Tasks": text("count(*)"),
        "Enabled Tasks": text("sum(case when task.enabled = 1 then 1 else 0 end )"),
        "Running Tasks": text("sum(case when task.status_id = 1 then 1 else 0 end)"),
        "Errored Tasks": text(
            "sum(case when task.status_id = 2 and task.enabled = 1 then 1 else 0 end)"
        ),
    }

    groups = {
        "Project Id": text("project.id"),
        "Name": text("project.name"),
        "Owner Id": text('"user".id'),
        "Last Edited": text("coalesce(project.updated,project.created)"),
    }

    projects = (
        db.session.query()
        .select_from(Project)
        .outerjoin(Task, Task.project_id == Project.id)
        .outerjoin(User, User.id == Project.owner_id)
        .add_columns(*cols.values())
        .order_by(text(str(cols[split_sort[0]]) + " " + split_sort[1]))
        .group_by(*groups.values())
    )

    if my_type.isdigit():
        projects = projects.filter(User.id == int(my_type))

    elif my_type != "all":
        projects = projects.filter(User.id == current_user.id)

    me = [{"head": '["Name","Last Run","Next Run","Tasks"]'}]

    me.append({"total": str(projects.count() or 0)})  # runs.total
    me.append({"page": str(page)})  # page
    me.append({"page_size": str(40)})
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No projects."})

    for proj in projects.limit(40).offset(page * 40).all():
        proj = dict(zip(cols.keys(), proj))

        status_icon = ""

        if proj["Running Tasks"] > 0:
            status_icon = '<span class="ml-0 mr-3 icon has-text-warning"><i class="fas fa-circle-notch"></i></span>'
        elif proj["Errored Tasks"] > 0:
            status_icon = '<span class="ml-0 mr-3 icon has-text-danger"><i class="fas fa-circle-xmark"></i></span>'
        elif proj["Enabled Tasks"] > 0 and not proj["Errored Tasks"]:
            status_icon = '<span class="ml-0 mr-3 icon has-text-success"><i class="fas fa-circle-check"></i></span>'
        elif proj["Enabled Tasks"] == 0:
            status_icon = '<span class="ml-0 mr-3 icon has-text-grey"><i class="fas fa-circle-stop"></i></span>'
        else:
            status_icon = '<span class="ml-0 mr-3 icon has-text-grey"><i class="fas fa-circle-question"></i></span>'
        me.append(
            {
                "Name": f'{status_icon}<a  href="/project/{proj["Project Id"]}">{proj["Name"]}</a>',
                "Last Run": relative_to_now(proj["Last Run"]) if proj["Last Run"] else "",
                "Next Run": (
                    datetime.datetime.strftime(proj["Next Run"], " %m/%-d/%y %H:%M")
                    if proj["Next Run"] and isinstance(proj["Next Run"], datetime.datetime)
                    else (proj["Next Run"] if proj["Next Run"] else "None")
                ),
                "Tasks": str((proj["Tasks"] or 0)),
            }
        )

    return jsonify(me)


@table_bp.route("/table/tasklog/userevents")
@login_required
def tasklog_userevents() -> Response:
    """Table of all user events."""
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status Date.desc", type=str)
    split_sort = sort.split(".")

    page = page - 1

    cols = {
        "Log Id": text("task_log.id"),
        "Task Id": text("task.id"),
        "Job Id": text("task_log.job_id"),
        "Task Name": text("task.name"),
        "Status Id": text("task_status.id"),
        "Status": text("task_status.name"),
        "Status Date": text("task_log.status_date"),
        "Message": text("task_log.message"),
        "Error": text("task_log.error"),
    }

    logs = (
        db.session.query()
        .select_from(TaskLog)
        .outerjoin(Task, Task.id == TaskLog.task_id)
        .outerjoin(TaskStatus, TaskStatus.id == TaskLog.status_id)
        .filter(TaskLog.status_id == 7)
        .add_columns(*cols.values())
        .order_by(text(str(cols[split_sort[0]]) + " " + split_sort[1]))
    )

    me = [{"head": '["Task Name", "Run Id", "Status Date", "Message"]'}]

    me.append({"total": str(logs.count() or 0)})  # runs.total
    me.append({"page": str(page)})  # page
    me.append({"page_size": str(10)})
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No log messages."})

    for log in logs.limit(10).offset(page * 10).all():
        log = dict(zip(cols.keys(), log))

        me.append(
            {
                "Task Name": (
                    '<a  href="/task/' + str(log["Task Id"]) + '">' + log["Task Name"] + "</a>"
                    if log["Task Name"]
                    else "N/A"
                ),
                "Run Id": (
                    "<a  href='/task/"
                    + str(log["Task Id"])
                    + "/log/"
                    + str(log["Job Id"])
                    + "'>"
                    + str(log["Job Id"])
                    + "</a>"
                    if log["Job Id"]
                    else ""
                ),
                "Status Date": (
                    datetime.datetime.strftime(
                        log["Status Date"],
                        "%a, %b %-d, %Y %H:%M:%S.%f",
                    )
                    if log["Status Date"] and isinstance(log["Status Date"], datetime.datetime)
                    else (log["Status Date"] if log["Status Date"] else "None")
                ),
                "Message": log["Message"],
                "class": "error" if log["Status Id"] == 2 or log["Error"] == 1 else "",
            }
        )

    return jsonify(me)


@table_bp.route("/table/user/auth")
@login_required
def user_auth() -> Response:
    """Table of all user login events."""
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Login Date.desc", type=str)
    split_sort = sort.split(".")

    page = page - 1

    cols = {
        "User": text("login.username"),
        "Login Date": text("login.login_date"),
        "Login Type Id": text("login.type_id"),
        "Login Type": text("login_type.name"),
    }

    logs = (
        db.session.query()
        .select_from(Login)
        .join(LoginType, LoginType.id == Login.type_id)
        .add_columns(*cols.values())
        .order_by(text(str(cols[split_sort[0]]) + " " + split_sort[1]))
    )

    me = [{"head": '["User", "Login Date", "Action"]'}]

    me.append({"total": str(logs.count() or 0)})  # runs.total
    me.append({"page": str(page)})  # page
    me.append({"page_size": str(10)})
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No log messages."})

    for log in logs.limit(10).offset(page * 10).all():
        log = dict(zip(cols.keys(), log))

        me.append(
            {
                "User": log["User"],
                "Login Date": (
                    datetime.datetime.strftime(
                        log["Login Date"],
                        "%a, %b %-d, %Y %H:%M:%S.%f",
                    )
                    if log["Login Date"] and isinstance(log["Login Date"], datetime.datetime)
                    else (log["Login Date"] if log["Login Date"] else "None")
                ),
                "Action": log["Login Type"] if log["Login Type"] else "None",
                "class": "error" if log["Login Type Id"] == 3 else "",
            }
        )

    return jsonify(me)


@table_bp.route("/table/connection/<connection_id>/tasks")
@login_required
def connection_tasks(connection_id: int) -> Response:
    """Get a table of any tasks associated with the connection."""
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status.desc", type=str)
    split_sort = sort.split(".")

    page -= 1

    cols = {
        "Task Id": text("task.id"),
        "Task Name": text("task.name"),
        "Project Id": text("task.project_id"),
        "Project Name": text("project.name"),
        "Enabled": text("task.enabled"),
        "Connection": text("connection_sftp_name"),
        "Last Run": text("task.last_run"),
        "Next Run": text("task.next_run"),
        "Status": text("task_status.name"),
        "Status Id": text("task_status.id"),
    }

    s_sftp = (
        db.session.query(Task.id, ConnectionSftp.name)
        .select_from(Task)
        .join(ConnectionSftp, ConnectionSftp.id == Task.source_sftp_id)
        .filter(ConnectionSftp.connection_id == connection_id)
        .filter(Task.source_type_id == 3)  # sftp
    )
    d_sftp = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionSftp, ConnectionSftp.id == Task.destination_sftp_id)
        .filter(ConnectionSftp.connection_id == connection_id)
        .filter(Task.destination_sftp == 1)  # enabled
        .add_columns(Task.id, ConnectionSftp.name)
    )
    q_sftp = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionSftp, ConnectionSftp.id == Task.query_sftp_id)
        .filter(ConnectionSftp.connection_id == connection_id)
        .filter(Task.source_query_type_id == 3)  # sftp
        .add_columns(Task.id, ConnectionSftp.name)
    )

    s_ssh = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionSsh, ConnectionSsh.id == Task.source_ssh_id)
        .filter(ConnectionSsh.connection_id == connection_id)
        .filter(Task.source_type_id == 6)  # ssh
        .add_columns(Task.id, ConnectionSsh.name)
    )

    s_ftp = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionFtp, ConnectionFtp.id == Task.source_ftp_id)
        .filter(ConnectionFtp.connection_id == connection_id)
        .filter(Task.source_type_id == 4)  # ftp
        .add_columns(Task.id, ConnectionFtp.name)
    )
    d_ftp = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionFtp, ConnectionFtp.id == Task.destination_ftp_id)
        .filter(ConnectionFtp.connection_id == connection_id)
        .filter(Task.destination_ftp == 1)  # enabled
        .add_columns(Task.id, ConnectionFtp.name)
    )
    q_ftp = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionFtp, ConnectionFtp.id == Task.query_ftp_id)
        .filter(ConnectionFtp.connection_id == connection_id)
        .filter(Task.source_query_type_id == 4)  # ftp
        .add_columns(Task.id, ConnectionFtp.name)
    )

    s_smb = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionSmb, ConnectionSmb.id == Task.source_smb_id)
        .filter(ConnectionSmb.connection_id == connection_id)
        .filter(Task.source_type_id == 2)  # smb
        .add_columns(Task.id, ConnectionSmb.name)
    )
    d_smb = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionSmb, ConnectionSmb.id == Task.destination_smb_id)
        .filter(ConnectionSmb.connection_id == connection_id)
        .filter(Task.destination_smb == 1)  # enabled
        .add_columns(Task.id, ConnectionSmb.name)
    )
    q_smb = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionSmb, ConnectionSmb.id == Task.query_smb_id)
        .filter(ConnectionSmb.connection_id == connection_id)
        .filter(Task.source_query_type_id == 2)  # smb
        .add_columns(Task.id, ConnectionSmb.name)
    )

    s_database = (
        db.session.query()
        .select_from(Task)
        .join(ConnectionDatabase, ConnectionDatabase.id == Task.source_database_id)
        .filter(ConnectionDatabase.connection_id == connection_id)
        .filter(Task.source_type_id == 1)  # database
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
        .order_by(text(str(cols[split_sort[0]]) + " " + split_sort[1]))
    )

    me = [
        {
            "head": '["Task Name", "Project Name",\
                "Status", "Connection", "Enabled",\
                "Last Run", "Next Run"]'
        }
    ]

    me.append({"total": str(tasks.count() or 0)})  # runs.total
    me.append({"page": str(page)})  # page
    me.append({"page_size": str(10)})
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No tasks associated with this connection."})

    for task in tasks.limit(10).offset(page * 10).all():
        task = dict(zip(cols.keys(), task))

        me.append(
            {
                "Task Name": '<a  href="/task/'
                + str(task["Task Id"])
                + '">'
                + task["Task Name"]
                + "</a>",
                "Project Name": (
                    '<a  href="/project/'
                    + str(task["Project Id"])
                    + '">'
                    + task["Project Name"]
                    + "</a>"
                    if task["Project Id"]
                    else "Orphan :'("
                ),
                "Connection": task["Connection"],
                "Enabled": (
                    "<a  href=/task/" + str(task["Task Id"]) + "/disable>Disable</a>"
                    if task["Enabled"] == 1
                    else "<a  href=/task/" + str(task["Task Id"]) + "/enable>Enable</a>"
                ),
                "Last Run": (
                    datetime.datetime.strftime(task["Last Run"], "%a, %b %-d, %Y %H:%M:%S")
                    if task["Last Run"] and isinstance(task["Last Run"], datetime.datetime)
                    else (task["Last Run"] if task["Last Run"] else "Never")
                ),
                "Run Now": "<a  href='/task/" + str(task["Task Id"]) + "/run'>Run Now</a>",
                "Status": task["Status"] if task["Status"] else "None",
                "Next Run": (
                    datetime.datetime.strftime(task["Next Run"], "%a, %b %-d, %Y %H:%M:%S")
                    if task["Next Run"] and isinstance(task["Next Run"], datetime.datetime)
                    else (task["Next Run"] if task["Next Run"] else "None")
                ),
                "class": (
                    "error"
                    if task["Status Id"] == 2 or (not task["Next Run"] and task["Enabled"] == 1)
                    else ""
                ),
            }
        )

    return jsonify(me)


@table_bp.route("/table/jobs/orphans")
@login_required
def table_jobs_orphans() -> Response:
    """Get a table of any jobs without a linked task."""
    active_tasks = [
        x[0] for x in db.session.query().select_from(Task).add_columns(text("task.id")).all()
    ]

    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Name.desc", type=str)
    split_sort = sort.split(".")

    page -= 1

    me = [{"head": '["Action", "Name", "Id", "Next Run Time", "Args"]'}]

    table = []

    try:
        for job in json.loads(
            requests.get(app.config["SCHEDULER_HOST"] + "/details", timeout=60).text
        ):
            if int(job["id"]) not in active_tasks:
                table.append(
                    {
                        "Action": "<a  href='/task/" + job["id"] + "/delete'>Delete</a>",
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
    except (requests.exceptions.ConnectionError, urllib3.exceptions.NewConnectionError):
        table = []
        me.append({"empty_msg": "Error - Scheduler offline."})

    for spage in table[page * 10 : page * 10 + 10]:
        me.append(spage)

    me.append({"total": str(len(table))})  # runs.total
    me.append({"page": str(page)})  # page
    me.append({"page_size": str(10)})
    me.append({"sort": sort})  # page

    return jsonify(me)


@table_bp.route("/table/tasks/<task_type>")
@login_required
def dash_tasks(task_type: str) -> Response:
    """Get a table of any jobs marked error."""
    default_sort = "Next Run.asc" if task_type == "scheduled" else "Last Run.asc"

    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default=default_sort, type=str)
    split_sort = sort.split(".")

    page -= 1

    cols = {
        "Task Id": text("task.id"),
        "Task Name": text("task.name"),
        "Project Name": text("project.name"),
        "Owner Id": text('"user".id'),
        "Owner": text('"user".full_name'),
        "Status Id": text("task_status.id"),
        "Status": text("task_status.name"),
        "Last Run": text("task.last_run"),
        "Enabled": text("task.enabled"),
        "Next Run": text("task.next_run"),
    }

    tasks = (
        db.session.query()
        .select_from(Task)
        .outerjoin(TaskStatus, TaskStatus.id == Task.status_id)
        .outerjoin(Project, Project.id == Task.project_id)
        .outerjoin(User, User.id == Project.owner_id)
        .add_columns(*cols.values())
        .order_by(text(str(cols[split_sort[0]]) + " " + split_sort[1]))
    )

    me = [{"head": '["Name", "Owner", "Last Run", "Next Run", "Actions"]'}]

    if task_type == "errored":
        tasks = tasks.filter(Task.status_id == 2, Task.enabled == 1)

    elif task_type == "scheduled":
        try:
            ids = json.loads(
                requests.get(app.config["SCHEDULER_HOST"] + "/scheduled", timeout=60).text
            )
            tasks = tasks.filter(and_(Task.id.in_(ids), Task.enabled == 1))  # type: ignore[attr-defined, union-attr]
        except (
            requests.exceptions.ConnectionError,
            urllib3.exceptions.NewConnectionError,
        ):
            tasks = tasks.filter(Task.id == -1)
            me.append({"empty_msg": "Error - Scheduler is offline."})

    elif task_type == "active":
        try:
            tasks = tasks.filter(Task.status_id == 1).filter(
                Task.enabled == 1
            )  # running and enabled
        except (
            requests.exceptions.ConnectionError,
            urllib3.exceptions.NewConnectionError,
        ):
            tasks = tasks.filter_by(id=-1)
            me.append({"empty_msg": "Error querying active tasks."})
        me = [{"head": '["Name", "Owner", "Started"]'}]

    me.append({"total": str(tasks.count() or 0)})  # runs.total
    me.append({"page": str(page)})  # page
    me.append({"page_size": str(10)})
    me.append({"sort": sort})  # page

    if "empty_msg" not in me:
        me.append({"empty_msg": "No task meet the criteria specified."})

    for task in tasks.limit(10).offset(page * 10).all():
        task = dict(zip(cols.keys(), task))

        if task["Enabled"] != 1:
            status_icon = '<span class="ml-5 mr-3 icon has-text-grey"><i class="fas fa-circle-stop"></i></span>'
        elif task["Status"] == "Completed":
            status_icon = '<span class="ml-5 mr-3 icon has-text-success"><i class="fas fa-circle-check"></i></span>'
        elif task["Status"] == "Running":
            status_icon = '<span class="ml-5 mr-3 icon has-text-warning"><i class="fas fa-circle-notch"></i></span>'
        elif task["Status"] == "Errored":
            status_icon = '<span class="ml-5 mr-3 icon has-text-danger"><i class="fas fa-circle-xmark"></i></span>'
        else:
            status_icon = '<span class="ml-5 mr-3 icon has-text-grey"><i class="fas fa-circle-question"></i></span>'

        if task["Enabled"] == 1:
            enabled = f'<div class="field mb-0"><input id="task-{task["Task Id"]}" name="task-{task["Task Id"]}" type="checkbox" class="switch is-rounded is-info" action="/task/{task["Task Id"]}/disable" checked /><label for="task-{task["Task Id"]}"></label></div>'
        else:
            enabled = f'<div class="field mb-0"><input id="task-{task["Task Id"]}" name="task-{task["Task Id"]}" type="checkbox" class="switch is-rounded is-info" action="/task/{task["Task Id"]}/enable" /><label for="task-{task["Task Id"]}"></label></div>'

        project = f" ({task['Project Name']})" if task["Project Name"] else ""

        me.append(
            {
                "Name": f'<div class="field has-addons">{enabled}{status_icon}<a  href="/task/{task["Task Id"]}">{task["Task Name"]}{project}</a></div>',
                "Owner": (
                    "<a href='project/user/"
                    + str(task["Owner Id"])
                    + "' >"
                    + task["Owner"]
                    + "</a>"
                    if task["Owner Id"]
                    else ""
                ),
                "Last Run": relative_to_now(task["Last Run"]) if task["Last Run"] else "Never",
                "Started": relative_to_now(task["Last Run"]) if task["Last Run"] else "Never",
                "Next Run": (
                    datetime.datetime.strftime(task["Next Run"], "%m/%-d/%y %H:%M")
                    if task["Next Run"] and isinstance(task["Next Run"], datetime.datetime)
                    else (task["Next Run"] if task["Next Run"] else "None")
                ),
                "Actions": (
                    (
                        "<a  href='/task/"
                        + str(task["Task Id"])
                        + "/run'>Run Now</a>&#8195;<span class='has-text-grey-light'>/</span>&#8195;"
                        if task_type != "active"
                        else ""
                    )
                    + "<a  href='/task/"
                    + str(task["Task Id"])
                    + "/schedule'>Reschedule</a>"
                ),
            }
        )

    return jsonify(me)


@table_bp.route("/table/tasks/<my_type>/list")
@login_required
def task_list(my_type: str) -> Response:
    """Build json dataset for ajax tables."""
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Name.asc", type=str)
    split_sort = sort.split(".")

    page -= 1

    cols = {
        "Task Id": text("task.id"),
        "Name": text("task.name"),
        "Project Name": text("project.name"),
        "Owner": text('"user".full_name'),
        "Owner Id": text('"user".id'),
        "Last Run": text("task.last_run"),
        "Next Run": text("task.next_run"),
        "Status Id": text("task_status.id"),
        "Status": text("task_status.name"),
        "Enabled": text("task.enabled"),
    }

    if my_type == "all":
        tasks = (
            db.session.query()
            .select_from(Task)
            .outerjoin(Project, Project.id == Task.project_id)
            .outerjoin(User, User.id == Project.owner_id)
            .outerjoin(TaskStatus, TaskStatus.id == Task.status_id)
            .add_columns(*cols.values())
            .order_by(text(str(cols[split_sort[0]]) + " " + split_sort[1]))
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
            .order_by(text(str(cols[split_sort[0]]) + " " + split_sort[1]))
        )

    else:
        tasks = (
            db.session.query()
            .select_from(Task)
            .outerjoin(Project, Project.id == Task.project_id)
            .outerjoin(User, User.id == Project.owner_id)
            .outerjoin(TaskStatus, TaskStatus.id == Task.status_id)
            .filter(User.id == current_user.id)
            .add_columns(*cols.values())
            .order_by(text(str(cols[split_sort[0]]) + " " + split_sort[1]))
        )

    if my_type == "all":
        me = [{"head": '["Name","Owner","Last Run"' + ',"Next Run"]'}]
    else:
        me = [{"head": '["Name","Last Run"' + ',"Next Run"]'}]
    me.append({"total": str(tasks.count() or 0)})  # runs.total
    me.append({"page": str(page)})  # page
    me.append({"page_size": str(40)})
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No tasks."})

    for task in tasks.limit(40).offset(page * 40).all():
        task = dict(zip(cols.keys(), task))

        if task["Enabled"] != 1:
            status_icon = '<span class="ml-5 mr-3 icon has-text-grey"><i class="fas fa-circle-stop"></i></span>'
        elif task["Status"] == "Completed":
            status_icon = '<span class="ml-5 mr-3 icon has-text-success"><i class="fas fa-circle-check"></i></span>'
        elif task["Status"] == "Running":
            status_icon = '<span class="ml-5 mr-3 icon has-text-warning"><i class="fas fa-circle-notch"></i></span>'
        elif task["Status"] == "Errored":
            status_icon = '<span class="ml-5 mr-3 icon has-text-danger"><i class="fas fa-circle-xmark"></i></span>'
        else:
            status_icon = '<span class="ml-5 mr-3 icon has-text-grey"><i class="fas fa-circle-question"></i></span>'

        if task["Enabled"] == 1:
            enabled = f'<div class="field mb-0"><input id="task-{task["Task Id"]}" name="task-{task["Task Id"]}" type="checkbox" class="switch is-rounded is-info" action="/task/{task["Task Id"]}/disable" checked /><label for="task-{task["Task Id"]}"></label></div>'
        else:
            enabled = f'<div class="field mb-0"><input id="task-{task["Task Id"]}" name="task-{task["Task Id"]}" type="checkbox" class="switch is-rounded is-info" action="/task/{task["Task Id"]}/enable" /><label for="task-{task["Task Id"]}"></label></div>'

        data = {
            "Name": f'<div class="field has-addons">{enabled}{status_icon}<a  href="/task/{task["Task Id"]}">{task["Name"]}</a></div>',
            "Last Run": relative_to_now(task["Last Run"]) if task["Last Run"] else "",
            "Next Run": (
                datetime.datetime.strftime(task["Next Run"], "%m/%-d/%y %H:%M")
                if task["Next Run"] and isinstance(task["Next Run"], datetime.datetime)
                else (task["Next Run"] if task["Next Run"] else "")
            ),
        }

        if my_type == "all":
            data["Owner"] = (
                "<a href='project/user/" + str(task["Owner Id"]) + "' >" + task["Owner"] + "</a>"
                if task["Owner"]
                else ""
            )

        me.append(data)

    return jsonify(me)


@table_bp.route("/table/project/<project_id>/task")
@login_required
def project_all_tasks(project_id: int) -> Response:
    """Build json dataset for ajax tables of tasks for a project."""
    page = request.args.get("p", default=1, type=int)
    page_size = 150
    page -= 1

    cols = {
        "Task Id": text("task.id"),
        "Name": text("task.name"),
        "Last Run": text("task.last_run"),
        "Next Run": text("task.next_run"),
        "Status Id": text("task_status.id"),
        "Status": text("task_status.name"),
        "Enabled": text("task.enabled"),
    }

    me = [{"head": '["Name","Last Run","Run Now","Next Run"]'}]

    # if the task run in series then add a rank column
    project = Project.query.filter_by(id=project_id).first()
    if project.sequence_tasks == 1:
        cols["Run Rank"] = text("task.order")
        me = [{"head": '["Name","Last Run","Run Now","Next Run","Run Rank"]'}]

        sort = request.args.get("s", default="Run Rank.asc", type=str)
    else:
        sort = request.args.get("s", default="Status.desc", type=str)

    split_sort = sort.split(".")

    tasks = (
        db.session.query()
        .select_from(Task)
        .outerjoin(TaskStatus, TaskStatus.id == Task.status_id)
        .filter(Task.project_id == project_id)
        .add_columns(*cols.values())
        .order_by(text(str(cols[split_sort[0]]) + " " + split_sort[1]))
    )

    me.append({"total": str(tasks.count() or 0)})  # runs.total
    me.append({"page": str(page)})  # page
    me.append({"page_size": str(page_size)})
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No tasks."})

    for task in tasks.limit(page_size).offset(page * page_size).all():
        task = dict(zip(cols.keys(), task))

        if task["Enabled"] != 1:
            status_icon = '<span class="ml-5 mr-3 icon has-text-grey"><i class="fas fa-circle-stop"></i></span>'
        elif task["Status"] == "Completed":
            status_icon = '<span class="ml-5 mr-3 icon has-text-success"><i class="fas fa-circle-check"></i></span>'
        elif task["Status"] == "Running":
            status_icon = '<span class="ml-5 mr-3 icon has-text-warning"><i class="fas fa-circle-notch"></i></span>'
        elif task["Status"] == "Errored":
            status_icon = '<span class="ml-5 mr-3 icon has-text-danger"><i class="fas fa-circle-xmark"></i></span>'
        else:
            status_icon = '<span class="ml-5 mr-3 icon has-text-grey"><i class="fas fa-circle-question"></i></span>'

        if task["Enabled"] == 1:
            enabled = f'<div class="field mb-0"><input id="task-{task["Task Id"]}" name="task-{task["Task Id"]}" type="checkbox" class="switch is-rounded is-info" action="/task/{task["Task Id"]}/disable" checked /><label for="task-{task["Task Id"]}"></label></div>'
        else:
            enabled = f'<div class="field mb-0"><input id="task-{task["Task Id"]}" name="task-{task["Task Id"]}" type="checkbox" class="switch is-rounded is-info" action="/task/{task["Task Id"]}/enable" /><label for="task-{task["Task Id"]}"></label></div>'

        me.append(
            {
                "Name": f'<div class="field has-addons">{enabled}{status_icon}<a  href="/task/{task["Task Id"]}">{task["Name"]}</a></div>',
                "Last Run": relative_to_now(task["Last Run"]) if task["Last Run"] else "",
                "Run Now": "<a href='/task/" + str(task["Task Id"]) + "/run'>Run Now</a>",
                "Next Run": (
                    datetime.datetime.strftime(task["Next Run"], "%m/%-d/%y %H:%M")
                    if task["Next Run"] and isinstance(task["Next Run"], datetime.datetime)
                    else (task["Next Run"] if task["Next Run"] else "")
                ),
                "Run Rank": task.get("Run Rank", None),
            }
        )

    return jsonify(me)


@table_bp.route("/table/task/<task_id>/log")
@login_required
def task_log(task_id: int) -> Response:
    """Build tasklog json dataset for ajax tables."""
    cols = {
        "log_id": text("task_log.id"),
        "task_id": text("task.id"),
        "job_id": text("task_log.job_id"),
        "status": text("task_status.name"),
        "status_id": text("task_log.status_id"),
        "date": text("task_log.status_date"),
        "message": text("task_log.message"),
        "error": text("task_log.error"),
    }

    logs = (
        db.session.query()
        .select_from(TaskLog)
        .join(Task, Task.id == TaskLog.task_id)
        .outerjoin(TaskStatus, TaskStatus.id == TaskLog.status_id)
        .filter(Task.id == task_id)
        .add_columns(*cols.values())
        .order_by(text(str("task_log.id desc")))
    )

    me = []

    me.append({"total": str(logs.count() or 0)})  # runs.total
    me.append({"empty_msg": "No log messages."})

    if request.args.get("gte"):
        logs = logs.filter(TaskLog.id >= request.args["gte"])

    elif request.args.get("lt"):
        logs = logs.filter(TaskLog.id < request.args["lt"]).limit(40)

    else:
        logs = logs.limit(40).offset(0)

    for log in logs.all():
        log = dict(zip(cols.keys(), log))

        me.append(
            {
                "log_id": log["log_id"],
                "job_id": ("(" + str(log["job_id"]) + ")" if log["job_id"] else ""),
                "date": (
                    datetime.datetime.strftime(
                        log["date"],
                        "%m/%-d/%y %H:%M:%S",
                    )
                    if log["date"] and isinstance(log["date"], datetime.datetime)
                    else (log["date"] if log["date"] else "None")
                ),
                "status": log["status"] if log["status"] else "None",
                "message": html.escape(log["message"]),
                "class": "error" if log["status_id"] == 2 or log["error"] == 1 else "",
            }
        )

    return jsonify(me)


@table_bp.route("/table/tasks/log")
@login_required
def dash_log() -> Response:
    """Get a table of all task logs."""
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status Date.desc", type=str)
    split_sort = sort.split(".")

    page = page - 1

    cols = {
        "Log Id": text("task_log.id"),
        "Task Id": text("task.id"),
        "Job Id": text("task_log.job_id"),
        "Task Name": text("task.name"),
        "Project Id": text("project.id"),
        "Project Name": text("project.name"),
        "Owner Id": text('"user".id'),
        "Owner": text('"user".full_name'),
        "Status Id": text("task_status.id"),
        "Status": text("task_status.name"),
        "Status Date": text("task_log.status_date"),
        "Message": text("task_log.message"),
        "Error": text("task_log.error"),
    }

    logs = (
        db.session.query()
        .select_from(TaskLog)
        .join(Task, Task.id == TaskLog.task_id)
        .outerjoin(Project, Project.id == Task.project_id)
        .outerjoin(User, User.id == Project.owner_id)
        .outerjoin(TaskStatus, TaskStatus.id == TaskLog.status_id)
        .add_columns(*cols.values())
        .order_by(text(str(cols[split_sort[0]]) + " " + split_sort[1]))
    )

    me = [{"head": '["Task Name", "Project Name", "Owner", "Status", "Status Date", "Message"]'}]
    me.append({"total": str(logs.count() or 0)})  # runs.total
    me.append({"page": str(page)})  # page
    me.append({"page_size": str(10)})
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No log messages."})

    for log in logs.limit(10).offset(page * 10).all():
        log = dict(zip(cols.keys(), log))

        me.append(
            {
                "Task Name": (
                    '<a  href="/task/' + str(log["Task Id"]) + '">' + log["Task Name"] + "</a>"
                    if log["Task Name"]
                    else "N/A"
                ),
                "Project Name": (
                    (
                        '<a  href="/project/'
                        + str(log["Project Id"])
                        + '">'
                        + log["Project Name"]
                        + "</a>"
                    )
                    if log["Project Id"]
                    else "N/A"
                ),
                "Owner": (
                    "<a href='project/user/" + str(log["Owner Id"]) + "' >" + log["Owner"] + "</a>"
                    if log["Owner"]
                    else "N/A"
                ),
                "Status Date": (
                    datetime.datetime.strftime(
                        log["Status Date"],
                        "%a, %b %-d, %Y %H:%M:%S.%f",
                    )
                    if log["Status Date"] and isinstance(log["Status Date"], datetime.datetime)
                    else (log["Status Date"] if log["Status Date"] else "None")
                ),
                "my_date_sort": log["Status Date"],
                "Status": log["Status"] if log["Status"] else "None",
                "Message": (
                    "Run: <a  href='/task/"
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
@login_required
def dash_error_log() -> Response:
    """Get a table of all task error logs."""
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status Date.desc", type=str)
    split_sort = sort.split(".")

    page = page - 1

    cols = {
        "Log Id": text("task_log.id"),
        "Task Id": text("task.id"),
        "Job Id": text("task.last_run_job_id"),
        "Task Name": text("task.name"),
        "Project Id": text("project.id"),
        "Project Name": text("project.name"),
        "Owner Id": text('"user".id'),
        "Owner": text('"user".full_name'),
        "Status Id": text("task_status.id"),
        "Status": text("task_status.name"),
        "Status Date": text("task_log.status_date"),
        "Message": text("task_log.message"),
        "Error": text("task_log.error"),
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
        .order_by(text(str(cols[split_sort[0]]) + " " + split_sort[1]))
    )

    me = [{"head": '["Task Name", "Project Name", "Owner", "Status", "Status Date", "Message"]'}]
    me.append({"total": str(logs.count() or 0)})  # runs.total
    me.append({"page": str(page)})  # page
    me.append({"page_size": str(10)})
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No log messages."})

    for log in logs.limit(10).offset(page * 10).all():
        log = dict(zip(cols.keys(), log))

        me.append(
            {
                "Task Name": (
                    '<a  href="/task/' + str(log["Task Id"]) + '">' + log["Task Name"] + "</a>"
                    if log["Task Name"]
                    else "N/A"
                ),
                "Project Name": (
                    (
                        '<a  href="/project/'
                        + str(log["Project Id"])
                        + '">'
                        + log["Project Name"]
                        + "</a>"
                    )
                    if log["Project Id"]
                    else "N/A"
                ),
                "Owner": (
                    "<a href='project/user/" + str(log["Owner Id"]) + "' >" + log["Owner"] + "</a>"
                    if log["Owner"]
                    else "N/A"
                ),
                "Status Date": (
                    datetime.datetime.strftime(
                        log["Status Date"],
                        "%a, %b %-d, %Y %H:%M:%S.%f",
                    )
                    if log["Status Date"] and isinstance(log["Status Date"], datetime.datetime)
                    else (log["Status Date"] if log["Status Date"] else "None")
                ),
                "my_date_sort": log["Status Date"],
                "Status": log["Status"] if log["Status"] else "None",
                "Message": (
                    "Run: <a  href='/task/"
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
@login_required
def one_task_files(task_id: int) -> Response:
    """Build backup files associated with task as json dataset."""
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Created.desc", type=str)
    split_sort = sort.split(".")

    page -= 1

    cols = {
        "File Id": text("task_file.id"),
        "Run Id": text("task_file.job_id"),
        "File Name": text("task_file.name"),
        "md5 Hash": text("task_file.file_hash"),
        "File Size": text("task_file.size"),
        "Created": text("task_file.created"),
    }

    my_files = (
        db.session.query()
        .select_from(TaskFile)
        .filter(TaskFile.task_id == task_id)
        .add_columns(*cols.values())
        .order_by(text(str(cols[split_sort[0]]) + " " + split_sort[1]))
    )

    me = [{"head": '["File Name", "Run Id", "Created", "md5 Hash", "File Size", "Action"]'}]
    me.append({"total": str(my_files.count() or 0)})  # runs.total
    me.append({"page": str(page)})  # page
    me.append({"page_size": str(10)})
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
                    "Run Id": "<a  href='/task/"
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
                        if my_file["Created"] and isinstance(my_file["Created"], datetime.datetime)
                        else (my_file["Created"] if my_file["Created"] else "N/A")
                    ),
                    "File Size": my_file["File Size"],
                    "md5 Hash": my_file["md5 Hash"],
                    "Action": (
                        (
                            "<a href='/task/"
                            + str(task_id)
                            + "/file/"
                            + str(my_file["File Id"])
                            + "/sendSftp' >Send to SFTP</a><br />"
                            if task.destination_sftp == 1
                            else ""
                        )
                        + (
                            "<a href='/task/"
                            + str(task_id)
                            + "/file/"
                            + str(my_file["File Id"])
                            + "/sendFtp' >Send to FTP</a><br />"
                            if task.destination_ftp == 1
                            else ""
                        )
                        + (
                            "<a href='/task/"
                            + str(task_id)
                            + "/file/"
                            + str(my_file["File Id"])
                            + "/sendSmb' >Send to SMB</a><br />"
                            if task.destination_smb == 1
                            else ""
                        )
                        + (
                            "<a href='/task/"
                            + str(task_id)
                            + "/file/"
                            + str(my_file["File Id"])
                            + "/sendEmail' >Send to Email</a><br />"
                            if task.email_completion == 1 and task.email_completion_file == 1
                            else ""
                        )
                        + (
                            "<a href='/file/"
                            + str(my_file["File Id"])
                            + "' >Download File</a><br />"
                        )
                    ),
                }
            )

    return jsonify(me)
