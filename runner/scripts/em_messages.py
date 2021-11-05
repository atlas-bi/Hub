"""Exception and logging messages."""


import datetime
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from jinja2 import Environment, PackageLoader, select_autoescape

from runner.extensions import db
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

            Smtp(
                task=task,
                run_id=run_id,
                recipients=task.email_error_recipients,
                subject="Error in Project: %s / Task: %s / Run: %s %s"
                % (
                    task.project.name,
                    task.name,
                    run_id,
                    date,
                ),
                message=template.render(
                    task=task,
                    success=0,
                    date=date,
                    logs=logs,
                ),
                short_message=task.email_error_message
                or f"Atlas Hub task {task} failed.",
                attachments=[],
            )


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
