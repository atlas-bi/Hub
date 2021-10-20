"""Host system monitors."""


import logging

import psutil
from flask import current_app as app

from runner import db
from runner.model import Task, TaskLog


class Monitor:
    """Group of functions to monitor host OS."""

    # pylint: disable=too-few-public-methods
    def __init__(self, task: Task, job_hash: str) -> None:
        """Set up class varaibles.

        :param task: task object
        """
        self.task = task
        self.process = psutil.Process()
        self.job_hash = job_hash

    def check_all(self) -> bool:
        """Check disk, cpu and memory of host.

        :returns: true if all tests pass, else false.
        """
        return self.__disk() or self.__cpu() or self.__mem() or False

    def __disk(self) -> bool:
        """Check if free disk space is below threshold set in config.py.

        :returns: True if test passes, else False.
        """
        my_disk = psutil.disk_usage("/")

        if my_disk.free < app.config["MIN_DISK_SPACE"]:
            logging.error(
                "System: System is below minimum disk space threshold. \
                Task cannot run: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                error=1,
                status_id=18,  # 18 = system
                message="System is below minimum disk space threshold. Task cannot run.",
            )
            db.session.add(log)
            db.session.commit()
            return True
        return False

    def __cpu(self) -> bool:
        """Check if cpu is below threshold set in config.py.

        :returns: True if test passes, else False.
        """
        my_cpu = psutil.cpu_percent(interval=5)  # seconds to check cpu

        if my_cpu > 100 - app.config["MIN_FREE_CPU_PERC"]:
            logging.error(
                "System: System is over maximum cpu threshold. \
                Task cannot run: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                error=1,
                status_id=18,  # 18 = system
                message="System is over maximum cpu threshold. Task cannot run.",
            )
            db.session.add(log)
            db.session.commit()
            return True
        return False

    def __mem(self) -> bool:
        """Check if memory is below threshold set in config.py.

        :returns: True if test passes, else False.
        """
        my_mem = psutil.virtual_memory()

        if my_mem.percent > 100 - app.config["MIN_FREE_MEM_PERC"]:
            logging.error(
                "System: System is over maximum memory threshold. \
                Task cannot run: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                error=1,
                status_id=18,  # 18 = system
                message="System is over maximum memory threshold. Task cannot run.",
            )
            db.session.add(log)
            db.session.commit()
            return True
        return False
