"""Project web views."""

import datetime
from typing import Optional, Union

from crypto import em_encrypt
from flask import Blueprint
from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, text
from werkzeug import Response

from web import cache, db
from web.extensions import get_or_create
from web.model import Project, ProjectParam, Task, TaskFile, TaskLog, User
from web.web import submit_executor

project_bp = Blueprint("project_bp", __name__)


def form_to_date(date_string: Optional[str]) -> Optional[datetime.datetime]:
    """Convert optional date string to date."""
    if date_string:
        return datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M")
    return None


@project_bp.route("/project")
@login_required
def all_projects() -> Union[Response, str]:
    """List all projects."""
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
    return redirect(url_for("project_bp.new_project_form"))


@project_bp.route("/project/user", defaults={"user_id": None})
@project_bp.route("/project/user/<user_id>")
@login_required
def user_projects(user_id: int) -> Union[Response, str]:
    """List projects for a specific user."""
    user_id = user_id or current_user.id
    my_user = User.query.filter_by(id=user_id).first()
    if not my_user:
        flash("That user doesn't exist.")
        return redirect(url_for("project_bp.all_projects"))

    if (
        db.session.query()
        .select_from(Project)
        .add_columns(Project.id)
        .filter(Project.owner_id == user_id)
        .first()
    ):

        return render_template(
            "pages/project/all.html.j2",
            title=my_user.full_name + "'s Projects",
            username=my_user.full_name,
            user_id=user_id,
            user=my_user,
        )

    if current_user.id == user_id:
        flash("You don't have any projects. Get started by creating one.")
    else:
        flash(f"{my_user} doesn't have any projects.")
        return redirect(url_for("project_bp.all_projects"))

    return redirect(url_for("project_bp.new_project_form"))


@project_bp.route("/project/<project_id>", methods=["GET"])
@login_required
def one_project(project_id: int) -> Union[str, Response]:
    """Project detail page."""
    me = Project.query.filter_by(id=project_id).first()

    if me:
        first_task = (
            Task.query.filter_by(project_id=project_id)
            .filter_by(enabled=1)
            .order_by(Task.order.asc(), Task.name.asc())  # type: ignore[attr-defined, union-attr]
            .first()
        )

        return render_template(
            "pages/project/one.html.j2", p=me, title=me.name, task=first_task
        )

    flash("The project does not exist.")
    return redirect(url_for("project_bp.all_projects"))


@project_bp.route("/project/<project_id>/edit", methods=["GET"])
@login_required
def edit_project_form(project_id: int) -> Union[str, Response]:
    """Project editor page."""
    me = Project.query.filter_by(id=project_id).first()

    if me:
        return render_template(
            "pages/project/new.html.j2", p=me, title="Editing " + me.name
        )

    flash("The project does not exist.")
    return redirect(url_for("project_bp.all_projects"))


@project_bp.route("/project/<project_id>/edit", methods=["POST"])
@login_required
def edit_project(project_id: int) -> Response:
    """Save project edits."""
    cache.clear()

    project = get_or_create(db.session, Project, id=project_id)

    # get filter query for update
    me = Project.query.filter_by(id=project.id)

    form = request.form

    me.update(
        dict(  # noqa: C408
            name=form.get("project_name", "undefined", type=str).strip(),
            description=form.get("project_desc", "", type=str),
            owner_id=(
                current_user.id
                if form.get("project_ownership", 0, type=int) == 1
                else me.first().owner_id
            ),
            updater_id=current_user.id,
            sequence_tasks=form.get("run_tasks_in_sequence", 0, type=int),
            cron=form.get("project_cron", 0, type=int),
            cron_year=form.get("project_cron_year", None, type=int),
            cron_month=form.get("project_cron_mnth", None, type=int),
            cron_week=form.get("project_cron_week", None, type=int),
            cron_day=form.get("project_cron_day", None, type=int),
            cron_week_day=form.get("project_cron_wday", None, type=int),
            cron_hour=form.get("project_cron_hour", None, type=int),
            cron_min=form.get("project_cron_min", None, type=int),
            cron_sec=form.get("project_cron_sec", None, type=int),
            cron_start_date=form_to_date(
                form.get("project_cron_sdate", None, type=str)
            ),
            cron_end_date=form_to_date(form.get("project_cron_edate", None, type=str)),
            intv=form.get("project_intv", 0, type=int),
            intv_value=form.get("project_intv_value", None, type=int),
            intv_type=form.get("project_intv_intv", None, type=str),
            intv_start_date=form_to_date(
                form.get("project_intv_sdate", None, type=str)
            ),
            intv_end_date=form_to_date(form.get("project_intv_edate", None, type=str)),
            ooff=form.get("project_ooff", 0, type=int),
            ooff_date=form_to_date(form.get("project_ooff_date", None, type=str)),
        )
    )

    db.session.commit()

    # update params 1. remove old params
    ProjectParam.query.filter_by(project_id=project_id).delete()
    db.session.commit()

    # update params 2. add new params
    for key, value in dict(
        zip(form.getlist("param-key"), form.getlist("param-value"))
    ).items():

        if key:
            db.session.add(
                ProjectParam(
                    project_id=project_id,
                    key=key,
                    value=em_encrypt(value, app.config["PASS_KEY"]),
                )
            )

    db.session.commit()

    # reschedule any jobs.
    submit_executor("schedule_project", project_id)

    flash("Changes saved.")
    return redirect(url_for("project_bp.one_project", project_id=project_id))


@project_bp.route("/project/new", methods=["GET"])
@login_required
def new_project_form() -> str:
    """Create a new project page."""
    return render_template(
        "pages/project/new.html.j2",
        p=Project.query.filter_by(id=0).first(),
        title="New Project",
    )


@project_bp.route("/project/new", methods=["POST"])
@login_required
def new_project() -> Response:
    """Save a new project."""
    cache.clear()
    form = request.form

    # create project
    me = Project(
        name=form.get("project_name", "undefined", type=str).strip(),
        description=form.get("project_desc", "", type=str),
        owner_id=current_user.id,
        creator_id=current_user.id,
        updater_id=current_user.id,
        sequence_tasks=form.get("run_tasks_in_sequence", 0, type=int),
        cron=form.get("project_cron", 0, type=int),
        cron_year=form.get("project_cron_year", None, type=int),
        cron_month=form.get("project_cron_mnth", None, type=int),
        cron_week=form.get("project_cron_week", None, type=int),
        cron_day=form.get("project_cron_day", None, type=int),
        cron_week_day=form.get("project_cron_wday", None, type=int),
        cron_hour=form.get("project_cron_hour", None, type=int),
        cron_min=form.get("project_cron_min", None, type=int),
        cron_sec=form.get("project_cron_sec", None, type=int),
        cron_start_date=form_to_date(form.get("project_cron_sdate", None, type=str)),
        cron_end_date=form_to_date(form.get("project_cron_edate", None, type=str)),
        intv=form.get("project_intv", 0, type=int),
        intv_value=form.get("project_intv_value", None, type=int),
        intv_type=form.get("project_intv_intv", None, type=str),
        intv_start_date=form_to_date(form.get("project_intv_sdate", None, type=str)),
        intv_end_date=form_to_date(form.get("project_intv_edate", None, type=str)),
        ooff=form.get("project_ooff", 0, type=int),
        ooff_date=form_to_date(form.get("project_ooff_date", None, type=str)),
    )

    db.session.add(me)
    db.session.commit()

    # add params
    for key, value in dict(
        zip(form.getlist("param-key"), form.getlist("param-value"))
    ).items():
        if key:
            db.session.add(
                ProjectParam(
                    task_id=me.id,
                    key=key,
                    value=em_encrypt(value, app.config["PASS_KEY"]),
                )
            )

    db.session.commit()

    return redirect(url_for("project_bp.one_project", project_id=me.id))


@project_bp.route("/project/<project_id>/delete")
@login_required
def delete_project(project_id: int) -> Response:
    """Delete a project."""
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

    submit_executor("disable_project", project_id)

    # delete logs
    db.session.query(TaskLog).filter(TaskLog.task_id.in_(tasks)).delete(  # type: ignore[attr-defined, union-attr]
        synchronize_session=False
    )
    db.session.commit()

    # delete file links
    db.session.query(TaskFile).filter(TaskFile.task_id.in_(tasks)).delete(  # type: ignore[attr-defined,union-attr]
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

    flash("Project deleted.")
    return redirect(url_for("project_bp.all_projects"))


@project_bp.route("/project/<project_id>/disable")
@login_required
def disable_all_project_tasks(project_id: int) -> Response:
    """Disable all tasks in a project."""
    submit_executor("disable_project", project_id)

    return redirect(url_for("project_bp.one_project", project_id=project_id))


@project_bp.route("/project/<project_id>/enable")
@login_required
def enable_all_project_tasks(project_id: int) -> Response:
    """Enable all tasks in a project."""
    submit_executor("enable_project", project_id)

    return redirect(url_for("project_bp.one_project", project_id=project_id))


@project_bp.route("/project/<project_id>/run")
@login_required
def run_all_project_tasks(project_id: int) -> Response:
    """Run all tasks in a project."""
    submit_executor("run_project", project_id)

    return redirect(url_for("project_bp.one_project", project_id=project_id))
