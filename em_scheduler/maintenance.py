"""Scheduler Maintenance."""
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

from sqlalchemy import update

from em_scheduler.extensions import db, scheduler
from em_scheduler.functions import scheduler_add_task, scheduler_delete_task
from em_scheduler.model import Task


@scheduler.task(
    "interval",
    id="job_sync",
    hours=1,
    max_instances=1,
    start_date="2000-01-01 12:19:00",
)
def job_sync():
    """Job to sync run times between model and scheduler."""
    try:
        with scheduler.app.app_context():

            # remove next run date and duration from disabled jobs
            db.session.execute(
                update(Task)
                .where(
                    Task.enabled == 0
                    and (Task.next_run is not None or Task.est_duration is not None)
                )
                .values(next_run=None, est_duration=None)
            )
            db.session.commit()

            # remove disabled jobs from the scheduler
            scheduler_jobs = scheduler.get_jobs()

            for task in Task.query.filter_by(enabled=0).all():
                for job in scheduler_jobs:
                    if job.args and str(job.args[0]) == str(task.id):
                        job.remove()

            # check that enabled job are scheduled
            scheduler_jobs = scheduler.get_jobs()

            tasks = Task.query.filter_by(enabled=1).all()
            for task in [u.__dict__ for u in tasks]:
                for job in scheduler_jobs:
                    if job.args and str(job.args[0]) == str(task.get("id")):
                        # nested for should use break. otherwise continue
                        break
                else:
                    # add if not found
                    scheduler_add_task(task.get("id"))

            # reschedule enabled jobs that do not have a next run date
            tasks = Task.query.filter_by(enabled=1, next_run=None).all()
            for task in [u.__dict__ for u in tasks]:
                scheduler_delete_task(task.get("id"))
                scheduler_add_task(task.get("id"))

    # pylint: disable=broad-except
    except BaseException as e:
        print(str(e))  # noqa: T001
