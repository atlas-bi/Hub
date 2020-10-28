"""

    Functions used to run ssh commands

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
import paramiko
from em import app, db
from ..model.model import Task, TaskLog
from .crypto import em_decrypt
from .error_print import full_stack


class Ssh:
    """
    Used to run SSH commands on remote server

    """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-few-public-methods

    def __init__(self, task, connection, command):

        self.connection = connection
        self.task = task
        self.session = None
        self.stdout_data = []
        self.stderr_data = []
        self.command = command

    def __connect(self):
        try:
            logging.info(
                "SSH: Connecting: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )

            # there is no timeout in paramiko so...
            # continue to attemp to login during time limit
            # if we are getting timeout exceptions

            self.session = paramiko.SSHClient()
            self.session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.session.connect(
                hostname=self.connection.address,
                port=(self.connection.port or 22),
                username=self.connection.username,
                password=em_decrypt(self.connection.password),
                timeout=5000,
            )

            # timeout = time.time() + 60 * 3  #  2 mins from now
            # while True:
            #     try:
            #         self.transport = paramiko.Transport(
            #             self.connection.address
            #             + ":"
            #             + str((self.connection.port or 22))
            #         )
            #         self.transport.connect(
            #             username=self.connection.username,
            #             password=em_decrypt(self.connection.password),
            #         )

            #         self.session = self.transport.open_channel(kind="session")
            #         break
            #     except paramiko.ssh_exception.AuthenticationException as e:
            #         # pylint: disable=no-else-continue
            #         if str(e) == "Authentication timeout." and time.time() <= timeout:
            #             time.sleep(10)  # wait 10 sec before retrying
            #             continue
            #         elif time.time() > timeout:
            #             # pylint: disable=raise-missing-from
            #             raise ValueError("SFTP Connection timeout.")

            #         else:
            #             raise e
        # pylint: disable=bare-except
        except:
            logging.error(
                "SSH: Failed to Connect: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=19,  # 19 SSH
                error=1,
                message="Failed to connect to <a class='em-link' href='/connection/"
                + str(self.connection.connection.id)
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

    def __close(self):
        try:
            logging.info(
                "SSH: Closing: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )
            self.session.close()
            # self.transport.close()

        # pylint: disable=bare-except
        except:
            logging.error(
                "SSH: Failed to Close: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=19,  # ssh
                error=1,
                message="Failed to close connection: "
                + self.connection.name
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

    def run(self):
        """ will connect, run command, and attempt to gather output """
        self.__connect()

        try:
            stdin, stdout, stderr = self.session.exec_command(
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

            # if self.stderr_data:
            #     print("error", str(self.stderr_data, "utf8"))

            # if self.stdout_data:
            #     print("success", str(self.stdout_data, "utf8"))

            if stdout.channel.recv_exit_status() != 0:

                logging.error(
                    "SSH: Error output: Task: %s, with run: %s\n%s\n%s",
                    str(self.task.id),
                    str(self.task.last_run_job_id),
                    str(self.stdout_data, "utf8"),
                    str(self.stderr_data, "utf8"),
                )
                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.task.last_run_job_id,
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
                    str(self.task.last_run_job_id),
                    str(self.stdout_data, "utf8"),
                    str(self.stderr_data, "utf8"),
                )
                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.task.last_run_job_id,
                    status_id=19,  # ssh
                    message="SSH Output:\n"
                    + str(self.stdout_data, "utf8")
                    + "\n"
                    + str(self.stderr_data, "utf8"),
                )
                db.session.add(log)
                db.session.commit()

        # pylint: disable=bare-except
        except:
            logging.error(
                "SSH: Error output: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
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
