"""SMB Connection Manager.

This module provides a class `Smb` to manage SMB file transfers,
and helper functions to handle connection caching and restoration via Redis.
"""

import fnmatch
import os
import tempfile
from pathlib import Path
from typing import IO, Dict, List, Optional

from flask import current_app as app
from pathvalidate import sanitize_filename
from smbclient import (
    ClientConfig,
    listdir,
    makedirs,
    register_session,
    reset_connection_cache,
    walk,
)
from smbclient.path import getsize
from smbclient.shutil import copyfile
from smbprotocol.exceptions import (
    LogonFailure,
    SMBAuthenticationError,
    SMBException,
    SMBOSError,
    SMBResponseException,
)
from smbprotocol.session import Session

from runner.model import ConnectionSmb, Task
from runner.scripts.em_file import file_size
from runner.scripts.em_messages import RunnerException, RunnerLog
from scripts.crypto import em_decrypt


def connection_json(connection: Session) -> Dict:
    """Convert the connection string to json."""
    return {
        "server_name": connection.server_name,
        "password": em_decrypt(connection.password, app.config["PASS_KEY"]),
        "username": str(connection.username),
    }


def connect(username: str, password: str, server_name: str) -> Session:
    """Connect to SMB server.

    Returns the session for use in connnection_cache
    """
    try:
        sess = register_session(
            server=server_name,
            username=username,
            password=em_decrypt(password, app.config["PASS_KEY"]),
            connection_cache={},
        )
        return sess
    except LogonFailure as err:
        raise ValueError(f"Authentication failed\n{err}")
    except SMBException as err:
        raise ValueError(f"SMB registration failed\n{err}")
    except Exception as err:
        raise ValueError(f"Unexpected error during registration\n{err}")


class Smb:
    """SMB Connection Handler Class.

    Provides methods to read files from and write files to SMB shares.
    Handles wildcard reads, path generation, and connection reuse.
    """

    def __init__(
        self,
        task: Task,
        run_id: Optional[str],
        connection: Optional[ConnectionSmb],
        directory: Path,
    ):
        """Initialize the SMB class with task, run ID, connection, and working directory."""
        self.task = task
        self.run_id = run_id
        self.connection = connection
        self.local_temp_dir = directory

        if self.connection is not None:
            self.share_name = str(self.connection.share_name).strip("/").strip("\\")
            self.username = self.connection.username
            self.password = self.connection.password
            self.server_name = self.connection.server_name
        else:
            # default connection for backups
            self.share_name = app.config["SMB_DEFAULT_SHARE"].strip("/").strip("\\")
            self.username = app.config["SMB_USERNAME"]
            self.password = app.config["SMB_PASSWORD"]
            self.server_name = app.config["SMB_SERVER_NAME"]
            self.subfolder = app.config["SMB_SUBFOLDER"]

        # set global username and password. It sets default just in case username and pw is missing.
        ClientConfig(
            username=app.config["SMB_USERNAME"],
            password=em_decrypt(app.config["SMB_PASSWORD"], app.config["PASS_KEY"]),
        )
        self.cache = {"cache": self.__connect()}

    def __connect(self) -> Session:
        """Connect to SMB server.

        After making a connection we save the session. Next time we need a connection
        we can grab it and attempt to use. If it is no longer connected
        then it will reconnect.
        """
        return connect(
            username=str(self.username),
            password=str(self.password),
            server_name=str(self.server_name),
        )

    def __load_file(self, full_path: str, index: int, length: int) -> IO[bytes]:
        """Copy a file from a smb drive to a local path.

        :param full_path: the full UNC path to the file.
        :param index: the file number that is being downloaded.
        :param length: the amount of files being downloaded.
        """
        original_name = Path(full_path).name
        local_path = Path(self.local_temp_dir) / original_name
        RunnerLog(
            self.task,
            self.run_id,
            10,
            f"({index} of {length}) downloading {original_name}",
        )

        # need to return a file object to be used in em_file steps.
        with tempfile.NamedTemporaryFile(
            mode="wb", delete=False, dir=self.local_temp_dir
        ) as data_file:
            copyfile(f"\\\\{full_path}", data_file.name, connection_cache=self.cache)

        # overwrite existing file if needed.
        if local_path.exists():
            local_path.unlink()
        os.rename(data_file.name, local_path)

        data_file.name = str(local_path)
        return data_file

    def __smb_file_exists(self, smb_path: str) -> bool:
        """Check if a file exists on an SMB share (more reliable than exists)."""
        try:
            dir_path = Path(smb_path).parent
            file_name = Path(smb_path).name
            return file_name in listdir(dir_path, connection_cache=self.cache)
        except SMBOSError as e:
            raise RunnerException(
                self.task,
                self.run_id,
                10,
                f"Failed to check if file exists.\n{e}",
            )

    def read(self, file_name: str) -> List[IO[bytes]]:
        """Read file contents of network file path.

        Data is loaded into a temp file.

        Returns a path or raises an exception.
        """
        # get full path
        # if the connection is none, then the file_name has the full path.
        if self.connection is not None:
            # lets get the full path and checking if the file_name already has the connection.path in it.
            # this is for older tasks where we had to include the path even though it was already in the connection.
            base = Path(sanitize_filename(self.server_name or "")) / Path(
                sanitize_filename(self.share_name or "")
            )
            if "/*" in file_name:
                file_name_path = Path(file_name.split("*")[0].strip("/"))
            else:
                file_name_path = Path(file_name.strip("/")).parent

            conn_path = (self.connection.path or "").strip("/")
            if conn_path and file_name_path.match(conn_path):
                file_path = str(base / Path(file_name.strip("/")))
            else:
                file_path = str(base / conn_path / Path(file_name.strip("/")))
        else:
            file_path = file_name

        try:
            # if there is a wildcard in the filename
            if "*" in file_name:
                RunnerLog(self.task, self.run_id, 10, "Searching for matching files...")

                # we need to split the file path from a * to get a base path
                # this will be passed into walk funcion
                # walk will generate file names in a directory and everything below it.

                # get the path up to the *.
                base_dir = f"\\\\{str(Path(file_path).parent).strip('*') if file_name.split('*')[0] else Path(file_path.split('*')[0])}"
                file_path_name = str(Path(file_path).name)
                file_list = []
                if self.task.source_smb_ignore_subfolders == 1:
                    for filename in listdir(base_dir, connection_cache=self.cache):
                        if fnmatch.fnmatch(filename, file_path_name):
                            file_list += [
                                # remove the \\ from the base_dir here.
                                str(Path(base_dir.replace("\\\\", "")) / filename)
                            ]
                else:
                    for path, _, filenames in walk(base_dir, connection_cache=self.cache):
                        file_list += [
                            str(Path(path) / f)
                            for f in filenames
                            if fnmatch.fnmatch(f, file_path_name)
                        ]

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
                    self.__load_file(full_path=f_name, index=i, length=len(file_list))
                    for i, f_name in enumerate(file_list, 1)
                ]

            return [self.__load_file(full_path=file_path, index=1, length=1)]
        except BaseException as e:
            raise RunnerException(
                self.task,
                self.run_id,
                10,
                f"File failed to load file from server.\n{e}",
            )

    # pylint: disable=R1710
    def save(self, overwrite: int, file_name: str) -> str:  # type: ignore[return]
        """Upload a local file to SMB server. Will create directories if needed.

        If overwrite is disabled and file exists, skips copy.
        """
        try:
            base_path = Path(sanitize_filename(self.server_name or "")) / Path(
                sanitize_filename(self.share_name or "")
            )
            if self.connection is not None:
                dest_path = str(
                    base_path / Path(self.connection.path.strip("/") or "").joinpath(file_name)
                )
            else:
                dest_path = str(
                    Path(
                        base_path
                        / (
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

            smb_path = f"\\\\{dest_path}"

            my_dir = str(Path(smb_path).parent)

            # makedirs will create the folders. If parent doesn't exist, it will create that also.
            try:
                makedirs(my_dir, exist_ok=True, connection_cache=self.cache)
            except (OSError, SMBException, SMBResponseException, SMBAuthenticationError) as e:
                raise RunnerException(
                    self.task,
                    self.run_id,
                    10,
                    f"Failed to create SMB directory: {my_dir}\n{e}",
                )

            if overwrite != 1 and self.__smb_file_exists(smb_path):
                RunnerLog(
                    self.task,
                    self.run_id,
                    10,
                    "File already exists and will not be loaded",
                )
                self.__close()
                return smb_path

            try:

                copyfile(
                    self.local_temp_dir.joinpath(file_name), smb_path, connection_cache=self.cache
                )
            except FileNotFoundError as e:
                raise RunnerException(self.task, self.run_id, 10, f"Source file not found: {e}")
            except PermissionError as e:
                raise RunnerException(
                    self.task,
                    self.run_id,
                    10,
                    f"Permission denied while copying file: {e}",
                )
            except Exception as e:
                raise RunnerException(
                    self.task,
                    self.run_id,
                    10,
                    f"Unexpected error during file copy: {e}",
                )
            uploaded_size = getsize(smb_path)

            server_name = "backup" if self.connection is None else self.connection.server_name

            RunnerLog(
                self.task,
                self.run_id,
                10,
                f"{file_size(uploaded_size)} uploaded to {server_name} server.",
            )
            self.__close()
            return smb_path

        # pylint: disable=broad-except
        except Exception as e:
            raise RunnerException(
                self.task, self.run_id, 10, f"Failed to save file on server.\n{e}"
            )

    def __close(self) -> None:
        try:
            reset_connection_cache(connection_cache=self.cache)
        except BaseException as e:
            raise RunnerException(self.task, self.run_id, 10, f"Failed to close connection.\n{e}")
