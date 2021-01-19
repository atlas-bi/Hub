"""Dashboard web views."""
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


import json
import sys
from pathlib import Path

import requests
from flask import Blueprint
from flask import current_app as app
from flask import flash, redirect, render_template, session, url_for

from em_web import db, ldap
from em_web.model import TaskLog
from em_web.web import submit_executor

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from error_print import full_stack

dashboard_bp = Blueprint("dashboard_bp", __name__)


@dashboard_bp.route("/")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash():
    """Home page.

    :url: /
    :returns: html webpage.
    """
    return render_template("pages/dashboard/dashboard.html.j2", title="Dashboard")


@dashboard_bp.route("/dash/errorGauge")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_error_gauge():
    """Guage showing number of errored tasks.

    :url: /dash/errorGauge
    :returns: html webpage.
    """
    success = db.session.execute(
        """
        select
            case when success > 0 and error > 0
                     then 1.00 - round(cast(error as decimal) / cast(success as decimal),2)
                 when error > 0 or success = 0
                     then 0
             else 1 end accuracy
        from
            (
                select
                    count(1) error
                from (
                    select
                        1
                    from
                        task_log t
                    where
                        status_date > now() - interval '72 hour'
                    and task_id is not null
                    and job_id is not null
                    and error=1
                    group by task_id
                ) as t
            ) as e
            , (
                select
                    count(1) success
                from
                    task_log t
                where
                    status_date > now() - interval '72 hour'
                and task_id is not null
                and job_id is not null
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


@dashboard_bp.route("/dash/runGauge")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_run_gauge():
    """Guage showing number of tasks run.

    :url: /dash/runGauge
    :returns: html webpage.
    """
    runs = db.session.execute(
        """
        select
            count(1)
        from
            task_log t
        where
            status_date > now() - interval '72 hour'
        and task_id is not null
        and job_id is not null
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


@dashboard_bp.route("/dash/orphans/delete")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_orphans_delete():
    """Button to delete any jobs without a linked tasks.

    :url: /dash/orphans/delete
    :returns: redirects to dashboard.
    """
    # pylint: disable=broad-except
    try:
        output = json.loads(
            requests.get(app.config["SCHEUDULER_HOST"] + "/delete-orphans").text
        )
        if output.get("error"):
            raise ValueError(output["error"])

        msg = output["message"]
        add_user_log(msg, 0)

    except ValueError as e:
        msg = str(e)
        add_user_log(str(e), 1)

    except requests.exceptions.ConnectionError:
        msg = "Failed to delete orphans. EM_Scheduler offline."
        add_user_log(msg, 1)

    except BaseException:
        msg = "Scheduler failed to delete orphans.\n" + str(full_stack())
        add_user_log(msg, 1)

    flash(msg)

    return redirect(url_for("dashboard_bp.dash"))


@dashboard_bp.route("/dash/errored/run")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_errored_run():
    """Button to run all errored tasks.

    :url: /dash/errored/run
    :returns: redirects to dashboard.
    """
    submit_executor("run_errored_tasks")

    return redirect(url_for("dashboard_bp.dash"))


@dashboard_bp.route("/dash/errored/schedule")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_errored_schedule():
    """Button to schedule all errored tasks.

    :url: /dash/errored/schedule
    :returns: redirects to dashboard.
    """
    submit_executor("schedule_errored_tasks")

    return redirect(url_for("dashboard_bp.dash"))


@dashboard_bp.route("/dash/scheduled/run")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_scheduled_run():
    """Button to run all scheduled tasks.

    :url: /dash/scheduled/run
    :returns: redirects to dashboard.
    """
    submit_executor("run_scheduled_tasks")

    return redirect(url_for("dashboard_bp.dash"))


@dashboard_bp.route("/dash/scheduled/reschedule")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_scheduled_reschedule():
    """Button to reschedule all scheduled tasks.

    :url: /dash/scheduled/reschedule
    :returns: redirects to dashboard.
    """
    submit_executor("rescheduled_scheduled_tasks")

    return redirect(url_for("dashboard_bp.dash"))


@dashboard_bp.route("/dash/scheduled/disable")
@ldap.login_required
@ldap.group_required(["Analytics"])
def dash_scheduled_disable():
    """Button to disable all scheduled tasks.

    :url: /dash/scheduled/disable
    :returns: redirects to dashboard.
    """
    submit_executor("disabled_scheduled_tasks")

    return redirect(url_for("dashboard_bp.dash"))


def add_user_log(message, error_code):
    """Add log entry prefixed by username.

    :param message str: message to save
    :param error_code: 1 (error) or 0 (no error)
    """
    log = TaskLog(
        status_id=7,
        error=error_code,
        message=session.get("user_full_name") + ": " + message,
    )
    db.session.add(log)
    db.session.commit()
