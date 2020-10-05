"""
    use to clear logs, and perform site wide scheduling activities
    
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
from flask import request, render_template, redirect, url_for, g, flash, jsonify
from em import app, ldap, db
from ..model.model import TaskLog, Task
from ..model.auth import Login
from ..scripts.error_print import full_stack


@app.route("/admin")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def admin():
    """ admin home page """
    message = request.args.get("message")
    if message:
        flash(message)

    return render_template("pages/admin.html.j2", title="Admin Area")


@app.route("/admin/emptyScheduler")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def admin_empty_scheduler():
    """ remove all jobs from scheduler """
    for job in app.apscheduler.get_jobs():
        job.remove()

    log = TaskLog(
        status_id=7, message=g.user_full_name + ": All jobs removed from scheduler.",
    )
    db.session.add(log)
    db.session.commit()

    return redirect(url_for("admin", message="All jobs removed from Scheduler!"))


@app.route("/admin/resetTasks")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def admin_reset_tasks():
    """ admin button to reset all tasks to complete """
    Task.query.update({Task.status_id: 4}, synchronize_session=False)
    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=g.user_full_name + ": All task reset to 'completed' status.",
    )
    db.session.add(log)
    db.session.commit()

    return redirect(url_for("admin", message="Tasks reset!"))


@app.route("/admin/clearlog")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def admin_clear_log():
    """ admin button to clear logs """
    TaskLog.query.delete()
    db.session.commit()

    log = TaskLog(status_id=7, message=g.user_full_name + ": All logs deleted.")
    db.session.add(log)
    db.session.commit()

    return redirect(url_for("admin", message="Logs deleted!"))


@app.route("/admin/pauseJobs")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def admin_pause_jobs():
    """ used to stop all jobs from running """
    try:
        app.apscheduler.pause()
        log = TaskLog(status_id=7, message=g.user_full_name + ": Scheduler paused.")
        db.session.add(log)
        db.session.commit()
        return redirect(url_for("admin", message="Scheduler paused."))
    # pylint: disable=bare-except
    except:
        log = TaskLog(
            status_id=7,
            error=1,
            message=g.user_full_name
            + ": Scheduler failed to pause.\n"
            + str(full_stack()),
        )
        db.session.add(log)
        db.session.commit()
        return redirect(
            url_for("admin", message="Scheduler failed to pause.\n" + str(full_stack()))
        )


@app.route("/admin/resumeJobs")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def admin_resume_jobs():
    """ used to stop all jobs from running """
    try:
        app.apscheduler.resume()
        log = TaskLog(status_id=7, message=g.user_full_name + ": Scheduler resumed.")
        db.session.add(log)
        db.session.commit()
        return redirect(url_for("admin", message="Scheduler resumed."))

    # pylint: disable=bare-except
    except:
        log = TaskLog(
            status_id=7,
            error=1,
            message=g.user_full_name
            + ": Scheduler failed to resume.\n"
            + str(full_stack()),
        )
        db.session.add(log)
        db.session.commit()
        return redirect(
            url_for(
                "admin", message="Scheduler failed to resume.\n" + str(full_stack())
            )
        )


@app.route("/admin/stopJobs")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def admin_stop_jobs():
    """ used to stop all jobs from running """
    try:
        app.apscheduler.shutdown()
        log = TaskLog(
            status_id=7, message=g.user_full_name + ": Scheduler gracefully shutdown.",
        )
        db.session.add(log)
        db.session.commit()
        return redirect(url_for("admin", message="Scheduler gracefully shutdown."))

    # pylint: disable=bare-except
    except:
        log = TaskLog(
            status_id=7,
            error=1,
            message=g.user_full_name
            + ": Scheduler failed to gracefully shutdown.\n"
            + str(full_stack()),
        )
        db.session.add(log)
        db.session.commit()
        return redirect(
            url_for(
                "admin",
                message="Scheduler failed to gracefully shutdown.\n"
                + str(full_stack()),
            )
        )


@app.route("/admin/killJobs")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def admin_kill_jobs():
    """ used to stop all jobs from running """
    try:
        app.apscheduler.shutdown(wait=False)
        log = TaskLog(status_id=7, message=g.user_full_name + ": Scheduler killed.")
        db.session.add(log)
        db.session.commit()
        return redirect(url_for("admin", message="Scheduler killed."))

    # pylint: disable=bare-except
    except:

        log = TaskLog(
            status_id=7,
            error=1,
            message=g.user_full_name
            + ": Scheduler failed to kill.\n"
            + str(full_stack()),
        )
        db.session.add(log)
        db.session.commit()
        return redirect(
            url_for("admin", message="Scheduler failed to kill.\n" + str(full_stack()))
        )


@app.route("/admin/user/tasklog")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def admin_user_task_log():
    """ log of all user events """

    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status Date.desc", type=str)
    split_sort = sort.split(".")

    page -= 1

    logs = TaskLog.query.filter_by(status_id=7).all()

    head = ["Task Name", "Run Id", "Status Date", "Message"]

    me = [{"head": str(head)}]
    table = []

    [
        table.append(
            {
                "Task Name": (
                    '<a class="em-link" href="/task/'
                    + str(log.task.id)
                    + '">'
                    + log.task.name
                    + "</a>"
                )
                if log.task
                else "N/A",
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
                )
                if log.task
                else "N/A",
                "Status Date": datetime.datetime.strftime(
                    log.status_date, "%a, %b %-d, %Y %H:%M:%S.%f",
                )
                if log.status_date
                else "None",
                "my_sort_date": (log.status_date or 0),
                "Message": log.message,
                "class": "error" if log.status_id == 2 or log.error == 1 else "",
            }
        )
        for log in logs
    ]

    table = (
        sorted(
            table, key=lambda k: k[split_sort[0].replace("Status Date", "my_sort_date")]
        )
        if split_sort[1] == "desc"
        else sorted(
            table,
            key=lambda k: k[split_sort[0].replace("Status Date", "my_sort_date")],
            reverse=True,
        )
    )
    [me.append(s) for s in table[page * 10 : page * 10 + 10]]

    me.append({"total": len(table) or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page

    return jsonify(me)


@app.route("/admin/user/loginlog")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def admin_user_login_log():
    """ log of all user events """

    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Login Date.asc", type=str)
    split_sort = sort.split(".")

    page -= 1

    logs = Login.query.all()

    head = ["User", "Login Date", "Action"]

    me = [{"head": str(head)}]
    table = []

    [
        table.append(
            {
                "User": log.username,
                "Login Date": datetime.datetime.strftime(
                    log.login_date, "%a, %b %-d, %Y %H:%M:%S.%f",
                )
                if log.login_date
                else "None",
                "my_sort_date": (log.login_date or 0),
                "Action": log.login_type.name if log.login_type else "None",
                "class": "error" if log.login_type == 3 else "",
            }
        )
        for log in logs
    ]

    table = (
        sorted(
            table, key=lambda k: k[split_sort[0].replace("Login Date", "my_sort_date")]
        )
        if split_sort[1] == "desc"
        else sorted(
            table,
            key=lambda k: k[split_sort[0].replace("Login Date", "my_sort_date")],
            reverse=True,
        )
    )
    [me.append(s) for s in table[page * 10 : page * 10 + 10]]

    me.append({"total": len(table) or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page

    return jsonify(me)
