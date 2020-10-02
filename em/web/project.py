"""
    webapp views for projects

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
from flask import request, render_template, redirect, url_for, g, jsonify

from em import app, ldap, db, cache
from ..model.model import Project, User, Task, TaskLog
from .task import add_task_to_engine


@app.route("/project")
@ldap.login_required
@ldap.group_required(["Analytics"])
def project():
    """ main view of all projects """
    me = Project.query.order_by(Project.name).all()
    if len(me) < 1:
        return redirect(url_for("project_new"))
    return render_template("pages/project/all.html.j2", projects=me, title="Projects")


@app.route("/project/mine")
@ldap.login_required
@ldap.group_required(["Analytics"])
def project_mine():
    """ main view of just my projects """

    me = (
        Project.query.join(User, Project.owner_id == User.id)
        .filter_by(user_id=g.user_id)
        .all()
    )

    if len(me) < 1:
        return redirect(url_for("project_new"))
    return render_template(
        "pages/project/all.html.j2",
        projects=me,
        title="My Projects",
        mine=g.user_full_name,
    )


@app.route("/project/<my_type>/list")
@ldap.login_required
@ldap.group_required(["Analytics"])
def project_all_list(my_type="all"):
    """ return a table of projects """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Name.desc", type=str)
    split_sort = sort.split(".")

    page -= 1

    if my_type == "all":
        projects = Project.query.join(User, Project.owner_id == User.id).all()
    else:
        projects = (
            Project.query.join(User, Project.owner_id == User.id)
            .filter_by(user_id=g.user_id)
            .all()
        )

    head = [
        "Name",
        "Owner",
        "Last Active",
        "Active Tasks",
        "Running Tasks",
        "Errored Tasks",
    ]

    me = [{"head": str(head)}]
    table = []

    [
        table.append(
            {
                "Name": '<a class="em-link" href="/project/'
                + str(project.id)
                + '">'
                + project.name
                + "</a>",
                "Owner": project.project_owner.full_name,
                "Last Active": datetime.datetime.strftime(
                    project.task.order_by(Task.last_run).first().last_run,
                    "%a, %b %-d, %Y %H:%M:%S",
                )
                if project.task.order_by(Task.last_run).first()
                and project.task.order_by(Task.last_run).first().last_run is not None
                else "Never",
                "Active Tasks": project.task.filter_by(enabled=1).count(),
                "Running Tasks": project.task.filter_by(status_id=1).count(),
                "Errored Tasks": (
                    project.task.filter_by(status_id=2).count()
                    + project.task.filter(
                        Task.id.notin_(
                            [
                                job.args[0]
                                for job in app.apscheduler.get_jobs()
                                if job.next_run_time is not None
                            ]
                        )
                    )
                    .filter_by(enabled=1)
                    .count()
                ),
                "class": "error"
                if project.task.filter_by(status_id=2).count() > 0
                or project.task.filter(
                    Task.id.notin_(
                        [
                            job.args[0]
                            for job in app.apscheduler.get_jobs()
                            if job.next_run_time is not None
                        ]
                    )
                )
                .filter_by(enabled=1)
                .count()
                > 0
                else "",
            }
        )
        for project in projects
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


@app.route("/project/<my_id>", methods=["GET"])
@ldap.login_required
@ldap.group_required(["Analytics"])
def project_get(my_id):
    """ return details for a specific project """
    me = Project.query.filter_by(id=my_id).first()

    if me:
        return render_template("pages/project/details.html.j2", p=me, title=me.name)

    return render_template("pages/project/details.html.j2", invalid=True, title="Error")


@app.route("/project/<my_id>/edit", methods=["GET"])
@ldap.login_required
@ldap.group_required(["Analytics"])
def project_edit_get(my_id):
    """ return project editor """
    me = Project.query.filter_by(id=my_id).first()

    if me:
        return render_template(
            "pages/project/new.html.j2", p=me, title="Editing " + me.name
        )

    return render_template("pages/project/details.html.j2", invalid=True, title="Error")


@app.route("/project/<my_id>/edit", methods=["POST"])
@ldap.login_required
@ldap.group_required(["Analytics"])
def project_edit_post(my_id):
    """ save project edits """
    me = Project.query.filter_by(id=my_id).first()
    if not me:
        return redirect(url_for("project_get", my_id=my_id))

    cache.clear()

    if User.query.filter_by(user_id=g.user_id).count():
        updater = User.query.filter_by(user_id=g.user_id).first()
        updater.full_name = g.user_full_name
    else:
        updater = User(user_id=g.user_id, full_name=g.user_full_name)

    form = request.form

    me.name = form["project_name"]
    me.description = form["project_desc"]
    me.updater_id = updater.id
    me.global_params = form["globalParams" if "globalParams" in form else ""]

    if "project_ownership" in form and form["project_ownership"] == 1:
        me.owner_id = updater.id

    # add triggers
    # cron
    if form["project_cron"] == "1":
        me.cron = 1
        if form["project_cron_year"].isdigit():
            me.cron_year = int(form["project_cron_year"])
        if form["project_cron_mnth"].isdigit():
            me.cron_month = int(form["project_cron_mnth"])
        if form["project_cron_week"].isdigit():
            me.cron_week = int(form["project_cron_week"])
        if form["project_cron_day"].isdigit():
            me.cron_day = int(form["project_cron_day"])
        if form["project_cron_wday"].isdigit():
            me.cron_week_day = int(form["project_cron_wday"])
        if form["project_cron_hour"].isdigit():
            me.cron_hour = int(form["project_cron_hour"])
        if form["project_cron_min"].isdigit():
            me.cron_min = int(form["project_cron_min"])
        if form["project_cron_sec"].isdigit():
            me.cron_sec = int(form["project_cron_sec"])

        if form["project_cron_sdate"]:
            date = datetime.datetime.strptime(
                form["project_cron_sdate"], "%Y-%m-%d %H:%M"
            )
            me.cron_start_date = date

        if form["project_cron_edate"]:
            date = datetime.datetime.strptime(
                form["project_cron_edate"], "%Y-%m-%d %H:%M"
            )
            me.cron_end_date = date
    else:
        me.cron = 0
    # intv
    if form["project_intv"] == "1":
        me.intv = 1

        me.intv_type = form["project_intv_intv"]
        me.intv_value = form["project_intv_value"]

        if form["project_intv_sdate"]:
            date = datetime.datetime.strptime(
                form["project_intv_sdate"], "%Y-%m-%d %H:%M"
            )
            me.intv_start_date = date

        if form["project_intv_edate"]:
            date = datetime.datetime.strptime(
                form["project_intv_edate"], "%Y-%m-%d %H:%M"
            )
            me.intv_end_date = date
    else:
        me.intv = 0

    if form["project_ooff"] == "1":
        me.ooff = 1
        date = (
            datetime.datetime.strptime(form["project_ooff_date"], "%Y-%m-%d %H:%M")
            if form["project_ooff_date"]
            else datetime.date.today()
        )
        me.ooff_date = date

    else:
        me.ooff = 0

    db.session.commit()

    # reschedule any jobs.
    tasks = Task.query.filter_by(project_id=my_id, enabled=1).all()
    for task in tasks:
        log = TaskLog(
            task_id=task.id,
            status_id=7,
            message=g.user_full_name + ": Task rescheduled.",
        )
        db.session.add(log)
        db.session.commit()
        add_task_to_engine(task.id)

    return redirect(url_for("project_get", my_id=my_id))


@app.route("/project/new", methods=["GET"])
@ldap.login_required
@ldap.group_required(["Analytics"])
@cache.cached(timeout=120)
def project_new_form():
    """ retrun page to create a new project """
    return render_template(
        "pages/project/new.html.j2",
        p=Project.query.filter(1 == 2).first(),
        title="New Project",
    )


@app.route("/project/new", methods=["POST"])
@ldap.login_required
@ldap.group_required(["Analytics"])
def project_new():
    """ create a new project """
    cache.clear()
    form = request.form

    project_name = form["project_name"]
    project_desc = form["project_desc"]
    project_params = form["globalParams"] if "globalParams" in form else ""

    # create owner record
    if User.query.filter_by(user_id=g.user_id).count():
        owner = User.query.filter_by(user_id=g.user_id).first()
        owner.full_name = g.user_full_name
    else:
        owner = User(user_id=g.user_id, full_name=g.user_full_name)

    db.session.add(owner)
    db.session.commit()

    # create project
    me = Project(
        name=project_name,
        description=project_desc,
        owner_id=owner.id,
        creator_id=owner.id,
        updater_id=owner.id,
        global_params=project_params,
    )

    # add triggers
    if form["project_cron"] == "1":
        me.cron = 1
        if form["project_cron_year"].isdigit():
            me.cron_year = int(form["project_cron_year"])
        if form["project_cron_mnth"].isdigit():
            me.cron_month = int(form["project_cron_mnth"])
        if form["project_cron_week"].isdigit():
            me.cron_week = int(form["project_cron_week"])
        if form["project_cron_day"].isdigit():
            me.cron_day = int(form["project_cron_day"])
        if form["project_cron_wday"].isdigit():
            me.cron_week_day = int(form["project_cron_wday"])
        if form["project_cron_hour"].isdigit():
            me.cron_hour = int(form["project_cron_hour"])
        if form["project_cron_min"].isdigit():
            me.cron_min = int(form["project_cron_min"])
        if form["project_cron_sec"].isdigit():
            me.cron_sec = int(form["project_cron_sec"])

        if form["project_cron_sdate"]:
            date = datetime.datetime.strptime(
                form["project_cron_sdate"], "%Y-%m-%d %H:%M"
            )
            me.cron_start_date = date

        if form["project_cron_edate"]:
            date = datetime.datetime.strptime(
                form["project_cron_edate"], "%Y-%m-%d %H:%M"
            )
            me.cron_end_date = date

    # intv
    if form["project_intv"] == "1":
        me.intv = 1

        me.intv_type = form["project_intv_intv"]
        me.intv_value = form["project_intv_value"]

        if form["project_intv_sdate"]:
            date = datetime.datetime.strptime(
                form["project_intv_sdate"], "%Y-%m-%d %H:%M"
            )
            me.intv_start_date = date

        if form["project_intv_edate"]:
            date = datetime.datetime.strptime(
                form["project_intv_edate"], "%Y-%m-%d %H:%M"
            )
            me.intv_end_date = date

    if form["project_ooff"] == "1":
        me.ooff = 1
        date = (
            datetime.datetime.strptime(form["project_ooff_date"], "%Y-%m-%d %H:%M")
            if form["project_ooff_date"]
            else datetime.date.today()
        )
        me.ooff_date = date

    db.session.add(me)
    db.session.commit()

    return redirect(url_for("project_get", my_id=me.id))


@app.route("/project/<my_id>/remove")
@ldap.login_required
@ldap.group_required(["Analytics"])
def project_remove(my_id):
    """ remove a project """
    cache.clear()
    tasks = [str(x.id) for x in Task.query.filter_by(project_id=my_id).all()]
    jobs = [str(j.args[0]) for j in app.apscheduler.get_jobs()]

    for task_id in list(set(tasks) & set(jobs)):
        for job in app.apscheduler.get_jobs():
            if job.args[0] == task_id:
                log = TaskLog(
                    task_id=task_id,
                    status_id=7,
                    message=g.user_full_name + ": Task removed.",
                )
                db.session.add(log)
                db.session.commit()

                job.remove()

    # delete project. db will cascade delete to tasks and run data.
    Project.query.filter_by(id=my_id).delete()
    db.session.commit()

    return redirect(url_for("project"))
