"""
    used to store a file on an smb server.

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

import re
import urllib
import logging
from pathlib import Path
from smb.SMBConnection import SMBConnection
from em import app, db
from ..model.model import TaskLog
from .smb_fix import SMBHandler
from .crypto import em_decrypt
from .error_print import full_stack


class Smb:
    """
    smb.read = returns contents of a network file
    smb.save = save contents of local file to network file
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, task, connection, overwrite, file_name, file_path):
        # pylint: disable=too-many-arguments
        self.task = task
        self.connection = connection
        self.overwrite = overwrite
        self.file_name = file_name
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
                + (self.task.last_run_job_id + "/" if self.task.last_run_job_id else "")
                + self.file_name
            )
        else:
            self.share_name = self.connection.share_name.strip("/").strip("\\")
            self.username = self.connection.username
            self.password = self.connection.password
            self.server_ip = self.connection.server_ip
            self.server_name = self.connection.server_name
            self.dest_path = self.connection.path + "/" + self.file_name

    def __connect(self):
        try:
            logging.info(
                "SMB: Connecting: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )
            self.conn = SMBConnection(
                self.username,
                em_decrypt(self.password),
                "EM2.0 Webapp",
                self.server_name,
                use_ntlm_v2=True,
            )
            assert self.conn.connect(self.server_ip, 139)

        # pylint: disable=bare-except
        except:
            logging.error(
                "SMB: Failed to Connect: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
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
        """ get directory listing """
        self.__connect()
        try:
            logging.info(
                "SMB: Listing Dir: %s, path: %s",
                str(self.share_name),
                str(self.file_path),
            )
            try:
                self.conn.getAttributes(self.share_name, self.file_path)

            except:
                # logging.error(
                #     "SMB: Dir does not exist: %s, path: %s\n%s",
                #     str(self.share_name),
                #     str(self.file_path),
                #     str(full_stack()),
                # )
                # log = TaskLog(
                #     task_id=self.task.id,
                #     status_id=10,  # 10 = SMB Error
                #     message="Cannot list directory - does not yet exist. "
                #     + self.share_name
                #     + " "
                #     + self.file_path,
                # )
                # db.session.add(log)
                # db.session.commit()
                return []

            my_list = self.conn.listPath(
                self.share_name, self.file_path, search=65591, timeout=30, pattern="*"
            )
            return my_list

        # pylint: disable=bare-except
        except:
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
        """ return contents of network file path """
        try:
            logging.info(
                "SMB: Reading: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
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

                for file in my_list:
                    if file.isDirectory is False:
                        if len(re.findall(re_name, file.filename)) > 0:
                            self.file_path = parent_folder + "/" + file.filename
                            break
                else:
                    # failed to find matching file
                    logging.error(
                        "SMB: Reading: Task: %s, with run: %s, \
                        failed to find matching file on server with pattern %s.",
                        str(self.task.id),
                        str(self.task.last_run_job_id),
                        (parent_folder + "/" + re_name),
                    )
                    log = TaskLog(
                        task_id=self.task.id,
                        job_id=self.task.last_run_job_id,
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
                + em_decrypt(self.password)
                + "@"
                + self.server_name
                + ","
                + self.server_ip
                + "/"
                + self.share_name
                + "/"
                + self.file_path
            )

            # send back contents
            x = file_path.read()

            file_path.close()

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=10,  # 10 = SMB
                message="File succefully loaded from server "
                + re.sub(r":.+?(?=@)", "", self.file_path),
            )
            db.session.add(log)
            db.session.commit()

            return x
        # pylint: disable=bare-except
        except:

            logging.error(
                "SMB: Failed to Read File: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=10,  # 10 = SMB
                error=1,
                message="Failed to load file from server "
                + re.sub(r":.+?(?=@)", "", self.file_path)
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
            return ""

    def save(self):
        """ load data into network file path, creating if not existing """
        try:
            logging.info(
                "SMB: Saving: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )
            self.__connect()
            # path must be created one folder at a time.. the docs say the path will all be
            # created if not existing, but it doesn't seem to be the case :)

            my_dir = self.dest_path.split("/")[:-1]

            path_builder = "/"
            for x in my_dir:
                path_builder += x + "/"

                try:
                    self.conn.listPath(self.share_name, path_builder)
                # pylint: disable=bare-except
                except:
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
                            job_id=self.task.last_run_job_id,
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
                    # pylint: disable=bare-except
                    except:
                        pass

                with open(self.file_path, "rb", buffering=0) as file_obj:
                    self.conn.storeFile(self.share_name, self.dest_path, file_obj)
                file_obj.close()

            self.__close()

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
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

            return True

        # pylint: disable=bare-except
        except:
            logging.error(
                "SMB: Failed to Save: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
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
                str(self.task.last_run_job_id),
            )
            self.conn.close()
        # pylint: disable=bare-except
        except:
            logging.error(
                "SMB: Failed to Close: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=10,  # 10 = SMB
                error=1,
                message="Failed to close connection" + "\n" + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
