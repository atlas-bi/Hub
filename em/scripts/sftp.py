"""
    sfpt connection manager

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
import paramiko
from em import app, db
from ..model.model import Task, TaskLog
from .crypto import em_decrypt
from .error_print import full_stack


class Sftp:
    """
        function takes a file name and source file path
        and will upload the file to the sfpt location
        specified in the task settings.
    """

    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-arguments
    def __init__(self, task, connection, overwrite, file_name, file_path):

        self.task = task
        self.connection = connection
        self.overwrite = overwrite
        self.file_name = file_name
        self.file_path = file_path
        self.transport = ""
        self.conn = ""

    def __connect(self):

        try:
            logging.info(
                "SFTP: Connecting: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )
            self.transport = paramiko.Transport(
                self.connection.address + ":" + str((self.connection.port or 22))
            )
            self.transport.connect(
                username=self.connection.username,
                password=em_decrypt(self.connection.password),
            )
            self.conn = paramiko.SFTPClient.from_transport(self.transport)

        # pylint: disable=bare-except
        except:
            logging.error(
                "SFTP: Failed to Connect: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=9,
                error=1,
                message="Failed to connect to <a class='em-link' href='/connection/"
                + str(self.connection.id)
                + "'>"
                + self.connection.name
                + "("
                + self.connection.username
                + "@"
                + self.connection.address
                + ":"
                + str((self.connection.port or 22))
                + "</a>\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

    def read(self):
        """ used to copy a file from sftp to local server """

        self.__connect()

        try:
            logging.info(
                "SFTP: Reading: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )
            self.conn.chdir(self.connection.path)
            data = self.conn.open(self.file_name, mode="r").read().decode("utf-8")

        # pylint: disable=bare-except
        except:
            logging.error(
                "SFTP: Failed to Read File: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            data = ""
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=9,
                error=1,
                message="File failed to load file from server: "
                + self.connection.path
                + self.file_name
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

        self.__close()
        return data

    def save(self):
        """ use to copy local file to sftp server """
        self.__connect()
        try:
            logging.info(
                "SFTP: Changing Dir: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )
            self.conn.chdir(self.connection.path)

        # pylint: disable=bare-except
        except:
            logging.error(
                "SFTP: Failed to change Dir: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=9,
                error=1,
                message="File failed to change path to: "
                + self.connection.path
                + self.file_name
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

        if self.overwrite != 1:
            try:
                self.conn.stat(self.file_name)
                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.task.last_run_job_id,
                    status_id=9,
                    error=1,
                    message="File already exists and will not be loaded: "
                    + self.connection.path
                    + self.file_name,
                )
                db.session.add(log)
                db.session.commit()
                self.__close()
                return "File already exists."

            # pylint: disable=bare-except
            except:
                pass

        try:
            logging.info(
                "SFTP: Saving: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )
            self.conn.put(self.file_path, self.file_name, confirm=True)

            # file is now confirmed on server w/ confirm=True flag
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=9,
                message="File verified on server: "
                + self.connection.path
                + self.file_name,
            )
            db.session.add(log)
            db.session.commit()

        # pylint: disable=bare-except
        except:
            logging.error(
                "SFTP: Failed to Save: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=9,
                error=1,
                message="File failed to finish loading to server: "
                + self.connection.path
                + self.file_name
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

        self.__close()
        return True

    def __close(self):
        try:
            logging.info(
                "SFTP: Closing: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )
            self.conn.close()
            self.transport.close()

        # pylint: disable=bare-except
        except:
            logging.error(
                "FTP: Failed to Close: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=9,
                error=1,
                message="File failed to close connection: "
                + self.connection.name
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
