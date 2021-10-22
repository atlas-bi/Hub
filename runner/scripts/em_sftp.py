"""SFTP connection manager."""


import logging
import sys
import tempfile
import time
from pathlib import Path
from typing import Generator, Optional, Tuple, Union

import paramiko
from flask import current_app as app
from paramiko import RSAKey, SFTPClient, SFTPFile, Transport

from runner import db
from runner.model import ConnectionSftp, Task, TaskLog

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from crypto import em_decrypt
from error_print import full_stack


class Sftp:
    """SFTP Connection Handler Class.

    Function takes a file name and source file path
    and will upload the file to the sfpt location
    specified in the task settings.
    """

    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        task: Task,
        connection: ConnectionSftp,
        overwrite: int,
        file_name: str,
        file_path: Optional[str],
        job_hash: str,
    ):
        """Set up class parameters.

        :param task: task object
        :param connection: connection object
        :param int overwrite: value determines if existing files should be overwriten
        :param str file_name: name of file in motion
        :param str file_path: local file path
        """
        self.task = task
        self.connection = connection
        self.overwrite = overwrite
        self.file_name = file_name
        self.file_path = file_path
        self.job_hash = job_hash
        self.key: Optional[RSAKey] = None
        self.transport, self.conn = self.__connect()

    def __connect(self) -> Tuple[Transport, SFTPClient]:

        try:
            logging.info(
                "SFTP: Connecting: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )

            # there is no timeout in paramiko so...
            # continue to attemp to login during time limit
            # if we are getting timeout exceptions
            timeout = time.time() + 60 * 3  # 2 mins from now
            while True:
                try:
                    transport = paramiko.Transport(
                        str(self.connection.address)
                        + ":"
                        + str((self.connection.port or 22))
                    )

                    # build ssh key file
                    if self.connection.key:
                        with tempfile.NamedTemporaryFile(
                            mode="w+", newline=""
                        ) as key_file:
                            key_file.write(
                                em_decrypt(self.connection.key, app.config["PASS_KEY"])
                            )
                            key_file.seek(0)

                            self.key = paramiko.RSAKey.from_private_key_file(
                                key_file.name,
                                password=em_decrypt(
                                    self.connection.password, app.config["PASS_KEY"]
                                ),
                            )

                    transport.connect(
                        username=str(self.connection.username),
                        password=(
                            em_decrypt(self.connection.password, app.config["PASS_KEY"])
                            if self.key is None
                            else ""
                        ),
                        pkey=self.key,
                    )

                    conn = paramiko.SFTPClient.from_transport(transport)
                    if conn is None:
                        raise ValueError("SFTP failed to create connection.")

                    break
                except (paramiko.ssh_exception.AuthenticationException, EOFError) as e:
                    # pylint: disable=no-else-continue
                    if str(e) == "Authentication timeout." and time.time() <= timeout:
                        time.sleep(10)  # wait 10 sec before retrying
                        continue
                    elif time.time() > timeout:
                        # pylint: disable=raise-missing-from
                        raise ValueError("SFTP Connection timeout.")

                    else:
                        raise e
            return (transport, conn)

        # pylint: disable=broad-except
        except BaseException as e:
            logging.error(
                "SFTP: Failed to Connect: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=9,
                error=1,
                message="Failed to connect to <a  href='/connection/"
                + str(self.connection.connection.id)
                + "'>"
                + str(self.connection.name)
                + "("
                + str(self.connection.username)
                + "@"
                + str(self.connection.address)
                + ":"
                + str((self.connection.port or 22))
                + "</a>\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

            raise e

    def read(self) -> str:
        """Read a file from FTP server.

        Data is loaded into a temp file.

        Returns a path or raises an exception.
        """
        try:
            logging.info(
                "SFTP: Reading: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )
            self.conn.chdir(self.connection.path or "")

            file_path = self.conn.open(self.file_name, mode="r")

            def load_data(file_obj: SFTPFile) -> Generator:
                with file_obj as this_file:
                    while True:
                        data = this_file.read(1024).decode("utf-8")  # type: ignore[attr-defined]
                        if not data:
                            break
                        yield data

            with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
                for data in load_data(file_path):
                    temp.write(data)

            file_path.close()

            name = temp.name

        # pylint: disable=broad-except
        except BaseException as e:
            logging.error(
                "SFTP: Failed to Read File: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            name = ""
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=9,
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
        return name

    def save(self) -> Optional[Union[str, bool]]:
        """Use to copy local file to FTP server.

        :returns: true if successful.
        """
        try:
            logging.info(
                "SFTP: Changing Dir: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )
            self.conn.chdir(self.connection.path)

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "SFTP: Failed to change Dir: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=9,
                error=1,
                message="File failed to change path to: "
                + str(self.connection.path)
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
                    job_id=self.job_hash,
                    status_id=9,
                    error=1,
                    message="File already exists and will not be loaded: "
                    + str(self.connection.path)
                    + self.file_name,
                )
                db.session.add(log)
                db.session.commit()
                self.__close()
                return "File already exists."

            # pylint: disable=broad-except
            except BaseException:
                pass

        try:
            logging.info(
                "SFTP: Saving: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )

            #  some sftp server do not allow overwrites. When attempted will
            #  return a permission error or other. So we log if the file exists
            #  to help with debugging.
            try:
                self.conn.stat(self.file_name)
                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.job_hash,
                    status_id=9,
                    message="File already exists will attempt to overwrite.",
                )
                db.session.add(log)
                db.session.commit()

            # pylint: disable=broad-except
            except BaseException:
                pass

            self.conn.put(str(self.file_path), self.file_name, confirm=True)

            # file is now confirmed on server w/ confirm=True flag
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=9,
                message="File verified on server: "
                + str(self.connection.path)
                + self.file_name,
            )
            db.session.add(log)
            db.session.commit()

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "SFTP: Failed to Save: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=9,
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
                "SFTP: Closing: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )
            self.conn.close()
            self.transport.close()

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
                status_id=9,
                error=1,
                message="File failed to close connection: "
                + str(self.connection.name)
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
