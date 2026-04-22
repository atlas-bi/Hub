"""Exception and logging messages."""

import datetime
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import requests
from flask import current_app as app
from jinja2 import Environment, PackageLoader, select_autoescape

from runner.extensions import db, redis_client
from runner.model import Task, TaskLog
from runner.scripts.em_smtp import Smtp
from runner.web.filters import datetime_format

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from error_print import full_stack


class RunnerException(Exception):
    """Log exceptions and handle."""

    def __init__(
        self,
        task: Task,
        run_id: Optional[str],
        source_id: int,
        message: Union[ValueError, str],
    ) -> None:
        """Set up class."""
        # set to errored
        task.status_id = 2
        task.last_run = datetime.datetime.now()
        db.session.commit()

        # add log
        log = TaskLog(
            task_id=task.id,
            job_id=run_id,
            error=1,
            status_id=source_id,  # 18 = system
            message=f"{message}\nFull trace:\n" + full_stack(),
        )
        db.session.add(log)
        db.session.commit()
        super().__init__(message)

        # log a cancellation message from the runner.
        log = TaskLog(
            task_id=task.id,
            job_id=run_id,
            status_id=8,
            error=1,
            message="Task cancelled.",
        )
        db.session.add(log)
        db.session.commit()

        if task.email_error == 1 and task.email_error_recipients:
            env = Environment(
                loader=PackageLoader("runner", "templates"),
                autoescape=select_autoescape(["html", "xml"]),
            )

            env.filters["datetime_format"] = datetime_format

            # get logs
            logs = (
                TaskLog.query.filter_by(task_id=task.id, job_id=run_id)
                .order_by(TaskLog.status_date)
                .all()
            )

            RunnerLog(task, run_id, 8, "Sending error email.")
            date = datetime.datetime.now()

            try:
                template = env.get_template("email/email.html.j2")
            except BaseException as e:
                RunnerLog(
                    task,
                    run_id,
                    8,
                    f"Failed to get email template.\n{e}\n{full_stack()}",
                    1,
                )
                raise

            subject = "Error in Project: %s / Task: %s / Run: %s %s" % (
                task.project.name,
                task.name,
                run_id,
                date,
            )

            if task.email_error_subject:
                subject = task.email_error_subject

            try:
                Smtp(
                    task=task,
                    run_id=run_id,
                    recipients=task.email_error_recipients,
                    subject=subject,
                    message=template.render(
                        task=task,
                        success=0,
                        date=date,
                        logs=logs,
                        org=app.config["ORG_NAME"],
                    ),
                    short_message=task.email_error_message or f"Atlas Hub task {task} failed.",
                    attachments=[],
                )
            except BaseException as e:
                RunnerLog(
                    task,
                    run_id,
                    8,
                    f"Failed to get send error email.\n{e}\n{full_stack()}",
                    1,
                )
                raise

        # if the error is coming from a run, we may need to trigger a retry.
        if run_id:
            # increment attempt counter
            redis_client.zincrby(f"runner_{task.id}_attempt", 1, "inc")
            task.status_id = 2

            # if task ended with a non-catastrophic error, it is possible that we can rerun it.
            if (redis_client.zincrby(f"runner_{task.id}_attempt", 0, "inc") or 1) <= (
                task.max_retries or 0
            ):
                run_number = int(redis_client.zincrby(f"runner_{task.id}_attempt", 0, "inc") or 1)

                # schedule a rerun in 5 minutes.
                RunnerLog(
                    task,
                    run_id,
                    8,
                    f"Scheduling re-attempt {run_number} of {task.max_retries}.",
                )

                requests.get(
                    "%s/run/%s/delay/5" % (app.config["SCHEDULER_HOST"], task.id),
                    timeout=60,
                )

            else:
                redis_client.delete(f"runner_{task.id}_attempt")

                # if the project runs in series, mark all following enabled tasks as errored
                if task.project.sequence_tasks == 1:
                    task_id_list = [
                        x.id
                        for x in Task.query.filter_by(enabled=1)
                        .filter_by(project_id=task.project_id)
                        .order_by(Task.order.asc(), Task.name.asc())  # type: ignore[union-attr]
                        .all()
                    ]

                    if task.id in task_id_list:
                        for this_id in task_id_list[task_id_list.index(task.id) + 1 :]:
                            Task.query.filter_by(id=this_id).update({"status_id": 2})


@dataclass
class RunnerLog:
    """Save log messages."""

    task: Task
    run_id: Optional[str]
    source_id: int
    message: str
    error: Optional[int] = 0

    def __post_init__(self) -> None:
        """Save message."""
        log = TaskLog(
            task_id=self.task.id,
            job_id=self.run_id,
            error=self.error,
            status_id=self.source_id,
            message=f"{self.message}",
        )
        db.session.add(log)
        db.session.commit()
