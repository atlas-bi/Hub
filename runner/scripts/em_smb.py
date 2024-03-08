"""SMB Connection Manager."""

import csv
import fnmatch
import os
import pickle
import sys
import tempfile
import time
import urllib
from io import TextIOWrapper
from pathlib import Path
from typing import IO, Any, Dict, Generator, List, Optional, Tuple

from flask import current_app as app
from pathvalidate import sanitize_filename
from smb.base import NotConnectedError, SMBTimeout
from smb.smb_structs import OperationFailure
from smb.SMBConnection import SMBConnection

from runner import redis_client
from runner.model import ConnectionSmb, Task
from runner.scripts.em_file import file_size
from runner.scripts.em_messages import RunnerException, RunnerLog
from runner.scripts.smb_fix import SMBHandler

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from crypto import em_decrypt


def connection_json(connection: SMBConnection) -> Dict:
    """Convert the connection string to json."""
    return {
        "share_name": str(connection.share_name).strip("/").strip("\\"),
        "server_name": connection.server_name,
        "server_ip": connection.server_ip,
        "password": em_decrypt(connection.password, app.config["PASS_KEY"]),
        "username": str(connection.username),
    }


def connect(username: str, password: str, server_name: str, server_ip: str) -> SMBConnection:
    """Connect to SMB server.

    After making a connection we save it to redis. Next time we need a connection
    we can grab if from redis and attempt to use. If it is no longer connected
    then reconnect.

    Because we want to use existing connection we will not close them...
    """

    def build_connect() -> SMBConnection:
        conn = SMBConnection(
            username,
            em_decrypt(password, app.config["PASS_KEY"]),
            "EM2.0 Webapp",
            server_name,
            use_ntlm_v2=True,
        )

        redis_client.set("smb_connection_" + str(server_name), pickle.dumps(conn))

        return conn

    try:
        smb_connection = redis_client.get("smb_connection_" + str(server_name))
        conn = pickle.loads(smb_connection) if smb_connection else None

        # there is no timeout in paramiko so...
        # continue to attemp to login during time limit
        # if we are getting timeout exceptions

        conn = build_connect()

        # make connection is not already connected.
        timeout = time.time() + 60 * 3  # 3 mins from now

        while True:
            try:
                connected = conn.connect(server_ip, 139)

                if not connected:
                    raise AssertionError()
                break

            except (
                AssertionError,
                ConnectionResetError,
                SMBTimeout,
                NotConnectedError,
            ) as e:
                # pylint: disable=no-else-continue
                if time.time() <= timeout:
                    time.sleep(30)  # wait 30 sec before retrying
                    # recreate login
                    conn = build_connect()
                    continue
                elif time.time() > timeout:
                    # pylint: disable=raise-missing-from
                    raise ValueError("Connection timeout.")

                raise ValueError(f"Connection failed.\n{e}")

        return conn

    except BaseException as e:
        raise ValueError(f"Connection failed.\n{e}")


class Smb:
    """SMB Connection Handler Class.

    smb.read = returns contents of a network file
    smb.save = save contents of local file to network file
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        task: Task,
        run_id: Optional[str],
        connection: Optional[ConnectionSmb],
        directory: Path,
    ):
        """Set up class parameters."""
        # pylint: disable=too-many-arguments
        self.task = task
        self.run_id = run_id
        self.connection = connection
        self.dir = directory

        if self.connection is not None:
            self.share_name = str(self.connection.share_name).strip("/").strip("\\")
            self.username = self.connection.username
            self.password = self.connection.password
            self.server_ip = self.connection.server_ip
            self.server_name = self.connection.server_name if self.connection else "Error"
        else:
            # default connection for backups
            self.share_name = app.config["SMB_DEFAULT_SHARE"].strip("/").strip("\\")
            self.username = app.config["SMB_USERNAME"]
            self.password = app.config["SMB_PASSWORD"]
            self.server_ip = app.config["SMB_SERVER_IP"]
            self.server_name = app.config["SMB_SERVER_NAME"]
            self.subfolder = app.config.get("SMB_SUBFOLDER")

        self.conn = self.__connect()

    def __connect(self) -> SMBConnection:
        """Connect to SMB server.

        After making a connection we save it to redis. Next time we need a connection
        we can grab if from redis and attempt to use. If it is no longer connected
        then reconnect.

        Because we want to use existing connection we will not close them...
        """
        try:
            return connect(
                str(self.username),
                str(self.password),
                str(self.server_name),
                str(self.server_ip),
            )
        except ValueError as e:
            raise RunnerException(self.task, self.run_id, 10, str(e))

    def _walk(self, directory: str) -> Generator[Tuple[str, List[Any], List[str]], None, None]:
        dirs = []
        nondirs = []

        for entry in self.conn.listPath(
            self.share_name, directory, search=65591, timeout=30, pattern="*"
        ):
            if entry.isDirectory and entry.filename not in ["/", ".", ".."]:
                dirs.append(entry.filename)
            elif entry.isDirectory is False:
                nondirs.append(str(Path(directory).joinpath(entry.filename)))

        yield directory, dirs, nondirs

        # Recurse into sub-directories
        for dirname in dirs:
            new_path = str(Path(directory).joinpath(dirname))
            yield from self._walk(new_path)

    def __load_file(self, file_name: str, index: int, length: int) -> IO[str]:
        RunnerLog(self.task, self.run_id, 10, f"({index} of {length}) downloading {file_name}")

        director = urllib.request.build_opener(SMBHandler)

        password = em_decrypt(self.password, app.config["PASS_KEY"])

        open_file_for_read = director.open(
            f"smb://{self.username}:{password}@{self.server_name},{self.server_ip}/{self.share_name}/{file_name}"
        )

        def load_data(file_obj: TextIOWrapper) -> Generator:
            with file_obj as this_file:
                while True:
                    data = this_file.read(1024)
                    if not data:
                        break
                    yield data

        # send back contents

        with tempfile.NamedTemporaryFile(mode="wb+", delete=False, dir=self.dir) as data_file:
            for data in load_data(open_file_for_read):
                if self.task.source_smb_ignore_delimiter != 1 and self.task.source_smb_delimiter:
                    my_delimiter = self.task.source_smb_delimiter or ","

                    csv_reader = csv.reader(
                        data.splitlines(),
                        delimiter=my_delimiter,
                    )
                    writer = csv.writer(data_file)
                    writer.writerows(csv_reader)

                else:
                    data_file.write(data)

            original_name = str(self.dir.joinpath(file_name.split("/")[-1]))
            if os.path.islink(original_name):
                os.unlink(original_name)
            elif os.path.isfile(original_name):
                os.remove(original_name)
            os.link(data_file.name, original_name)
            data_file.name = original_name  # type: ignore[misc]

        open_file_for_read.close()

        return data_file

    def read(self, file_name: str) -> List[IO[str]]:
        """Read file contents of network file path.

        Data is loaded into a temp file.

        Returns a path or raises an exception.
        """
        try:
            # if there is a wildcard in the filename
            if "*" in file_name:
                RunnerLog(self.task, self.run_id, 10, "Searching for matching files...")

                # a smb file name can be a path, but listpath
                # will only list current folder.
                # we need to split the filename path and iter
                # through the folders that match.

                # get the path up to the *.
                base_dir = str(Path(file_name.split("*")[0]).parent)

                file_list = []
                for _, _, walk_file_list in self._walk(base_dir):
                    for this_file in walk_file_list:
                        if fnmatch.fnmatch(this_file, file_name):
                            file_list.append(this_file)

                RunnerLog(
                    self.task,
                    self.run_id,
                    10,
                    "Found %d file%s.\n%s"
                    % (
                        len(file_list),
                        ("s" if len(file_list) != 1 else ""),
                        "\n".join(file_list),
                    ),
                )

                # if a file was found, try to open.
                return [
                    self.__load_file(file_name, i, len(file_list))
                    for i, file_name in enumerate(file_list, 1)
                ]

            return [self.__load_file(file_name, 1, 1)]
        except BaseException as e:
            raise RunnerException(
                self.task,
                self.run_id,
                10,
                f"File failed to load file from server.\n{e}",
            )

    # pylint: disable=R1710
    def save(self, overwrite: int, file_name: str) -> str:  # type: ignore[return]
        """Load data into network file path, creating location if not existing."""
        try:
            if self.connection is not None:
                dest_path = str(Path(self.connection.path or "").joinpath(file_name))
            else:
                dest_path = str(
                    Path(
                        (
                            Path(
                                Path(sanitize_filename(self.subfolder or ""))
                                / Path(sanitize_filename(self.task.project.name or ""))
                            )
                            if self.subfolder
                            else Path(sanitize_filename(self.task.project.name or ""))
                        )
                        / sanitize_filename(self.task.name or "")
                        / sanitize_filename(self.task.last_run_job_id or "")
                        / file_name
                    )
                )

            # path must be created one folder at a time.. the docs say the path will all be
            # created if not existing, but it doesn't seem to be the case :)
            my_dir = dest_path.split("/")[:-1]

            path_builder = ""
            for my_path in my_dir:
                # only create directories in the backup drive. For tasks
                # the user must already have a usable folder created.
                if self.connection is None:
                    path_builder += my_path + "/"

                    try:
                        self.conn.listPath(self.share_name, path_builder)
                    # pylint: disable=broad-except
                    except OperationFailure:
                        self.conn.createDirectory(self.share_name, path_builder)

            # pylint: disable=useless-else-on-loop
            else:
                if overwrite != 1:
                    try:
                        # try to get security of the file. if it doesn't exist,
                        # we crash and then can create the file.
                        self.conn.getSecurity(self.share_name, dest_path)
                        RunnerLog(
                            self.task,
                            self.run_id,
                            10,
                            "File already exists and will not be loaded",
                        )
                        return dest_path

                    # pylint: disable=broad-except
                    except BaseException:
                        pass

                with open(str(self.dir.joinpath(file_name)), "rb", buffering=0) as file_obj:
                    uploaded_size = self.conn.storeFile(
                        self.share_name, dest_path, file_obj, timeout=120
                    )

            server_name = "backup" if self.connection is None else self.connection.server_name

            RunnerLog(
                self.task,
                self.run_id,
                10,
                f"{file_size(uploaded_size)} uploaded to {server_name} server.",
            )

            return dest_path

        # pylint: disable=broad-except
        except BaseException as e:
            raise RunnerException(
                self.task, self.run_id, 10, f"Failed to save file on server.\n{e}"
            )
