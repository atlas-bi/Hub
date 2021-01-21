"""FTP connection manager."""
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


import ftplib  # noqa: S402
import logging
import sys
import time
from ftplib import FTP  # noqa: S402
from pathlib import Path

from crypto import em_decrypt
from em_runner import db
from em_runner.model import TaskLog
from error_print import full_stack
from flask import current_app as app

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")


class Ftp:
    """FTP Connection Handler Class.

    Function takes a file name and source file path
    and will upload the file to the fpt location
    specified in the task settings.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, task, connection, overwrite, file_name, file_path, job_hash):
        """Set up class parameters.

        :param task: task object
        :param connection: connection object
        :param int overwrite: value determines if existing files should be overwriten
        :param str file_name: name of file in motion
        :param str file_path: local file path
        """
        # pylint: disable=too-many-arguments
        self.task = task
        self.connection = connection
        self.overwrite = overwrite
        self.file_name = file_name
        self.file_path = file_path
        self.job_hash = job_hash
        self.transport = ""
        self.conn = ""

    def __connect(self):

        try:
            logging.info(
                "FTP: Connecting: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )

            # there is no timeout in paramiko so...
            # continue to attemp to login during time limit
            # if we are getting timeout exceptions
            timeout = time.time() + 60 * 3  # 2 mins from now
            while True:
                try:
                    self.conn = FTP(self.connection.address)  # noqa: S321
                    self.conn.login(
                        user=(self.connection.username or ""),
                        passwd=(
                            em_decrypt(self.connection.password, app.config["PASS_KEY"])
                            or ""
                        ),
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

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "FTP: Failed to Connect: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=13,  # ftp
                error=1,
                message="Failed to connect to <a class='em-link' href='/connection/"
                + str(self.connection.connection.id)
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
        """Read a file from FTP server.

        :returns: file contents as string.
        """
        self.__connect()

        try:
            logging.info(
                "FTP: Reading File: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )
            self.conn.cwd(self.connection.path)
            my_binary = []

            def handle_binary(more_data):
                my_binary.append(more_data)

            self.conn.retrbinary("RETR " + self.file_name, callback=handle_binary)
            data = "".join(my_binary)

        # pylint: disable=broad-except
        except BaseException as e:
            data = ""
            logging.error(
                "FTP: Failed to Read File: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
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

            raise e

        self.__close()
        return data

    def save(self):
        """Use to copy local file to FTP server.

        :returns: true if successful.
        """
        self.__connect()
        try:
            logging.info(
                "FTP: Changing Dir: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )
            self.conn.cwd(self.connection.path)

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "FTP: Failed to change Dir: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
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
                    job_id=self.job_hash,
                    status_id=13,  # ftp
                    error=1,
                    message="File already exists and will not be loaded: "
                    + self.connection.path
                    + self.file_name,
                )
                db.session.add(log)
                db.session.commit()
                return "File already exists."

            # pylint: disable=broad-except
            except BaseException:
                pass

        try:
            logging.info(
                "FTP: Saving: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )
            with open(self.file_path, "rb") as file:
                self.conn.storbinary("STOR " + self.file_name, file)

            # file is now confirmed on server w/ confirm=True flag
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=13,  # ftp
                message="File loaded to server: "
                + self.connection.path
                + "/"
                + self.file_name,
            )
            db.session.add(log)
            db.session.commit()

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "FTP: Failed to Save: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
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
                str(self.job_hash),
            )
            self.conn.close()
        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "FTP: Failed to Close: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=13,  # ftp
                error=1,
                message="File failed to close connection: "
                + self.connection.name
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
