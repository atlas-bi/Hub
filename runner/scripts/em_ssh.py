"""SSH connection handler."""
import logging
import sys
from pathlib import Path

import paramiko
from flask import current_app as app

from runner import db
from runner.model import ConnectionSsh, Task, TaskLog

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")

from crypto import em_decrypt
from error_print import full_stack


class Ssh:
    """SSH Connection Handler Class."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-few-public-methods

    def __init__(
        self, task: Task, connection: ConnectionSsh, command: str, job_hash: str
    ):
        """Set up class parameters.

        :param task: task object
        :param connection: connection object
        :param str command: command to be run
        """
        self.connection = connection
        self.task = task
        self.session = paramiko.SSHClient()
        self.stdout_data: bytes = b""
        self.stderr_data: bytes = b""
        self.job_hash = job_hash
        self.command = command

    def __connect(self) -> None:
        try:
            logging.info(
                "SSH: Connecting: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )

            # there is no timeout in paramiko so...
            # continue to attemp to login during time limit
            # if we are getting timeout exceptions

            self.session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.session.connect(
                hostname=str(self.connection.address),
                port=(self.connection.port or 22),
                username=self.connection.username,
                password=em_decrypt(self.connection.password, app.config["PASS_KEY"]),
                timeout=5000,
            )

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "SSH: Failed to Connect: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=19,  # 19 SSH
                error=1,
                message="Failed to connect to <a href='/connection/"
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

    def __close(self) -> None:
        try:
            logging.info(
                "SSH: Closing: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )
            self.session.close()

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "SSH: Failed to Close: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=19,  # ssh
                error=1,
                message="Failed to close connection: "
                + str(self.connection.name)
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

    def run(self) -> str:
        """Run an SSH Command.

        First, this will make a connection then run the command

        :returns: Output from command.
        """
        self.__connect()

        try:
            # pylint: disable=W0612
            stdin, stdout, stderr = self.session.exec_command(  # noqa: S601
                self.command, timeout=5000
            )

            self.stderr_data = b""
            self.stdout_data = b""

            while not stdout.channel.exit_status_ready():
                self.stdout_data += stdout.channel.recv(1024)

            for line in iter(stdout.readline, ""):
                self.stdout_data += bytes(line, "utf8")

            for line in iter(stderr.readline, ""):
                self.stderr_data += bytes(line, "utf8")

            if stdout.channel.recv_exit_status() != 0:

                logging.error(
                    "SSH: Error output: Task: %s, with run: %s\n%s\n%s",
                    str(self.task.id),
                    str(self.job_hash),
                    str(self.stdout_data, "utf8"),
                    str(self.stderr_data, "utf8"),
                )
                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.job_hash,
                    status_id=19,  # ssh
                    error=1,
                    message="SSH Error:\n"
                    + str(self.stdout_data, "utf8")
                    + "\n"
                    + str(self.stderr_data, "utf8"),
                )
                db.session.add(log)
                db.session.commit()

            if self.stdout_data != "":

                logging.info(
                    "SSH: Output: Task: %s, with run: %s\n%s\n%s",
                    str(self.task.id),
                    str(self.job_hash),
                    str(self.stdout_data, "utf8"),
                    str(self.stderr_data, "utf8"),
                )
                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.job_hash,
                    status_id=19,  # ssh
                    message="SSH Output:\n"
                    + str(self.stdout_data, "utf8")
                    + "\n"
                    + str(self.stderr_data, "utf8"),
                )
                db.session.add(log)
                db.session.commit()

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "SSH: Error output: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=19,  # ssh
                error=1,
                message="SSH Error:\n"
                + (str(self.stderr_data, "utf8") + "\n" if self.stderr_data else "")
                + (str(self.stdout_data, "utf8") + "\n" if self.stdout_data else "")
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

        self.__close()
        return "output"
