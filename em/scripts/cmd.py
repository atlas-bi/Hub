"""

    Functions used to run system commands

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

import logging
import os
from em import app, db
from .error_print import full_stack
from ..model.model import (
    TaskLog,
    Task,
)


class Cmd:
    """ system command runner """
    # pylint: disable=too-few-public-methods
    def __init__(self, task, cmd, success_msg, error_msg):
        self.task = task
        self.cmd = cmd
        self.success_msg = success_msg
        self.error_msg = error_msg


    def run(self):
        """ function to run command and log output """
        try:
            out = os.popen(self.cmd + " 2>&1").read()
            if "Error" in out:
                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.task.last_run_job_id,
                    status_id=14,  # 14 = py processing
                    error=1,
                    message=self.error_msg + ("\n" if out != "" else "") + out,
                )
                db.session.add(log)
                db.session.commit()
            else:
                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.task.last_run_job_id,
                    status_id=14,  # 14 = py processing
                    message=self.success_msg,
                )
                db.session.add(log)
                db.session.commit()
            return out

        # pylint: disable=bare-except
        except:
            logging.error(
                "PyProcesser: Running Failed: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=14,  # 14 = py processing
                error=1,
                message=self.error_msg
                + ("\n" if out != "" else "")
                + "\n"
                + str(full_stack()),
            )

            db.session.add(log)
            db.session.commit()
            return ""