"""FTP connection manager."""

import csv
import fnmatch
import ftplib  # noqa: S402
import os
import re
import sys
import tempfile
import time
from ftplib import FTP  # noqa: S402
from pathlib import Path
from typing import IO, Any, Dict, Generator, List, Optional, Tuple

from flask import current_app as app

from runner.model import ConnectionFtp, Task
from runner.scripts.em_messages import RunnerException, RunnerLog

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from crypto import em_decrypt


def connection_json(connection: ConnectionFtp) -> Dict:
    """Convert the connection string to json."""
    return {
        "address": connection.address,
        "port": connection.port or 22,
        "password": em_decrypt(connection.password, app.config["PASS_KEY"]),
        "username": str(connection.username),
    }


def connect(connection: ConnectionFtp) -> FTP:
    """Connect to ftp server."""
    try:
        # there is no timeout in paramiko so...
        # continue to attemp to login during time limit
        # if we are getting timeout exceptions
        timeout = time.time() + 60 * 3  # 2 mins from now
        while True:
            try:
                conn = FTP(connection.address or "")  # noqa: S321
                conn.login(
                    user=(connection.username or ""),
                    passwd=(em_decrypt(connection.password, app.config["PASS_KEY"]) or ""),
                )
                break
            except ftplib.error_reply as e:
                # pylint: disable=no-else-continue
                if time.time() <= timeout:
                    time.sleep(10)  # wait 10 sec before retrying
                    continue
                elif time.time() > timeout:
                    # pylint: disable=raise-missing-from
                    raise ValueError("Connection timeout.")

                else:
                    raise ValueError(f"Connection failed.\n{e}")

        return conn

    except BaseException as e:
        raise ValueError(f"Connection failed.\n{e}")


class Ftp:
    """FTP Connection Handler Class.

    Function takes a file name and source file path
    and will upload the file to the fpt location
    specified in the task settings.
    """

    def __init__(
        self,
        task: Task,
        run_id: Optional[str],
        connection: ConnectionFtp,
        directory: Path,
    ):
        """Set up class parameters."""
        self.task = task
        self.run_id = run_id
        self.connection = connection
        self.dir = directory
        self.conn = self.__connect()

    def __connect(self) -> FTP:
        try:
            return connect(self.connection)
        except ValueError as e:
            raise RunnerException(self.task, self.run_id, 13, str(e))

    def _walk(self, directory: str) -> Generator[Tuple[str, List[Any], List[str]], None, None]:
        dirs = []
        nondirs = []

        for name, stats in self.conn.mlsd(directory):
            if stats["type"] == "dir":
                dirs.append(name)
            elif stats["type"] == "file":
                nondirs.append(str(Path(directory).joinpath(name)))

        yield directory, dirs, nondirs

        # Recurse into sub-directories
        for dirname in dirs:
            new_path = str(Path(directory).joinpath(dirname))
            yield from self._walk(new_path)

    def __load_file(self, file_name: str) -> IO[str]:
        """Download file from sftp server."""
        my_binary: List[bytes] = []

        def handle_binary(more_data: bytes) -> None:
            my_binary.append(more_data)

        self.conn.retrbinary("RETR " + file_name, callback=handle_binary)
        data = "".join([str(x) for x in my_binary])

        with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=self.dir) as data_file:
            if self.task.source_sftp_ignore_delimiter != 1 and self.task.source_sftp_delimiter:
                my_delimiter = self.task.source_sftp_delimiter or ","

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

        return data_file

    def __clean_path(self, path: str) -> str:
        path = re.sub(r"/$", "", path, re.MULTILINE)
        path = re.sub(r"^/", "", path, re.MULTILINE)

        return "/" + path

    def read(self, file_name: str) -> List[IO[str]]:
        """Read a file from FTP server.

        Data is loaded into a temp file.

        Returns a path or raises an exception.
        """
        try:
            self.conn.cwd(self.__clean_path(self.connection.path or "/"))

            if "*" in file_name:
                RunnerLog(self.task, self.run_id, 13, "Searching for matching files...")

                # get the path up to the *
                base_dir = str(Path(file_name.split("*")[0]).parent)

                file_list = []
                for _, _, walk_file_list in self._walk(base_dir):
                    for this_file in walk_file_list:
                        if fnmatch.fnmatch(this_file, file_name):
                            file_list.append(this_file)

                RunnerLog(
                    self.task,
                    self.run_id,
                    13,
                    "Found %d file%s.\n%s"
                    % (
                        len(file_list),
                        ("s" if len(file_list) != 1 else ""),
                        "\n".join(file_list),
                    ),
                )
                return [self.__load_file(file_name) for file_name in file_list]

            return [self.__load_file(file_name)]

        # pylint: disable=broad-except
        except BaseException as e:
            raise RunnerException(
                self.task,
                self.run_id,
                13,
                f"File failed to load file from server.\n{e}",
            )

    def save(self, overwrite: int, file_name: str) -> None:
        """Use to copy local file to FTP server.

        :returns: true if successful.
        """
        self.__connect()
        try:
            self.conn.cwd(self.connection.path or "/")

        # pylint: disable=broad-except
        except BaseException as e:
            raise RunnerException(self.task, self.run_id, 13, f"Failed to change path.\n{e}")

        if overwrite != 1:
            try:
                self.conn.size(file_name)
                RunnerLog(
                    self.task,
                    self.run_id,
                    13,
                    "File already exists and will not be loaded.",
                )
                self.__close()

                return

            # pylint: disable=broad-except
            except BaseException:
                pass

        try:
            with open(str(self.dir.joinpath(file_name)), "rb") as file:
                self.conn.storbinary("STOR " + file_name, file)

            RunnerLog(self.task, self.run_id, 13, "File loaded to server.")

            self.__close()

        except BaseException as e:
            raise RunnerException(
                self.task, self.run_id, 13, f"Failed to save file on server.\n{e}"
            )

    def __close(self) -> None:
        try:
            self.conn.close()

        except BaseException as e:
            raise RunnerException(self.task, self.run_id, 13, f"Failed to close connection.\n{e}")
