"""Project web views."""

import datetime
from typing import Optional, Union

from cron_descriptor import ExpressionDescriptor
from cron_validator import CronValidator
from crypto import em_encrypt
from flask import Blueprint
from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import text
from sqlalchemy.sql import functions as func
from werkzeug import Response

from web import cache, db
from web.model import Project, ProjectParam, Task, TaskFile, TaskLog, TaskParam, User
from web.web import submit_executor

from . import get_or_create
from .executors import disable_project

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
        return render_template("pages/project/all.html.j2", title="Projects", owners=owners)
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
        try:
            desc = ExpressionDescriptor(
                cron_year=me.cron_year,
                cron_month=me.cron_month,
                cron_week=me.cron_week,
                cron_day=me.cron_day,
                cron_week_day=me.cron_week_day,
                cron_hour=me.cron_hour,
                cron_min=me.cron_min,
                cron_sec=me.cron_sec,
            ).get_full_description()
        except ValueError as e:
            desc = e

        return render_template(
            "pages/project/one.html.j2",
            p=me,
            has_secrets=any(p.sensitive == 1 for p in me.params),
            title=me.name,
            task=first_task,
            cron_desc=desc,
        )

    flash("The project does not exist.")
    return redirect(url_for("project_bp.all_projects"))


@project_bp.route("/project/<project_id>/edit", methods=["GET"])
@login_required
def edit_project_form(project_id: int) -> Union[str, Response]:
    """Project editor page."""
    me = Project.query.filter_by(id=project_id).first()

    if me:
        return render_template("pages/project/new.html.j2", p=me, title="Editing " + me.name)

    flash("The project does not exist.")
    return redirect(url_for("project_bp.all_projects"))


@project_bp.route("/project/<project_id>/edit", methods=["POST"])
@login_required
def edit_project(project_id: int) -> Union[str, Response]:
    """Save project edits."""
    cache.clear()
    error = None
    project = get_or_create(db.session, Project, id=project_id)

    # get filter query for update
    me = Project.query.filter_by(id=project.id)
    me2 = Project.query.filter_by(id=project_id).first()
    form = request.form
    cron = form.get("project_cron", 0, type=int)
    cron_year = form.get("project_cron_year", None, type=str)
    cron_month = form.get("project_cron_mnth", None, type=str)
    cron_week = form.get("project_cron_week", None, type=str)
    cron_day = form.get("project_cron_day", None, type=str)
    cron_week_day = form.get("project_cron_wday", None, type=str)
    cron_hour = form.get("project_cron_hour", None, type=str)
    cron_min = form.get("project_cron_min", None, type=str)
    cron_sec = form.get("project_cron_sec", None, type=str)
    if cron == 1:
        try:
            CronValidator(
                cron=cron,
                cron_year=cron_year,
                cron_month=cron_month,
                cron_week=cron_week,
                cron_day=cron_day,
                cron_week_day=cron_week_day,
                cron_hour=cron_hour,
                cron_min=cron_min,
                cron_sec=cron_sec,
            ).validate()

        except ValueError as e:
            error = str(e)
            return render_template(
                "pages/project/new.html.j2",
                p=me2,
                title="Editing " + me2.name,
                error=error,
            )
    # pylint: disable=R1735
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
            cron=cron,
            cron_year=cron_year,
            cron_month=cron_month,
            cron_week=cron_week,
            cron_day=cron_day,
            cron_week_day=cron_week_day,
            cron_hour=cron_hour,
            cron_min=cron_min,
            cron_sec=cron_sec,
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
    )

    db.session.commit()

    # update params 1. remove old params
    ProjectParam.query.filter_by(project_id=project_id).delete()
    db.session.commit()

    # update params 2. add new params
    for param in list(
        zip(
            form.getlist("param-key"),
            form.getlist("param-value"),
            form.getlist("param-sensitive"),
        )
    ):
        if param[0]:
            db.session.add(
                ProjectParam(
                    project_id=project_id,
                    key=param[0],
                    value=em_encrypt(param[1], app.config["PASS_KEY"]),
                    sensitive=int(param[2] or 0),
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
def new_project() -> Union[str, Response]:
    """Save a new project."""
    cache.clear()
    error = None
    form = request.form
    cron = form.get("project_cron", 0, type=int)
    cron_year = form.get("project_cron_year", None, type=str)
    cron_month = form.get("project_cron_mnth", None, type=str)
    cron_week = form.get("project_cron_week", None, type=str)
    cron_day = form.get("project_cron_day", None, type=str)
    cron_week_day = form.get("project_cron_wday", None, type=str)
    cron_hour = form.get("project_cron_hour", None, type=str)
    cron_min = form.get("project_cron_min", None, type=str)
    cron_sec = form.get("project_cron_sec", None, type=str)

    if cron == 1:
        try:
            CronValidator(
                cron=cron,
                cron_year=cron_year,
                cron_month=cron_month,
                cron_week=cron_week,
                cron_day=cron_day,
                cron_week_day=cron_week_day,
                cron_hour=cron_hour,
                cron_min=cron_min,
                cron_sec=cron_sec,
            ).validate()

        except ValueError as e:
            error = str(e)
            return render_template(
                "pages/project/new.html.j2",
                p=Project.query.filter_by(id=0).first(),
                title="New Project",
                error=error,
            )

    # create project
    me = Project(
        name=form.get("project_name", "undefined", type=str).strip(),
        description=form.get("project_desc", "", type=str),
        owner_id=current_user.id,
        creator_id=current_user.id,
        updater_id=current_user.id,
        sequence_tasks=form.get("run_tasks_in_sequence", 0, type=int),
        cron=cron,
        cron_year=cron_year,
        cron_month=cron_month,
        cron_week=cron_week,
        cron_day=cron_day,
        cron_week_day=cron_week_day,
        cron_hour=cron_hour,
        cron_min=cron_min,
        cron_sec=cron_sec,
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
    for param in list(
        zip(
            form.getlist("param-key"),
            form.getlist("param-value"),
            form.getlist("param-sensitive"),
        )
    ):
        if param[0]:
            db.session.add(
                ProjectParam(
                    project_id=me.id,
                    key=param[0],
                    value=em_encrypt(param[1], app.config["PASS_KEY"]),
                    sensitive=int(param[2] or 0),
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

    # must wait for this to complete before deleting
    disable_project([project_id])

    # delete logs
    db.session.query(TaskLog).filter(TaskLog.task_id.in_(tasks)).delete(  # type: ignore[attr-defined, union-attr]
        synchronize_session=False
    )
    db.session.commit()

    # delete file links
    db.session.query(TaskFile).filter(TaskFile.task_id.in_(tasks)).delete(  # type: ignore[attr-defined,union-attr]
        synchronize_session=False
    )
    db.session.commit()

    # delete task params
    db.session.query(TaskParam).filter(TaskParam.task_id.in_(tasks)).delete(  # type: ignore[attr-defined,union-attr]
        synchronize_session=False
    )
    db.session.commit()

    # delete tasks
    db.session.query(Task).filter(Task.project_id == project_id).delete(synchronize_session=False)
    db.session.commit()

    # delete params
    ProjectParam.query.filter_by(project_id=project_id).delete(synchronize_session=False)
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


@project_bp.route("/project/<project_id>/duplicate")
@login_required
def duplicate_project(project_id: int) -> Response:
    """Duplicate a project."""
    my_project = Project.query.filter_by(id=project_id).first()
    # pylint: disable=R1702
    if my_project:
        my_project_copy = Project()

        # pylint: disable=protected-access
        for key in my_project_copy.__table__.columns.keys():
            if key not in ["id", "owner_id"]:
                setattr(my_project_copy, key, getattr(my_project, key))

        my_project_copy.creator_id = current_user.id
        my_project_copy.owner_id = current_user.id
        my_project_copy.updater_id = current_user.id
        my_project_copy.name = str(my_project.name or "") + " - Duplicated"

        db.session.add(my_project_copy)
        db.session.commit()

        # copy parameters
        for my_param in ProjectParam.query.filter_by(project_id=project_id).all():
            if my_param:
                new_param = ProjectParam()
                for key in my_param.__table__.columns.keys():
                    if key not in ["id", "project_id"]:
                        setattr(new_param, key, getattr(my_param, key))

                new_param.project_id = my_project_copy.id
                db.session.add(new_param)
                db.session.commit()

        # copy the tasks
        for my_task in Task.query.filter_by(project_id=project_id).all():
            if my_task:
                new_task = Task()

                # pylint: disable=protected-access
                for key in my_task.__table__.columns.keys():
                    if key not in [
                        "id",
                        "last_run",
                        "last_run_job_id",
                        "status_id",
                        "project_id",
                    ]:
                        setattr(new_task, key, getattr(my_task, key))

                new_task.enabled = 0
                new_task.creator_id = current_user.id
                new_task.updater_id = current_user.id
                new_task.status_id = None
                new_task.project_id = my_project_copy.id
                new_task.name = str(my_task.name or "")

                db.session.add(new_task)
                db.session.commit()

                # copy parameters
                for my_param in TaskParam.query.filter_by(task_id=my_task.id).all():
                    if my_param:
                        new_param = TaskParam()
                        for key in my_param.__table__.columns.keys():
                            if key not in ["id", "task_id"]:
                                setattr(new_param, key, getattr(my_param, key))

                        new_param.task_id = new_task.id
                        db.session.add(new_param)
                        db.session.commit()

        return redirect(url_for("project_bp.one_project", project_id=my_project_copy.id))

    flash("Project does not exist.")
    return redirect(url_for("project_bp.all_projects"))


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
