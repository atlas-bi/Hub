"""Scheduler Maintenance."""

from sqlalchemy import update

from scheduler.extensions import db, apscheduler
from scheduler.functions import scheduler_add_task, scheduler_delete_task
from scheduler.model import Task


@apscheduler.task(
    "interval",
    id="job_sync",
    hours=1,
    max_instances=1,
    start_date="2000-01-01 12:19:00",
)
def job_sync() -> None:
    """Job to sync run times between model and scheduler."""
    try:
        with apscheduler.app.app_context():

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
            scheduler_jobs = apscheduler.get_jobs()

            for task in Task.query.filter_by(enabled=0).all():
                for job in scheduler_jobs:
                    if job.args and str(job.args[0]) == str(task.id):
                        job.remove()

            # check that enabled job are scheduled
            scheduler_jobs = apscheduler.get_jobs()

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
