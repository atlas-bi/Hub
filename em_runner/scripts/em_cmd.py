"""Functions used to run system commands."""
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


import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from em_runner import db
from em_runner.model import TaskLog

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from error_print import full_stack


class Cmd:
    """System command runner."""

    # pylint: disable=too-few-public-methods
    def __init__(self, task, cmd, success_msg, error_msg, job_hash):
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

    def shell(self):
        """Run input command as a shell command.

        :returns: Shell output of command.
        """
        out = ""
        # pylint: disable=broad-except
        try:
            out = subprocess.check_output(
                self.cmd, stderr=subprocess.STDOUT, shell=True
            )
            out = out.decode("utf-8")

            if "Error" in out:
                log = TaskLog(
                    task_id=(self.task.id if self.task is not None else None),
                    job_id=(self.job_hash),
                    status_id=(17 if self.task else 7),  # 17 = cmd runner, 7 =  user
                    error=1,
                    message=self.error_msg
                    + ("\n" if out != "" else None)
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

    def run(self):
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
                    message=self.error_msg + ("\n" if out != "" else None) + out,
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
