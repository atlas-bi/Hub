"""SMB Connection Manager."""

import logging
import pickle
import re
import sys
import tempfile
import time
import urllib
from io import TextIOWrapper
from pathlib import Path
from typing import Generator, List, Optional

from flask import current_app as app
from smb.base import SMBTimeout
from smb.SMBConnection import SMBConnection

from runner import db, redis_client
from runner.model import ConnectionSmb, Task, TaskLog
from runner.scripts.smb_fix import SMBHandler

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from crypto import em_decrypt
from error_print import full_stack


class Smb:
    """SMB Connection Handler Class.

    smb.read = returns contents of a network file
    smb.save = save contents of local file to network file
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        task: Task,
        connection: Optional[ConnectionSmb],
        overwrite: int,
        file_name: Optional[str],
        file_path: str,
        job_hash: str,
    ):
        """Set up class parameters."""
        # pylint: disable=too-many-arguments
        self.task = task
        self.connection = connection
        self.overwrite = overwrite
        self.file_name = file_name or ""
        self.job_hash = job_hash
        self.file_path = "/" + file_path.strip("/").strip("\\")

        if self.connection is not None:
            self.share_name = str(self.connection.share_name).strip("/").strip("\\")
            self.username = self.connection.username
            self.password = self.connection.password
            self.server_ip = self.connection.server_ip
            self.server_name = (
                self.connection.server_name if self.connection else "Error"
            )
            self.dest_path = str(self.connection.path) + "/" + str(self.file_name)

        else:
            # default connection for backups
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

        try:
            self.conn = self.__connect()
        except:
            self.conn = None

    def __connect(self) -> SMBConnection:
        """Connect to SMB server.

        After making a connection we save it to redis. Next time we need a connection
        we can grab if from redis and attempt to use. If it is no longer connected
        then reconnect.

        Because we want to use existing connection we will not close them...
        """

        def connect() -> SMBConnection:

            conn = SMBConnection(
                self.username,
                em_decrypt(self.password, app.config["PASS_KEY"]),
                "EM2.0 Webapp",
                self.server_name,
                use_ntlm_v2=True,
            )

            redis_client.set(
                "smb_connection_" + str(self.server_name), pickle.dumps(conn)
            )

            return conn

        try:
            smb_connection = redis_client.get("smb_connection_" + str(self.server_name))
            conn = pickle.loads(smb_connection) if smb_connection else None

            # there is no timeout in paramiko so...
            # continue to attemp to login during time limit
            # if we are getting timeout exceptions

            conn = connect()

            # make connection is not already connected.
            timeout = time.time() + 60 * 3  # 3 mins from now

            while True:

                try:
                    connected = conn.connect(self.server_ip, 139)

                    if not connected:
                        raise AssertionError()
                    break

                except (AssertionError, ConnectionResetError, SMBTimeout) as e:

                    # pylint: disable=no-else-continue
                    if time.time() <= timeout:
                        time.sleep(30)  # wait 30 sec before retrying
                        # recreate login
                        conn = connect()
                        continue
                    elif time.time() > timeout:
                        # pylint: disable=raise-missing-from
                        raise ValueError("SMB Connection failed after timeout.")
                    else:
                        raise e

        # pylint: disable=broad-except
        except BaseException as e:
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
                message=f"Failed to connect to {self.username}@{self.server_name}({self.server_ip})/{self.share_name}\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
            raise e

        return conn

    def list_dir(self) -> List:
        """Get list of directory contents."""
        # pylint: disable=broad-except
        if self.conn is None:
            return []
        try:
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
                message=f"Failed to get directory listing on {self.share_name} {self.file_path}\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
            return []

    def read(self) -> str:
        """Return file contents of network file path."""
        if self.conn is None:
            return ""
        try:
            # if there is a wildcard in the filename
            if "*" in self.file_path:
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

                # find matching file name
                for smb_file in my_list:
                    if (
                        smb_file.isDirectory is False
                        and len(re.findall(re_name, smb_file.filename)) > 0
                    ):
                        self.file_path = parent_folder + "/" + smb_file.filename
                        break
                else:
                    # failed to find matching file
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
                    self.file_path = ""

            # if a file was found, try to open.
            if self.file_path:

                director = urllib.request.build_opener(SMBHandler)

                open_file_for_read = director.open(
                    "smb://"
                    + str(self.username)
                    + ":"
                    + em_decrypt(self.password, app.config["PASS_KEY"])
                    + "@"
                    + str(self.server_name)
                    + ","
                    + str(self.server_ip)
                    + "/"
                    + str(self.share_name)
                    + "/"
                    + str(self.file_path)
                )

                def load_data(file_obj: TextIOWrapper) -> Generator:
                    with file_obj as this_file:
                        while True:
                            data = this_file.read(1024)
                            if not data:
                                break
                            yield data

                # send back contents
                with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp:
                    for data in load_data(open_file_for_read):
                        temp.write(data)

                open_file_for_read.close()

                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.job_hash,
                    status_id=10,  # 10 = SMB
                    message="File successfully loaded from server "
                    + re.sub(r":.+?(?=@)", "", self.file_path),
                )
                db.session.add(log)
                db.session.commit()

                return temp.name

            # else return an empty file
            # pylint: disable=R1732
            temp = tempfile.NamedTemporaryFile(mode="wb", delete=False)
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

    def save(self) -> str:
        """Load data into network file path, creating location if not existing."""
        if self.conn is None:
            return ""
        try:
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
                            + f"smb://{self.username}@{self.server_name} {self.server_ip})/{self.share_name}/{self.dest_path}",
                        )
                        db.session.add(log)
                        db.session.commit()

                        return "File already exists"
                    # pylint: disable=broad-except
                    except BaseException:
                        pass

                with open(self.file_path, "rb", buffering=0) as file_obj:
                    self.conn.storeFile(self.share_name, self.dest_path, file_obj)

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=10,  # 10 = SMB
                message=f"File saved: {self.file_path} to {self.username}@{self.server_name} {self.server_ip})/{self.share_name}/{self.dest_path}",
            )
            db.session.add(log)
            db.session.commit()

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
                message=f"Failed to load file {self.file_path} to {self.username}@{self.server_name} {self.server_ip})/{self.share_name}/{self.dest_path}\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

        return self.dest_path
