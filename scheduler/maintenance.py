"""Scheduler Maintenance."""

from sqlalchemy import update

from scheduler.extensions import atlas_scheduler, db
from scheduler.model import Task


@atlas_scheduler.task(
    "interval",
    id="job_sync",
    hours=1,
    max_instances=1,
    start_date="2000-01-01 12:19:00",
)
def job_sync() -> None:
    """Job to sync run times between model and scheduler."""
    try:
        with atlas_scheduler.app.app_context():

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
            scheduler_jobs = atlas_scheduler.get_jobs()

            for task in Task.query.filter_by(enabled=0).all():
                for job in scheduler_jobs:
                    if job.args and str(job.args[0]) == str(task.id):
                        job.remove()

    # pylint: disable=broad-except
    except BaseException as e:
        print(str(e))  # noqa: T001
