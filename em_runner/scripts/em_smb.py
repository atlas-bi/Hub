"""SMB Connection Manager."""
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


import logging
import pickle
import re
import sys
import tempfile
import time
import urllib
from pathlib import Path

from crypto import em_decrypt
from error_print import full_stack
from flask import current_app as app
from smb.base import SMBTimeout
from smb.SMBConnection import SMBConnection

from em_runner import db, redis_client
from em_runner.model import TaskLog
from em_runner.scripts.smb_fix import SMBHandler

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")


class Smb:
    """SMB Connection Handler Class.

    smb.read = returns contents of a network file
    smb.save = save contents of local file to network file
    """

    # pylint: disable=too-many-instance-attributes

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
        self.job_hash = job_hash
        self.file_path = "/" + file_path.strip("/").strip("\\")
        self.conn = ""

        if connection == "default":
            self.share_name = app.config["SMB_DEFAULT_SHARE"].strip("/").strip("\\")
            self.username = app.config["SMB_USERNAME"]
            self.password = app.config["SMB_PASSWORD"]
            self.server_ip = app.config["SMB_SERVER_IP"]
            self.server_name = app.config["SMB_SERVER_NAME"]
            self.dest_path = (
                self.task.project.name
                + "/"
                + self.task.name
                + "/"
                + (self.job_hash + "/" if self.job_hash else "")
                + self.file_name
            )
        else:
            self.share_name = (
                self.connection.share_name.strip("/").strip("\\")
                if self.connection
                else "Error"
            )
            self.username = self.connection.username if self.connection else "Error"
            self.password = self.connection.password if self.connection else "Error"
            self.server_ip = self.connection.server_ip if self.connection else "Error"
            self.server_name = (
                self.connection.server_name if self.connection else "Error"
            )
            self.dest_path = (
                (self.connection.path + "/" + self.file_name)
                if self.connection
                else "Error"
            )

    def __connect(self):
        """Connect to SMB server.

        After making a connection we save it to redis. Next time we need a connection
        we can grab if from redis and attempt to use. If it is no longer connected
        then reconnect.

        Because we want to use existing connection we will not close them...
        """

        def connect():
            if self.conn is None:
                self.conn = SMBConnection(
                    self.username,
                    em_decrypt(self.password, app.config["PASS_KEY"]),
                    "EM2.0 Webapp",
                    self.server_name,
                    use_ntlm_v2=True,
                )

                redis_client.set(
                    "smb_connection_" + self.server_name, pickle.dumps(self.conn)
                )

        try:
            logging.info(
                "SMB: Connecting: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )

            smb_connection = redis_client.get("smb_connection_" + self.server_name)

            self.conn = pickle.loads(smb_connection) if smb_connection else None

            # there is no timeout in paramiko so...
            # continue to attemp to login during time limit
            # if we are getting timeout exceptions
            connect()

            # make connection is not already connected.
            timeout = time.time() + 60 * 3  # 3 mins from now
            while True:
                try:
                    connected = self.conn.connect(self.server_ip, 139)
                    if not connected:
                        raise AssertionError()
                    break

                except (AssertionError, ConnectionResetError, SMBTimeout) as e:
                    # pylint: disable=no-else-continue
                    if time.time() <= timeout:
                        time.sleep(30)  # wait 30 sec before retrying
                        # recreate login
                        connect()
                        continue
                    elif time.time() > timeout:
                        # pylint: disable=raise-missing-from
                        raise ValueError("SMB Connection failed after timeout.")
                    else:
                        raise e

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "SMB: Failed to Connect: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                error=1,
                status_id=10,  # 10 = SMB Error
                message="Failed to connect to "
                + self.username
                + "@"
                + self.server_name
                + " ("
                + self.server_ip
                + ") /"
                + self.share_name
                + "/ \n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

    def list_dir(self):
        """Get list of directory contents.

        :returns: list of all directory contents.
        """
        # pylint: disable=broad-except
        try:
            self.__connect()
        except BaseException as e:
            raise e
        try:
            logging.info(
                "SMB: Listing Dir: %s, path: %s",
                str(self.share_name),
                str(self.file_path),
            )

            try:
                # verify that it is actually existing. if not exising
                # return empty list.
                self.conn.getAttributes(self.share_name, self.file_path)

            # pylint: disable=broad-except
            except BaseException:
                return []

            my_list = self.conn.listPath(
                self.share_name, self.file_path, search=65591, timeout=30, pattern="*"
            )
            return my_list

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "SMB: Failed to list Dir: %s, path: %s\n%s",
                str(self.share_name),
                str(self.file_path),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                error=1,
                status_id=10,  # 10 = SMB Error
                message="Failed to get Dir listing to "
                + self.share_name
                + " "
                + self.file_path
                + " \n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
            return []

    def read(self):
        """Return file contents of network file path.

        :returns: Contents of file specified.
        """
        try:
            logging.info(
                "SMB: Reading: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )

            # if there is a wildcard in the filename
            if "*" in self.file_path:
                self.__connect()

                parent_folder = (
                    str(Path(self.file_path).parent)
                    if "/" in self.file_path or "\\" in self.file_path
                    else ""
                )
                my_file = (
                    str(Path(self.file_path).name)
                    if "/" in self.file_path or "\\" in self.file_path
                    else self.file_path
                )

                my_list = self.conn.listPath(
                    self.share_name,
                    parent_folder,
                    search=65591,
                    timeout=30,
                    pattern="*",
                )

                # convert search to regex and check for matching names.
                re_name = my_file.replace(".", r"\.").replace("*", ".+?")

                for my_file in my_list:
                    if (
                        my_file.isDirectory is False
                        and len(re.findall(re_name, my_file.filename)) > 0
                    ):
                        self.file_path = parent_folder + "/" + my_file.filename
                        break
                else:
                    # failed to find matching file
                    logging.error(
                        "SMB: Reading: Task: %s, with run: %s, \
                        failed to find matching file on server with pattern %s.",
                        str(self.task.id),
                        str(self.job_hash),
                        (parent_folder + "/" + re_name),
                    )
                    log = TaskLog(
                        task_id=self.task.id,
                        job_id=self.job_hash,
                        error=1,
                        status_id=10,  # 10 = SMB
                        message="Failed to find matching file on server with pattern %s"
                        % parent_folder
                        + "/"
                        + re_name,
                    )
                    db.session.add(log)
                    db.session.commit()
                    return None

            director = urllib.request.build_opener(SMBHandler)

            file_path = director.open(
                u"smb://"
                + self.username
                + ":"
                + em_decrypt(self.password, app.config["PASS_KEY"])
                + "@"
                + self.server_name
                + ","
                + self.server_ip
                + "/"
                + self.share_name
                + "/"
                + self.file_path
            )

            def load_data(file_obj):
                with file_obj as this_file:
                    while True:
                        data = this_file.read(1024)
                        if not data:
                            break
                        yield data

            # send back contents
            with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp:
                for data in load_data(file_path):
                    temp.write(data)

            file_path.close()

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=10,  # 10 = SMB
                message="File succefully loaded from server "
                + re.sub(r":.+?(?=@)", "", self.file_path),
            )
            db.session.add(log)
            db.session.commit()

            return temp.name
        # pylint: disable=broad-except
        except BaseException as e:

            logging.error(
                "SMB: Failed to Read File: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=10,  # 10 = SMB
                error=1,
                message="Failed to load file from server "
                + re.sub(r":.+?(?=@)", "", self.file_path)
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
            raise e

    def save(self):
        """Load data into network file path, creating location if not existing.

        :returns: True if successful.
        """
        try:
            logging.info(
                "SMB: Saving: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )
            self.__connect()

            # path must be created one folder at a time.. the docs say the path will all be
            # created if not existing, but it doesn't seem to be the case :)
            my_dir = self.dest_path.split("/")[:-1]

            path_builder = "/"
            for my_path in my_dir:
                path_builder += my_path + "/"

                try:
                    self.conn.listPath(self.share_name, path_builder)
                # pylint: disable=broad-except
                except BaseException:
                    self.conn.createDirectory(self.share_name, path_builder)

            # pylint: disable=useless-else-on-loop
            else:
                if self.overwrite != 1:
                    try:
                        # try to get security of the file. if it doesn't exist,
                        # we crash and then can create the file.
                        self.conn.getSecurity(self.share_name, self.dest_path)
                        log = TaskLog(
                            task_id=self.task.id,
                            job_id=self.job_hash,
                            status_id=10,
                            error=1,
                            message="File already exists and will not be loaded: "
                            + "smb://"
                            + self.username
                            + "@"
                            + self.share_name
                            + ","
                            + self.server_ip
                            + "/"
                            + self.share_name
                            + "/"
                            + self.dest_path,
                        )
                        db.session.add(log)
                        db.session.commit()
                        self.__close()
                        return "File already exists"
                    # pylint: disable=broad-except
                    except BaseException:
                        pass

                with open(self.file_path, "rb", buffering=0) as file_obj:
                    self.conn.storeFile(self.share_name, self.dest_path, file_obj)

            self.__close()

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=10,  # 10 = SMB
                message="File saved: "
                + self.file_path
                + " to "
                + self.username
                + "@"
                + self.server_name
                + " ("
                + self.server_ip
                + ") /"
                + self.share_name
                + "/"
                + self.dest_path,
            )
            db.session.add(log)
            db.session.commit()

            return self.dest_path

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "SMB: Failed to Save: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=10,  # 10 = SMB
                error=1,
                message="Failed to load file "
                + self.file_path
                + " to "
                + self.username
                + "@"
                + self.server_name
                + " ("
                + self.server_ip
                + ") /"
                + self.share_name
                + "/"
                + self.dest_path
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
                "SMB: Closing: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )
            self.conn.close()
        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "SMB: Failed to Close: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=10,  # 10 = SMB
                error=1,
                message="Failed to close connection" + "\n" + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
