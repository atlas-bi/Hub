"""
    fpt connection manager

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
import time
from ftplib import FTP
from em import app, db
from .error_print import full_stack
from ..model.model import Task, TaskLog
from .crypto import em_decrypt


class Ftp:
    """
    function takes a file name and source file path
    and will upload the file to the fpt location
    specified in the task settings.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, task, connection, overwrite, file_name, file_path):
        # pylint: disable=too-many-arguments
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
                "FTP: Connecting: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )

            # there is no timeout in paramiko so...
            # continue to attemp to login during time limit
            # if we are getting timeout exceptions
            timeout = time.time() + 60 * 3  #  2 mins from now
            while True:
                try:
                    self.conn = FTP(self.connection.address)
                    self.conn.login(
                        user=(self.connection.username or ""),
                        passwd=(em_decrypt(self.connection.password) or ""),
                    )
                    break
                except ftplib.error_reply as e:
                    # pylint: disable=no-else-continue
                    if time.time() <= timeout:
                        time.sleep(10)  # wait 10 sec before retrying
                        continue
                    elif time.time() > timeout:
                        # pylint: disable=raise-missing-from
                        raise ValueError("SFTP Connection timeout.")

                    else:
                        raise e

        # pylint: disable=bare-except
        except:
            logging.error(
                "FTP: Failed to Connect: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=13,  # ftp
                error=1,
                message="Failed to connect to <a class='em-link' href='/connection/"
                + str(self.connection.id)
                + "'>"
                + self.connection.name
                + "("
                + self.connection.username
                + ("@" if self.connection.username else "")
                + self.connection.address
                + ")</a>\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

    def read(self):
        """ used to copy a file from ftp to local server """

        self.__connect()

        try:
            logging.info(
                "FTP: Reading File: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )
            self.conn.cwd(self.connection.path)
            my_binary = []

            def handle_binary(more_data):
                my_binary.append(more_data)

            self.conn.retrbinary("RETR " + self.file_name, callback=handle_binary)
            data = "".join(my_binary)

        # pylint: disable=bare-except
        except:
            data = ""
            logging.error(
                "FTP: Failed to Read File: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=13,  # fpt
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
                "FTP: Changing Dir: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )
            self.conn.cwd(self.connection.path)
        # pylint: disable=bare-except
        except:
            logging.error(
                "FTP: Failed to change Dir: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=13,  # ftp
                error=1,
                message="File failed to change path to : "
                + self.connection.path
                + self.file_name
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

        if self.overwrite != 1:
            try:
                self.conn.size(self.file_name)
                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.task.last_run_job_id,
                    status_id=13,  # ftp
                    error=1,
                    message="File already exists and will not be loaded: "
                    + self.connection.path
                    + self.file_name,
                )
                db.session.add(log)
                db.session.commit()
                return "File already exists."

            # pylint: disable=bare-except
            except:
                pass

        try:
            logging.info(
                "FTP: Saving: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )
            with open(self.file_path, "rb") as file:
                self.conn.storbinary("STOR " + self.file_name, file)

            # file is now confirmed on server w/ confirm=True flag
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=13,  # ftp
                message="File loaded to server: "
                + self.connection.path
                + "/"
                + self.file_name,
            )
            db.session.add(log)
            db.session.commit()

        # pylint: disable=bare-except
        except:
            logging.error(
                "FTP: Failed to Save: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=13,  # ftp
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
                "FTP: Closing: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )
            self.conn.close()
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
                status_id=13,  # ftp
                error=1,
                message="File failed to close connection: "
                + self.connection.name
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
