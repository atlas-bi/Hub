"""Project web views."""
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

import requests
from flask import Blueprint
from flask import current_app as app
from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, text

from em_web import cache, db
from em_web.model import Project, Task, TaskFile, TaskLog, User

project_bp = Blueprint("project_bp", __name__)


@project_bp.route("/project")
@login_required
def project():
    """List all projects.

    :url: /project

    :returns: html page for projects. If no projects exist then redirect to new project page.
    """
    if db.session.query().select_from(Project).add_columns(Project.id).first():
        owners = (
            db.session.query()
            .select_from(User)
            .join(Project, Project.owner_id == User.id)
            .add_columns(User.full_name, User.id, func.count(Project.id))
            .group_by(User.full_name, User.id)
            .all()
        )
        return render_template(
            "pages/project/all.html.j2", title="Projects", owners=owners
        )
    return redirect(url_for("project_bp.project_new"))


@project_bp.route("/project/user", defaults={"user_id": None})
@project_bp.route("/project/user/<user_id>")
@login_required
def project_user(user_id):
    """List projects for a specific user.

    :url: /project/user *or* /project/user/<user_id>
    :param user_id: id of project owner

    :returns: html page for projects. If no projects exist then redirect to new project page.
    """
    my_user = User.query.filter_by(id=current_user.id)

    if my_user.count():
        user_id = (
            user_id
            or (
                db.session.query()
                .select_from(User)
                .add_columns(User.id)
                .filter(User.id == current_user.id)
                .first()
            )[0]
        )

        if (
            db.session.query()
            .select_from(Project)
            .add_columns(Project.id)
            .filter(Project.owner_id == user_id)
            .first()
        ):

            my_user = User.query.filter_by(id=user_id).first()

            return render_template(
                "pages/project/all.html.j2",
                title=my_user.full_name + "'s Projects",
                username=my_user.full_name,
                user_id=user_id,
            )

    return redirect(url_for("project_bp.project_new"))


@project_bp.route("/project/<project_id>", methods=["GET"])
@login_required
def project_get(project_id):
    """Project detail page.

    :url: /project/<project_id>
    :param project_id: id of the project

    :returns: html page for project details, or error page if project id was invalid.
    """
    me = Project.query.filter_by(id=project_id).first()

    if me:
        return render_template("pages/project/details.html.j2", p=me, title=me.name)

    return render_template("pages/project/details.html.j2", invalid=True, title="Error")


@project_bp.route("/project/<project_id>/edit", methods=["GET"])
@login_required
def project_edit_get(project_id):
    """Project editor page.

    :url: project/project_id/edit [get]
    :param project_id: id of the project

    :returns: html page for project editor, or error page if project id was invalid.
    """
    me = Project.query.filter_by(id=project_id).first()

    if me:
        return render_template(
            "pages/project/new.html.j2", p=me, title="Editing " + me.name
        )

    return render_template("pages/project/details.html.j2", invalid=True, title="Error")


@project_bp.route("/project/<project_id>/edit", methods=["POST"])
@login_required
def project_edit_post(project_id):
    """Save project edits.

    :url: /project/<project_id>/edit [post]
    :param project_id: id of the project

    :returns: redirects to project details page.
    """
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    cache.clear()

    me = Project.query.filter_by(id=project_id).first()
    if not me:
        return redirect(url_for("project_bp.project_get", project_id=project_id))

    if User.query.filter_by(id=current_user.id).count():
        updater = User.query.filter_by(id=current_user.id).first()
        updater.full_name = current_user.full_name or "none"
    else:
        updater = User(
            id=current_user.id,
            full_name=(current_user.full_name or "none"),
        )

    form = request.form

    me.name = form["project_name"].strip()
    me.description = form["project_desc"]
    me.updater_id = updater.id
    me.global_params = form.get("globalParams") or ""

    if form.get("project_ownership") == "1":
        me.owner_id = updater.id

    # add triggers
    # cron
    if form.get("project_cron") == "1":
        me.cron = 1

        if form["project_cron_year"].isdigit() and form["project_cron_year"] != "0":
            me.cron_year = int(form["project_cron_year"])
        else:
            me.cron_year = None

        if form["project_cron_mnth"].isdigit() and form["project_cron_mnth"] != "0":
            me.cron_month = int(form["project_cron_mnth"])
        else:
            me.cron_month = None

        if form["project_cron_week"].isdigit() and form["project_cron_week"] != "0":
            me.cron_week = int(form["project_cron_week"])
        else:
            me.cron_week = None

        if form["project_cron_day"].isdigit() and form["project_cron_day"] != "0":
            me.cron_day = int(form["project_cron_day"])
        else:
            me.cron_day = None

        if form["project_cron_wday"].isdigit():
            me.cron_week_day = int(form["project_cron_wday"])
        else:
            me.cron_week_day = None

        if form["project_cron_hour"].isdigit():
            me.cron_hour = int(form["project_cron_hour"])
        else:
            me.cron_hour = None

        if form["project_cron_min"].isdigit():
            me.cron_min = int(form["project_cron_min"])
        else:
            me.cron_min = None

        if form["project_cron_sec"].isdigit():
            me.cron_sec = int(form["project_cron_sec"])
        else:
            me.cron_sec = None

        if form["project_cron_sdate"]:
            date = datetime.datetime.strptime(
                form["project_cron_sdate"], "%Y-%m-%d %H:%M"
            )
            me.cron_start_date = date
        else:
            me.cron_start_date = None

        if form["project_cron_edate"]:
            date = datetime.datetime.strptime(
                form["project_cron_edate"], "%Y-%m-%d %H:%M"
            )
            me.cron_end_date = date
        else:
            me.cron_end_date = None

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
        else:
            me.intv_start_date = None

        if form["project_intv_edate"]:
            date = datetime.datetime.strptime(
                form["project_intv_edate"], "%Y-%m-%d %H:%M"
            )
            me.intv_end_date = date
        else:
            me.intv_end_date = None
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
    tasks = Task.query.filter_by(project_id=project_id, enabled=1).all()
    for task in tasks:
        log = TaskLog(
            task_id=task.id,
            status_id=7,
            message=(current_user.full_name or "none") + ": Task rescheduled.",
        )
        db.session.add(log)
        db.session.commit()
        requests.get(app.config["SCHEUDULER_HOST"] + "/add/" + str(task.id))

    return redirect(url_for("project_bp.project_get", project_id=project_id))


@project_bp.route("/project/new", methods=["GET"])
@login_required
@cache.cached(timeout=120)
def project_new_form():
    """Create a new project page.

    :url: /project/new [get]

    :returns: html page for new project.
    """
    return render_template(
        "pages/project/new.html.j2",
        p=Project.query.filter_by(id=0).first(),
        title="New Project",
    )


@project_bp.route("/project/new", methods=["POST"])
@login_required
def project_new():
    """Save a new project.

    :url: /project/new [post]

    :returns: html page for project details.
    """
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    cache.clear()
    form = request.form

    project_name = form["project_name"].strip()
    project_desc = form["project_desc"]
    project_params = form.get("globalParams") or ""

    # create owner record
    if User.query.filter_by(id=current_user.id).count():
        owner = User.query.filter_by(id=current_user.id).first()
        owner.full_name = current_user.full_name or "none"
    else:
        owner = User(
            id=current_user.id,
            full_name=(current_user.full_name or "none"),
        )

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

    return redirect(url_for("project_bp.project_get", project_id=me.id))


@project_bp.route("/project/<project_id>/delete")
@login_required
def project_delete(project_id):
    """Delete a project.

    :url: /project/<project_id>/delete
    :param project_id: id of project to delete

    :returns: redirects to all project page.
    """
    cache.clear()

    # get tasks
    tasks = [
        x[0]
        for x in (
            db.session.query()
            .select_from(Task)
            .filter(Task.project_id == project_id)
            .add_columns(text("task.id"))
            .all()
        )
    ]

    for task in tasks:
        try:
            requests.get(app.config["SCHEUDULER_HOST"] + "/delete/" + str(task))
            log = TaskLog(
                task_id=task,
                status_id=7,
                message=(current_user.full_name or "none") + ": Task deleted.",
            )
            db.session.add(log)
            db.session.commit()
        # pylint: disable=broad-except
        except BaseException as e:
            log = TaskLog(
                task_id=task,
                status_id=7,
                error=1,
                message=(current_user.full_name or "none")
                + ": Failed to delete task.\n"
                + str(e),
            )
            db.session.add(log)
            db.session.commit()

    # delete logs
    db.session.query(TaskLog).filter(TaskLog.task_id.in_(tasks)).delete(
        synchronize_session=False
    )
    db.session.commit()

    # delete file links
    db.session.query(TaskFile).filter(TaskFile.task_id.in_(tasks)).delete(
        synchronize_session=False
    )

    # delete tasks
    db.session.query(Task).filter(Task.project_id == project_id).delete(
        synchronize_session=False
    )
    db.session.commit()

    # delete project
    Project.query.filter_by(id=project_id).delete(synchronize_session=False)
    db.session.commit()

    return redirect(url_for("project_bp.project"))


@project_bp.route("/project/<project_id>/disable")
@login_required
def disable_all_project_tasks(project_id):
    """Disable all tasks in a project.

    :url: /project/<project_id>/task/disable
    :param project_id: id of project owning the tasks

    :returns: redirects to the project details page.
    """
    tasks = Task.query.filter_by(project_id=project_id).all()
    for task in tasks:
        task.enabled = 0
        task.next_run = None
        db.session.commit()

        try:
            requests.get(app.config["SCHEUDULER_HOST"] + "/delete/" + str(task.id))

            log = TaskLog(
                task_id=task.id,
                status_id=7,
                message=(current_user.full_name or "none") + ": Task disabled.",
            )
            db.session.add(log)
            db.session.commit()

        # pylint: disable=broad-except
        except BaseException as e:
            log = TaskLog(
                task_id=task.id,
                status_id=7,
                message=(current_user.full_name or "none")
                + ": Failed to disable task.\n"
                + str(e),
            )
            db.session.add(log)
            db.session.commit()

    return redirect(url_for("project_bp.project_get", project_id=project_id))


@project_bp.route("/project/<project_id>/enable")
@login_required
def enable_all_project_tasks(project_id):
    """Enable all tasks in a project.

    :url: /project/<project_id>/task/enable
    :param project_id: id of project owning the tasks

    :returns: redirects to the project details page.
    """
    tasks = Task.query.filter_by(project_id=project_id).all()
    for task in tasks:

        try:
            requests.get(app.config["SCHEUDULER_HOST"] + "/add/" + str(task.id))

            log = TaskLog(
                task_id=task.id,
                status_id=7,
                message=(current_user.full_name or "none") + ": Task enabled.",
            )
            db.session.add(log)
            db.session.commit()

        # pylint: disable=broad-except
        except BaseException as e:
            log = TaskLog(
                task_id=task.id,
                status_id=7,
                message=(current_user.full_name or "none")
                + ": Failed to enable task.\n"
                + str(e),
            )
            db.session.add(log)
            db.session.commit()

    return redirect(url_for("project_bp.project_get", project_id=project_id))


@project_bp.route("/project/<project_id>/run")
@login_required
def run_all_project_tasks(project_id):
    """Run all tasks in a project.

    :url: /project/<project_id>/task/run
    :param project_id: id of project owning the tasks

    :returns: redirects to the project details page.
    """
    tasks = Task.query.filter_by(project_id=project_id, enabled=1).all()
    for task in tasks:
        try:
            requests.get(app.config["SCHEUDULER_HOST"] + "/run/" + str(task.id))

            log = TaskLog(
                task_id=task.id,
                status_id=7,
                message=(current_user.full_name or "none") + ": Task manually run.",
            )
            db.session.add(log)
            db.session.commit()
        # pylint: disable=broad-except
        except BaseException as e:
            log = TaskLog(
                task_id=task.id,
                status_id=7,
                message=(current_user.full_name or "none")
                + ": Failed to run task.\n"
                + str(e),
            )
            db.session.add(log)
            db.session.commit()

    return redirect(url_for("project_bp.project_get", project_id=project_id))
