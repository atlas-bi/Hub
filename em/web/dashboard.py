"""
    dashboard view and routes

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

import datetime
import hashlib
import logging
import time

from flask import render_template, request, jsonify, redirect, url_for
from em import app, ldap, db
from .task import add_task_to_engine
from ..model.model import Task, TaskStatus, TaskLog
from ..scripts.runner import Runner


@app.route("/")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash():
    """ main dashboard route """
    return render_template("pages/dashboard.html.j2", title="Dashboard")


@app.route("/dash/errorGauge")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_error_gauge():
    """ home page gauge of errored task % """
    success = db.session.execute(
        """
        select case when success > 0 
                    and error > 0 
                    then 1.00 - round(cast(error as decimal) / cast(success as decimal),2) 
             when error > 0 then 0
             when success = 0 then 0
             else 1 end accuracy from 
            (
                select count(1) error from (
                    select 1
                    from task_log t 
                    where status_date > now() - interval '72 hour' 
                    and task_id is not null and job_id is not null
                    and error=1
                    group by task_id
                ) as t
            ) as e
            , (
                select count(1) success
                from task_log t 
                where status_date > now() - interval '72 hour' 
                and task_id is not null and job_id is not null
                and message = 'Completed task.'
                and status_id = 8 -- runner
              ) as s



        """
    )
    names = [row[0] for row in success]

    return render_template(
        "pages/dashboard/gauge.html.j2",
        value_value=names[0],
        value=str(round((names[0] * 100), 0)) + "%",
        value_title="Successful Runs",
        value_subtitle="(last 72 hrs)",
    )


@app.route("/dash/runGauge")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_run_gauge():
    """ homepage guage of all tasks run """
    runs = db.session.execute(
        """
        select count(1)
        from task_log t 
        where status_date > now() - interval '24 hour' 
        and task_id is not null and job_id is not null
        and message = 'Completed task.'
        and status_id = 8 -- runner
        """
    )

    names = [row[0] for row in runs]
    return render_template(
        "pages/dashboard/gauge.html.j2",
        value_value=1,
        value=str(names[0]),
        value_title="Total Runs",
        value_subtitle="(last 72 hrs)",
    )


@app.route("/dash/orphans")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_orphans():
    """ ajax table of orphaned jobs """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Name.desc", type=str)
    split_sort = sort.split(".")

    page -= 1

    head = ["Action", "Name", "Id", "Next Run Time", "Args"]

    me = [{"head": str(head)}]

    table = []

    [
        table.append(
            {
                "Action": "<a class='em-link' href='/job/"
                + job.id
                + "/delete'>Delete</a>",
                "Name": job.name,
                "Id": job.id,
                "Next Run": job.next_run_time,
                "Args": job.args,
                "class": "error",
            }
        )
        for job in app.apscheduler.get_jobs()
        if Task.query.filter_by(id=int(job.args[0])).count() == 0
    ]

    table = (
        sorted(table, key=lambda k: k[split_sort[0]])
        if split_sort[1] == "desc"
        else sorted(table, key=lambda k: k[split_sort[0]], reverse=True)
    )

    [me.append(s) for s in table[page * 10 : page * 10 + 10]]

    me.append({"total": len(table)})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No orphans."})

    return jsonify(me)


@app.route("/dash/orphans/delete")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_orphans_delete():
    """ dash action to delete orphaned jobs """
    for j in app.apscheduler.get_jobs():
        if Task.query.filter_by(id=int(j.args[0])).count() == 0:
            j.remove()

    return redirect(url_for("dash"))


@app.route("/dash/errored")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_errored():
    """ dash table of errored jobs """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Task Name.desc", type=str)
    split_sort = sort.split(".")

    page -= 1
    tasks = Task.query.filter_by(status_id=2).all()

    head = [
        "Action",
        "Task Name",
        "Project Name",
        "Owner",
        "Last Active",
    ]

    me = [{"head": str(head)}]
    table = []

    [
        table.append(
            {
                "Task Name": '<a class="em-link" href="/task/'
                + str(task.id)
                + '">'
                + task.name
                + "</a>",
                "Project Name": (
                    (
                        '<a class="em-link" href="/project/'
                        + str(task.project.id)
                        + '">'
                        + task.project.name
                        + "</a>"
                    )
                    if task.project
                    else "Project Deleted"
                ),
                "Owner": (
                    task.project.project_owner.full_name
                    if task.project and task.project.project_owner
                    else "N/A"
                ),
                "Last Active": task.last_run or "Never",
                "Action": "<a class='em-link' href=/task/"
                + str(task.id)
                + ">Rerun Now</a>",
                "class": "error",
            }
        )
        for task in tasks
    ]

    ids = []
    [
        ids.append(job.args[0])
        for job in app.apscheduler.get_jobs()
        if job.next_run_time is not None
    ]
    tasks = Task.query.filter(Task.id.notin_(ids)).filter_by(enabled=1).all()

    [
        table.append(
            {
                "Task Name": '<a class="em-link" href="/task/'
                + str(task.id)
                + '">'
                + task.name
                + "</a>",
                "Project Name": (
                    '<a class="em-link" href="/project/'
                    + str(task.project.id)
                    + '">'
                    + task.project.name
                    + "</a>"
                )
                if task.project
                else "N/A",
                "Owner": (
                    task.project.project_owner.full_name
                    if task.project and task.project.project_owner
                    else ""
                ),
                "Last Active": task.last_run or "Never",
                "Action": "Error: Task must be <a class='em-link' href='/task/"
                + str(task.id)
                + "/schedule'>rescheduled</a> to run.",
                "class": "error",
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

    me.append({"total": len(table)})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page
    me.append({"empty_msg": "No errors tasks."})

    return jsonify(me)


@app.route("/dash/errored/run")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_errored_run():
    """ dash action to run all error tasks """
    tasks = Task.query.filter_by(status_id=2).all()

    ids = []

    [
        ids.append(job.args[0])
        for job in app.apscheduler.get_jobs()
        if job.next_run_time is not None
    ]

    [
        tasks.append(task)
        for task in Task.query.filter(Task.id.notin_(ids)).filter_by(enabled=1).all()
    ]

    for task in tasks:
        my_hash = hashlib.sha256()
        my_hash.update(str(time.time()).encode("utf-8"))
        app.apscheduler.add_job(
            func=Runner,
            trigger="date",
            run_date=datetime.datetime.now(),
            args=[
                str(task.id),
                # str(task.project.id) + "-" + str(task.id) + "-" + my_hash.hexdigest()[:10],
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
    return redirect(url_for("dash"))


@app.route("/dash/errored/schedule")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_errored_schedule():
    """ dash action to reschedul all errored jobs """

    tasks = Task.query.filter_by(status_id=2).all()
    ids = []

    [
        ids.append(job.args[0])
        for job in app.apscheduler.get_jobs()
        if job.next_run_time is not None
    ]
    [
        tasks.append(task)
        for task in Task.query.filter(Task.id.notin_(ids)).filter_by(enabled=1).all()
    ]

    for task in tasks:
        add_task_to_engine(task.id)

    return redirect(url_for("dash"))


@app.route("/dash/scheduled")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_scheduled():
    """ dash table of all scheduled tasks """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Last Active.asc", type=str)
    split_sort = sort.split(".")

    page -= 1
    ids = []

    [
        ids.append(int(job.args[0]))
        for job in app.apscheduler.get_jobs()
        if job.next_run_time is not None and len(job.args) > 0
    ]

    tasks = Task.query.filter(Task.id.in_(ids)).filter_by(enabled=1).all()

    head = [
        "Action",
        "Task Name",
        "Project Name",
        "Owner",
        "Last Active",
        "Last Status",
        "Next Run",
    ]

    me = [{"head": str(head)}]
    table = []

    [
        table.append(
            {
                "Task Name": '<a class="em-link" href="/task/'
                + str(task.id)
                + '">'
                + task.name
                + "</a>",
                "Project Name": '<a class="em-link" href="/project/'
                + str(task.project.id)
                + '">'
                + task.project.name
                + "</a>",
                "Owner": task.project.project_owner.full_name,
                "Last Active": datetime.datetime.strftime(
                    task.last_run, "%a, %b %-d, %Y %H:%M:%S",
                )
                if task.last_run
                else "Never",
                "Last Status": task.status.name if task.status else "None",
                "Action": "<a class='em-link' href='/task/"
                + str(task.id)
                + "/run'>Run Now</a><br><a class='em-link' href='/task/"
                + str(task.id)
                + "/schedule'>Reschedule</a><br><a class='em-link' href=/task/"
                + str(task.id)
                + "/disable>Disable</a>"
                if task.enabled == 1
                else "<a class='em-link' href=/task/"
                + str(task.id)
                + "/enable>Enable</a>",
                "Next Run": (
                    datetime.datetime.strftime(
                        min(
                            [
                                job.next_run_time
                                for job in app.apscheduler.get_jobs()
                                if str(job.args[0]) == str(task.id)
                            ]
                        ),
                        "%a, %b %-d, %Y %H:%M:%S",
                    )
                    if [
                        job.next_run_time
                        for job in app.apscheduler.get_jobs()
                        if str(job.args[0]) == str(task.id)
                    ]
                    else "None"
                ),
                "class": "error" if task.enabled == 0 else "",
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
    me.append({"empty_msg": "No scheduled tasks."})

    return jsonify(me)


@app.route("/dash/scheduled/run")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_scheduled_run():
    """ dash action to run all scheduled jobs now """
    log = logging.getLogger()

    ids = []
    [
        ids.append(int(job.args[0]))
        for job in app.apscheduler.get_jobs()
        if job.next_run_time is not None and len(job.args) > 0
    ]

    log.warn(ids)

    tasks = Task.query.filter(Task.id.in_(ids)).filter_by(enabled=1).all()
    log.warn(len(tasks))

    for task in tasks:
        my_hash = hashlib.sha256()
        my_hash.update(str(time.time() * 1000).encode("utf-8"))
        app.apscheduler.add_job(
            func=Runner,
            trigger="date",
            run_date=datetime.datetime.now(),
            args=[
                str(task.id),
                # str(t.project.id) + "-" + str(t.id) + "-" + hash.hexdigest()[:10],
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
        log.warn("task added: " + str(task.id))

    # return redirect(url_for("dash"))

    return str(len(tasks))


@app.route("/dash/scheduled/reschedule")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_scheduled_reschedule():
    """ dash action to reschedule all scheduled tasks """
    ids = []
    [
        ids.append(job.args[0])
        for job in app.apscheduler.get_jobs()
        if job.next_run_time is not None
    ]

    tasks = Task.query.filter(Task.id.in_(ids)).filter_by(enabled=1).all()

    for task in tasks:
        add_task_to_engine(task.id)

    return redirect(url_for("dash"))


@app.route("/dash/scheduled/disable")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_scheduled_disable():
    """ dash action to disable all scheduled jobs """
    ids = []
    [
        ids.append(job.args[0])
        for job in app.apscheduler.get_jobs()
        if job.next_run_time is not None
    ]

    tasks = Task.query.filter(Task.id.in_(ids)).filter_by(enabled=1).all()

    for task in tasks:
        task.enabled = 0
        db.session.commit()

        for job in app.apscheduler.get_jobs():
            if str(job.args[0]) == str(task.id):
                job.remove()

    return redirect(url_for("dash"))


@app.route("/dash/log")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_log():
    """ dash get current log table """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status Date.asc", type=str)
    split_sort = sort.split(".")

    page -= 1

    logs = TaskLog.query.order_by(TaskLog.status_date).all()

    head = ["Task Name", "Project Name", "Owner", "Status", "Status Date", "Message"]

    me = [{"head": str(head)}]
    table = []

    [
        table.append(
            {
                "Task Name": '<a class="em-link" href="/task/'
                + str(log.task.id)
                + '">'
                + log.task.name
                + "</a>"
                if log.task
                else "N/A",
                "Project Name": (
                    '<a class="em-link" href="/project/'
                    + str(log.task.project.id)
                    + '">'
                    + log.task.project.name
                    + "</a>"
                )
                if log.task and log.task.project
                else "N/A",
                "Owner": (
                    log.task.project.project_owner.full_name
                    if log.task and log.task.project
                    else "N/A"
                )
                if log.task
                else "N/A",
                "Status Date": datetime.datetime.strftime(
                    log.status_date, "%a, %b %-d, %Y %H:%M:%S.%f",
                )
                if log.status_date
                else "None",
                "my_date_sort": log.status_date,
                "Status": log.status.name if log.status else "None",
                "Message": (
                    "Run: <a class='em-link' href='/task/"
                    + str(log.task.id)
                    + "/log/"
                    + log.job_id
                    + "'>"
                    + log.job_id
                    + ".</a> "
                    if log.job_id
                    else ""
                )
                + log.message,
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


@app.route("/dash/active")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_active():
    """ dash get table of active tasks """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Last Active.asc", type=str)
    split_sort = sort.split(".")

    page -= 1
    ids = []
    [
        ids.append(job.args[0])
        for job in app.apscheduler.get_jobs()
        if job.next_run_time is not None
    ]
    tasks = (
        Task.query.filter(Task.id.in_(ids))
        .filter_by(status_id=1)
        .join(TaskStatus, Task.status_id == TaskStatus.id)
        .all()
    )

    head = [
        "Task Name",
        "Project Name",
        "Owner",
        "Last Active",
        "Last Status",
    ]

    me = [{"head": str(head)}]
    table = []

    [
        table.append(
            {
                "Task Name": '<a class="em-link" href="/task/'
                + str(task.id)
                + '">'
                + task.name
                + "</a>",
                "Project Name": '<a class="em-link" href="/project/'
                + str(task.project.id)
                + '">'
                + task.project.name
                + "</a>",
                "Owner": task.project.project_owner.full_name,
                "Last Active": datetime.datetime.strftime(
                    task.last_run, "%a, %b %-d, %Y %H:%M:%S.%f",
                )
                if task.last_run
                else "Never",
                "Last Status": task.status.name,
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
    me.append({"empty_msg": "No active tasks."})

    return jsonify(me)
