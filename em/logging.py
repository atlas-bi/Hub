"""
    Scheduler event logging.

    These logs will only be from scheduler events (starting/stoping/etc)
    and not from the actual details of the run.

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
from apscheduler.events import (
    EVENT_SCHEDULER_STARTED,
    EVENT_SCHEDULER_SHUTDOWN,
    EVENT_SCHEDULER_PAUSED,
    EVENT_SCHEDULER_RESUMED,
    EVENT_EXECUTOR_ADDED,
    EVENT_EXECUTOR_REMOVED,
    EVENT_JOBSTORE_ADDED,
    EVENT_JOBSTORE_REMOVED,
    EVENT_ALL_JOBS_REMOVED,
    EVENT_JOB_ADDED,
    EVENT_JOB_REMOVED,
    EVENT_JOB_MODIFIED,
    EVENT_JOB_SUBMITTED,
    EVENT_JOB_MAX_INSTANCES,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED,
)

from em import app, db
from .model.model import TaskLog, Task


def event_log():
    """
    each type of event has a trigger assigned to a callback function
    """

    def job_missed(event):
        # print(
        #     " -- -- -- job missed",
        #     event,
        #     event.code,
        #     event.job_id,
        #     event.jobstore,
        #     event.scheduled_run_time,
        #     event.retval,
        #     event.exception,
        #     event.traceback,
        # )
        job = app.apscheduler.get_job(event.job_id)
        if job:
            task = Task.query.filter_by(id=job.args[0]).first()
            ex_time = (
                datetime.datetime.now(datetime.timezone.utc) - event.scheduled_run_time
            )

            log = TaskLog(
                task_id=task.id if task else event.job_id,
                status_id=6,
                error=1,
                message="Job missed. Scheduled for: "
                + datetime.datetime.strftime(
                    event.scheduled_run_time,
                    "%a, %b %-d, %Y %H:%M:%S",
                )
                + ". Missed by : "
                + str(ex_time),
            )
            db.session.add(log)
            db.session.commit()

    app.apscheduler.add_listener(job_missed, EVENT_JOB_MISSED)

    def job_error(event):
        # print(
        #     " -- -- -- job error",
        #     event,
        #     event.code,
        #     event.job_id,
        #     event.jobstore,
        #     event.scheduled_run_time,
        #     event.retval,
        #     event.exception,
        #     event.traceback,
        # )
        job = app.apscheduler.get_job(event.job_id)
        if job:
            task = Task.query.filter_by(id=job.args[0]).first()
            ex_time = (
                datetime.datetime.now(datetime.timezone.utc) - event.scheduled_run_time
            )

            log = TaskLog(
                task_id=task.id if task else event.job_id,
                job_id=task.last_run_job_id or "",
                status_id=6,
                error=1,
                message="Job error. Scheduled for: "
                + datetime.datetime.strftime(
                    event.scheduled_run_time,
                    "%a, %b %-d, %Y %H:%M:%S",
                )
                + ". Execution time: "
                + str(ex_time)
                + " error: "
                + str(event.exception)
                + " trace: "
                + str(event.traceback),
            )
            task.status_id = 2
            db.session.add(log)
            db.session.commit()

    app.apscheduler.add_listener(job_error, EVENT_JOB_ERROR)

    def job_executed(event):
        # print(
        #     " -- -- -- job excecuted",
        #     event,
        #     event.code,
        #     event.job_id,
        #     event.jobstore,
        #     event.scheduled_run_time,
        #     event.retval,
        #     event.exception,
        #     event.traceback,
        # )

        job = app.apscheduler.get_job(event.job_id)
        task = Task.query.filter_by(
            id=job.args[0] if job else event.job_id.split("-")[1]
        ).first()
        ex_time = (
            datetime.datetime.now(datetime.timezone.utc) - event.scheduled_run_time
        )

        log = TaskLog(
            task_id=task.id if task else event.job_id,
            job_id=task.last_run_job_id or "",
            status_id=6,
            message="Job excecuted in " + str(ex_time) + ".",
        )
        db.session.add(log)
        db.session.commit()

    app.apscheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)

    def job_added(event):
        # code, alias
        # print(
        #     " -- -- -- job added",
        #     event,
        #     event.code,
        #     event.job_id,

        # )
        job = app.apscheduler.get_job(event.job_id)
        task = Task.query.filter_by(id=job.args[0]).first()

        log = TaskLog(
            task_id=task.id if task else event.job_id,
            status_id=6,
            error=(0 if job.next_run_time else 1),
            message=(
                "Job added. Scheduled for: "
                + datetime.datetime.strftime(
                    job.next_run_time,
                    "%a, %b %-d, %Y %H:%M:%S",
                )
                if job.next_run_time
                else "Job could not be scheduled. Verify project has currect and valid schedule."
            ),
        )
        db.session.add(log)
        db.session.commit()

    app.apscheduler.add_listener(job_added, EVENT_JOB_ADDED)

    def job_removed(event):
        # print(
        #     " -- -- -- job removed", event, event.code, event.job_id,
        # )
        task = Task.query.filter_by(id=event.job_id.split("-")[1]).first()

        log = TaskLog(
            task_id=task.id if task else event.job_id,
            status_id=6,
            message="Job removed.",
        )
        db.session.add(log)
        db.session.commit()

    app.apscheduler.add_listener(job_removed, EVENT_JOB_REMOVED)

    # def job_modified(event):
    #     # code, alias
    #     print(
    #         " -- -- -- job modified", event, event.code, event.job_id,
    #     )

    # app.apscheduler.add_listener(job_modified, EVENT_JOB_MODIFIED)

    def job_submitted(event):
        # print(
        #     " -- -- -- job submitted", event, event.code, event.job_id, event.jobstore
        # )
        job = app.apscheduler.get_job(event.job_id)
        task = Task.query.filter_by(
            id=job.args[0] if job else event.job_id.split("-")[1]
        ).first()

        log = TaskLog(
            task_id=task.id if task else event.job_id,
            status_id=6,
            message="Job submitted.",
        )
        db.session.add(log)
        db.session.commit()

    app.apscheduler.add_listener(job_submitted, EVENT_JOB_SUBMITTED)

    # def job_max_instances(event):
    #     print(
    #         " -- -- -- job max instances",
    #         event,
    #         event.code,
    #         event.job_id,
    #         event.jobstore,
    #     )
    #     # code, job_id, jobstore

    # app.apscheduler.add_listener(job_max_instances, EVENT_JOB_MAX_INSTANCES)

    # def scheduler_started(event):
    #     print(" -- -- -- scheduler started", event, event.code, event.alias)

    # app.apscheduler.add_listener(scheduler_started, EVENT_SCHEDULER_STARTED)

    # def scheduler_shutdown(event):
    #     print(" -- -- -- scheduler shutdown", event, event.code, event.alias)

    # app.apscheduler.add_listener(scheduler_shutdown, EVENT_SCHEDULER_SHUTDOWN)

    # def scheduler_paused(event):
    #     print(" -- -- -- scheduler paused", event, event.code, event.alias)

    # app.apscheduler.add_listener(scheduler_paused, EVENT_SCHEDULER_PAUSED)

    # def scheduler_resumed(event):
    #     print(" -- -- -- scheduler resumed", event, event.code, event.alias)

    # app.apscheduler.add_listener(scheduler_resumed, EVENT_SCHEDULER_RESUMED)

    # def executor_added(event):
    #     print(" -- -- -- executor added", event, event.code, event.alias)

    # app.apscheduler.add_listener(executor_added, EVENT_EXECUTOR_ADDED)

    # def executor_removed(event):
    #     print(" -- -- -- executor removed", event, event.code, event.alias)

    # app.apscheduler.add_listener(executor_removed, EVENT_EXECUTOR_REMOVED)

    # def jobstore_added(event):
    #     print(" -- -- -- jobstore added", event, event.code, event.alias)

    # app.apscheduler.add_listener(jobstore_added, EVENT_JOBSTORE_ADDED)

    # def jobstore_removed(event):
    #     print(" -- -- -- jobstore removed", event, event.code, event.alias)

    # app.apscheduler.add_listener(jobstore_removed, EVENT_JOBSTORE_REMOVED)

    # def all_jobs_removed(event):
    #     print(" -- -- -- all jobs removed", event, event.code, event.alias)

    # app.apscheduler.add_listener(all_jobs_removed, EVENT_ALL_JOBS_REMOVED)
