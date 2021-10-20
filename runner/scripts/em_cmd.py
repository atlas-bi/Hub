"""Functions used to run system commands."""


import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from runner import db
from runner.model import Task, TaskLog

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from error_print import full_stack


class Cmd:
    """System command runner."""

    # pylint: disable=too-few-public-methods
    def __init__(
        self, task: Task, cmd: str, success_msg: str, error_msg: str, job_hash: str
    ) -> None:
        """Set system path and variables.

        :param cmd: add system path to cmd.
        :param task: task object
        :param success_msg: message to print if command is successful
        :param error_msg: message to print if command errors
        """
        self.task = task
        self.cmd = (
            "PATH=$PATH:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            + " export PATH && "
            + cmd
        )
        self.success_msg = success_msg
        self.error_msg = error_msg
        self.job_hash = job_hash

    def shell(self) -> str:
        """Run input command as a shell command.

        :returns: Shell output of command.
        """
        # pylint: disable=broad-except
        try:
            out_bytes = subprocess.check_output(
                self.cmd, stderr=subprocess.STDOUT, shell=True
            )
            out = out_bytes.decode("utf-8")

            if "Error" in out:
                log = TaskLog(
                    task_id=(self.task.id if self.task is not None else None),
                    job_id=(self.job_hash),
                    status_id=(17 if self.task else 7),  # 17 = cmd runner, 7 =  user
                    error=1,
                    message=self.error_msg
                    + ("\n" if out != "" else "")
                    + re.sub(
                        r"(?<=:)([^:]+?)(?=@)",
                        "*****",
                        out,
                        flags=re.IGNORECASE | re.MULTILINE,
                    ),
                )
                db.session.add(log)
                db.session.commit()
            else:
                log = TaskLog(
                    task_id=(self.task.id if self.task is not None else None),
                    job_id=(self.job_hash),
                    status_id=(17 if self.task else 7),  # 17 = cmd runner, 7 =  user
                    message=self.success_msg + (("\n" + out) if out != "" else ""),
                )
                db.session.add(log)
                db.session.commit()
            return out

        # pylint: disable=bare-except
        except subprocess.CalledProcessError as e:
            out = e.output.decode("utf-8")
            logging.error(
                "Cmd: Running Failed: Task: %s, with run: %s\n%s",
                str(self.task.id if self.task is not None else None),
                str(self.job_hash),
                re.sub(
                    r"(?<=:)([^:]+?)(?=@)",
                    "*****",
                    str(out),
                    flags=re.IGNORECASE | re.MULTILINE,
                )
                + "\n"
                + str(e),
            )

            log = TaskLog(
                task_id=(self.task.id if self.task is not None else None),
                job_id=(self.job_hash),
                status_id=(17 if self.task else 7),  # 17 = cmd runner, 7 =  user
                error=1,
                message=self.error_msg
                + (("\n" + out) if out != "" else "")
                + "\n"
                + re.sub(
                    r"(?<=:)([^:]+?)(?=@)",
                    "*****",
                    str(e),
                    flags=re.IGNORECASE | re.MULTILINE,
                ),
            )

            db.session.add(log)
            db.session.commit()
            return "Failed"

        except BaseException:
            logging.error(
                "Cmd: Running Failed: Task: %s, with run: %s\n%s",
                str(self.task.id if self.task is not None else None),
                str(self.job_hash),
                str(full_stack()),
            )

            log = TaskLog(
                task_id=(self.task.id if self.task is not None else None),
                job_id=(self.job_hash),
                status_id=(17 if self.task else 7),  # 17 = cmd runner, 7 =  user
                error=1,
                message=re.sub(
                    r"(?<=:)([^:]+?)(?=@)",
                    "*****",
                    self.error_msg,
                    flags=re.IGNORECASE | re.MULTILINE,
                )
                + (("\n" + str(out)) if out != "" else "")
                + "\n"
                + str(full_stack()),
            )

            db.session.add(log)
            db.session.commit()
            return "Failed"

    def run(self) -> str:
        """Run input command as a subprocess command.

        :returns: Subprocess output of command.
        """
        try:
            out = os.popen(self.cmd + " 2>&1").read()

            if "Error" in out:
                log = TaskLog(
                    task_id=(self.task.id if self.task is not None else None),
                    job_id=(self.job_hash),
                    status_id=(17 if self.task else 7),  # 17 = cmd runner, 7 =  user
                    error=1,
                    message=self.error_msg + ("\n" if out != "" else "") + out,
                )
                db.session.add(log)
                db.session.commit()
            else:
                log = TaskLog(
                    task_id=(self.task.id if self.task is not None else None),
                    job_id=(self.job_hash),
                    status_id=(17 if self.task else 7),  # 17 = cmd runner, 7 =  user
                    message=self.success_msg,
                )
                db.session.add(log)
                db.session.commit()
            return out

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "Cmd: Running Failed: Task: %s, with run: %s\n%s",
                str(self.task.id if self.task is not None else None),
                str(self.job_hash),
                str(full_stack()),
            )

            log = TaskLog(
                task_id=(self.task.id if self.task is not None else None),
                job_id=(self.job_hash),
                status_id=(17 if self.task else 7),  # 17 = cmd runner, 7 =  user
                error=1,
                message=self.error_msg
                + ("\n" if out != "" else "")
                + "\n"
                + str(full_stack()),
            )

            db.session.add(log)
            db.session.commit()
            return ""
