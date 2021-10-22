"""FTP connection manager."""


import ftplib  # noqa: S402
import logging
import sys
import time
from ftplib import FTP  # noqa: S402
from pathlib import Path
from typing import List, Optional, Union

from flask import current_app as app

from runner import db
from runner.model import ConnectionFtp, Task, TaskLog

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from crypto import em_decrypt
from error_print import full_stack


class Ftp:
    """FTP Connection Handler Class.

    Function takes a file name and source file path
    and will upload the file to the fpt location
    specified in the task settings.
    """

    # pylint: disable=too-few-public-methods
    def __init__(
        self,
        task: Task,
        connection: ConnectionFtp,
        overwrite: int,
        file_name: str,
        file_path: Optional[str],
        job_hash: str,
    ) -> None:
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
        self.conn = FTP(self.connection.address or "")  # noqa: S321

    def __connect(self) -> None:

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
                message="Failed to connect to <a href='/connection/"
                + str(self.connection.connection.id)
                + "'>"
                + str(self.connection.name)
                + "("
                + str(self.connection.username)
                + ("@" if self.connection.username else "")
                + str(self.connection.address)
                + ")</a>\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

    def read(self) -> str:
        """Read a file from FTP server.

        Data is loaded into a temp file.

        Returns a path or raises an exception.
        """
        self.__connect()

        try:
            logging.info(
                "FTP: Reading File: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )
            self.conn.cwd(self.connection.path or "")
            my_binary: List[bytes] = []

            def handle_binary(more_data: bytes) -> None:
                my_binary.append(more_data)

            self.conn.retrbinary("RETR " + self.file_name, callback=handle_binary)
            data = "".join([str(x) for x in my_binary])

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
                + str(self.connection.path)
                + self.file_name
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

            raise e

        self.__close()
        return data

    def save(self) -> Union[bool, str]:
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
            self.conn.cwd(self.connection.path or "")

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
                + str(self.connection.path)
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
                    + str(self.connection.path)
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
            with open(str(self.file_path), "rb") as file:
                self.conn.storbinary("STOR " + self.file_name, file)

            # file is now confirmed on server w/ confirm=True flag
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=13,  # ftp
                message="File loaded to server: "
                + str(self.connection.path)
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
                + str(self.connection.path)
                + self.file_name
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

        self.__close()
        return True

    def __close(self) -> None:
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
                + str(self.connection.name)
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
