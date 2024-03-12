"""SFTP connection manager."""

import csv
import fnmatch
import os
import re
import sys
import tempfile
import time
import warnings
from pathlib import Path
from stat import S_ISDIR
from typing import IO, Any, Dict, Generator, List, Optional, Tuple

import paramiko
from cryptography.utils import CryptographyDeprecationWarning
from flask import current_app as app

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
    from paramiko import SFTPClient, SFTPFile, Transport

from runner.model import ConnectionSftp, Task
from runner.scripts.em_file import file_size
from runner.scripts.em_messages import RunnerException, RunnerLog

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from crypto import em_decrypt


def connection_key(connection: ConnectionSftp) -> Optional[paramiko.pkey.PKey]:
    """Build a ssh key from a string."""
    key = None
    if connection.key:
        with tempfile.NamedTemporaryFile(mode="w+", newline="") as key_file:
            key_file.write(em_decrypt(connection.key, app.config["PASS_KEY"]))
            key_file.seek(0)

            key = paramiko.RSAKey.from_private_key_file(
                key_file.name,
                password=(
                    em_decrypt(connection.key_password, app.config["PASS_KEY"])
                    if connection.key_password
                    else None
                ),
            )

    return key


def connection_json(connection: ConnectionSftp) -> Dict:
    """Convert the connection string to json."""
    return {
        "address": connection.address,
        "port": connection.port or 22,
        "key": em_decrypt(connection.key, app.config["PASS_KEY"]),
        "password": em_decrypt(connection.password, app.config["PASS_KEY"]),
        "key_password": em_decrypt(connection.key_password, app.config["PASS_KEY"]),
        "username": str(connection.username),
    }


def connect(connection: ConnectionSftp) -> Tuple[Transport, SFTPClient]:
    """Connect to sftp server."""
    try:
        # there is no timeout in paramiko so...
        # continue to attemp to login during time limit
        # if we are getting timeout exceptions
        timeout = time.time() + 60 * 3  # 2 mins from now
        while True:
            try:
                transport = paramiko.Transport(
                    f"{connection.address}:{(connection.port or 22)}",
                    disabled_algorithms={"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]},
                )

                key = connection_key(connection)

                if key and connection.password and connection.username:
                    transport.start_client(event=None, timeout=15)
                    transport.get_remote_server_key()
                    transport.auth_publickey(connection.username, key, event=None)
                    transport.auth_password(
                        connection.username,
                        (
                            em_decrypt(connection.password, app.config["PASS_KEY"])
                            if connection.password
                            else ""
                        ),
                        event=None,
                    )

                else:
                    transport.connect(
                        username=str(connection.username),
                        password=(
                            em_decrypt(connection.password, app.config["PASS_KEY"])
                            if connection.password
                            else ""
                        ),
                        pkey=key,
                    )

                conn = paramiko.SFTPClient.from_transport(transport)
                if conn is None:
                    raise ValueError("Failed to create connection.")

                break
            except (paramiko.ssh_exception.AuthenticationException, EOFError) as e:
                # pylint: disable=no-else-continue
                if str(e) == "Authentication timeout." and time.time() <= timeout:
                    time.sleep(10)  # wait 10 sec before retrying
                    continue
                elif time.time() > timeout:
                    raise ValueError("Connection timeout.")

                raise ValueError(f"Connection failed.\n{e}")

        return (transport, conn)

    except BaseException as e:
        raise ValueError(f"Connection failed.\n{e}")


class Sftp:
    """SFTP Connection Handler Class.

    Function takes a file name and source file path
    and will upload the file to the sfpt location
    specified in the task settings.
    """

    def __init__(
        self,
        task: Task,
        run_id: Optional[str],
        connection: ConnectionSftp,
        directory: Path,
    ):
        """Set up class parameters."""
        self.task = task
        self.run_id = run_id
        self.connection = connection
        self.dir = directory
        self.transport, self.conn = self.__connect()

    def __connect(self) -> Tuple[Transport, SFTPClient]:
        try:
            return connect(self.connection)
        except ValueError as e:
            raise RunnerException(self.task, self.run_id, 9, str(e))

    def _walk(self, directory: str) -> Generator[Tuple[str, List[Any], List[str]], None, None]:
        dirs = []
        nondirs = []

        for entry in self.conn.listdir_attr(directory):
            if S_ISDIR(entry.st_mode or 0):
                dirs.append(entry.filename)
            else:
                nondirs.append(str(Path(directory).joinpath(entry.filename)))

        yield directory, dirs, nondirs

        # Recurse into sub-directories
        for dirname in dirs:
            new_path = str(Path(directory).joinpath(dirname))
            yield from self._walk(new_path)

    def __load_file(self, file_name: str) -> IO[str]:
        """Download file from sftp server."""
        RunnerLog(
            self.task,
            self.run_id,
            9,
            f"Downloading {file_size(self.conn.stat(file_name).st_size or 0)} from {file_name}.",
        )

        sftp_file = self.conn.open(file_name, mode="r")

        def load_data(file_obj: SFTPFile) -> Generator:
            with file_obj as this_file:
                while True:
                    data = this_file.read(1024).decode("utf-8", "replace")  # type: ignore[attr-defined]
                    if not data:
                        break
                    yield data

        with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=self.dir) as data_file:
            for data in load_data(sftp_file):
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

        sftp_file.close()
        RunnerLog(
            self.task,
            self.run_id,
            9,
            f"{file_size(Path(data_file.name).stat().st_size)} saved  to {file_name}.",
        )

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
            self.conn.chdir(self.__clean_path(self.connection.path or "/"))

            if "*" in file_name:
                RunnerLog(self.task, self.run_id, 9, "Searching for matching files...")

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
                    9,
                    "Found %d file%s.\n%s"
                    % (
                        len(file_list),
                        ("s" if len(file_list) != 1 else ""),
                        "\n".join(file_list),
                    ),
                )
                return [self.__load_file(file_name) for file_name in file_list]

            return [self.__load_file(file_name)]

        except BaseException as e:
            raise RunnerException(
                self.task, self.run_id, 9, f"File failed to load file from server.\n{e}"
            )

    def save(self, overwrite: int, file_name: str) -> None:
        """Use to copy local file to FTP server.

        :returns: true if successful.
        """
        try:
            self.conn.chdir(self.__clean_path(self.connection.path or "/"))

        except BaseException as e:
            raise RunnerException(self.task, self.run_id, 9, f"Failed to change path.\n{e}")

        if overwrite != 1:
            try:
                self.conn.stat(file_name)
                RunnerLog(
                    self.task,
                    self.run_id,
                    9,
                    "File already exists and will not be loaded.",
                )

                self.__close()

                return

            except BaseException:
                # continue of file does not exist.
                pass

        try:
            #  some sftp server do not allow overwrites. When attempted will
            #  return a permission error or other. So we log if the file exists
            #  to help with debugging.
            try:
                self.conn.stat(file_name)
                RunnerLog(
                    self.task,
                    self.run_id,
                    9,
                    "File already exist. Attempting to overwrite.",
                )

            # pylint: disable=broad-except
            except BaseException:
                # continue of file does not exist.
                pass

            self.conn.put(str(self.dir.joinpath(file_name)), file_name, confirm=True)

            # file is now confirmed on server w/ confirm=True flag
            RunnerLog(
                self.task,
                self.run_id,
                9,
                f"{file_size(self.conn.stat(file_name).st_size or 0)} stored on server as {file_name}.",
            )

            self.__close()

        except BaseException as e:
            raise RunnerException(
                self.task, self.run_id, 9, f"Failed to save file on server.\n{e}"
            )

    def __close(self) -> None:
        try:
            self.conn.close()
            self.transport.close()

        except BaseException as e:
            raise RunnerException(self.task, self.run_id, 9, f"Failed to close connection.\n{e}")
