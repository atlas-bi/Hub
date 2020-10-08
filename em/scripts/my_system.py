"""

    Functions used to monitory the host

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
import psutil
from em import app, db
from ..model.model import TaskLog


class Monitor:
    """ main class to check the system """

    # pylint: disable=too-few-public-methods
    def __init__(self, task):

        self.task = task
        self.process = psutil.Process()

    def check_all(self):
        """ return true if any tests fail, otherwise false. """
        return self.__disk() or self.__cpu() or self.__mem() or False

    def __disk(self):
        """ get disk free space. need some free % """
        my_disk = psutil.disk_usage("/")

        if my_disk.free < app.config["MIN_DISK_SPACE"]:
            logging.error(
                "System: System is below minimum disk space threshold. \
                Task cannot run: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                error=1,
                status_id=18,  # 18 = system
                message="System is below minimum disk space threshold. Task cannot run.",
            )
            db.session.add(log)
            db.session.commit()
            return True
        return False

    def __cpu(self):
        """ get cpu usage % """
        my_cpu = self.process.cpu_percent(interval=None)
        my_cpu = self.process.cpu_percent(interval=None)

        if my_cpu > 100 - app.config["MIN_FREE_CPU_PERC"]:
            logging.error(
                "System: System is over maximum cpu threshold. \
                Task cannot run: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                error=1,
                status_id=18,  # 18 = system
                message="System is over maximum cpu threshold. Task cannot run.",
            )
            db.session.add(log)
            db.session.commit()
            return True
        return False

    def __mem(self):
        """ get mem usage % """
        my_mem = psutil.virtual_memory()

        if my_mem.percent > 100 - app.config["MIN_FREE_MEM_PERC"]:
            logging.error(
                "System: System is over maximum memory threshold. \
                Task cannot run: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                error=1,
                status_id=18,  # 18 = system
                message="System is over maximum memory threshold. Task cannot run.",
            )
            db.session.add(log)
            db.session.commit()
            return True
        return False
