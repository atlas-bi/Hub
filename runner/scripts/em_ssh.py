"""SSH connection handler."""

import select
import sys
import time
import warnings
from pathlib import Path
from typing import Dict, Optional

from cryptography.utils import CryptographyDeprecationWarning

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
    import paramiko

from flask import current_app as app

from runner.model import ConnectionSsh, Task
from runner.scripts.em_messages import RunnerException, RunnerLog

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")

from crypto import em_decrypt


def connection_json(connection: ConnectionSsh) -> Dict:
    """Convert connection string to json."""
    return {
        "address": connection.address,
        "port": connection.port or 22,
        "password": em_decrypt(connection.password, app.config["PASS_KEY"]),
        "username": str(connection.username),
    }


def connect(connection: ConnectionSsh) -> paramiko.SSHClient:
    """Connect to SSH server."""
    session = paramiko.SSHClient()
    session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    session.connect(
        hostname=str(connection.address),
        port=(connection.port or 22),
        username=connection.username,
        password=em_decrypt(connection.password, app.config["PASS_KEY"]),
        timeout=5000,
        allow_agent=False,
        look_for_keys=False,
    )

    return session


class Ssh:
    """SSH Connection Handler Class."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        task: Task,
        run_id: Optional[str],
        connection: ConnectionSsh,
        command: str,
    ):
        """Set up class parameters."""
        self.connection = connection
        self.task = task
        self.run_id = run_id
        self.command = command
        self.session = self.__connect()

    def __connect(self) -> paramiko.SSHClient:
        try:
            return connect(self.connection)
        except BaseException as e:
            raise RunnerException(self.task, self.run_id, 19, f"Failed to connect.\n{e}")

    def __close(self) -> None:
        try:
            self.session.close()

        except BaseException as e:
            raise RunnerException(self.task, self.run_id, 19, f"Failed to disconnect.\n{e}")

    def run(self) -> None:
        """Run an SSH Command.

        Some code from https://stackoverflow.com/a/32758464 - thanks!
        :returns: Output from command.
        """
        timeout = 600
        try:
            RunnerLog(
                self.task,
                self.run_id,
                19,
                "Starting command.",
            )
            # pylint: disable=W0612
            stdin, stdout, stderr = self.session.exec_command(  # noqa: S601
                ";".join(self.command.splitlines()), timeout=timeout
            )

            channel = stdout.channel

            stdin.close()
            channel.shutdown_write()

            stderr_data = b""
            stdout_data = b""

            while not channel.closed or channel.recv_ready() or channel.recv_stderr_ready():
                got_chunk = False
                readq, _, _ = select.select([stdout.channel], [], [], timeout)

                for chunk in readq:
                    if chunk.recv_ready():
                        stdout_data += stdout.channel.recv(len(chunk.in_buffer))
                        got_chunk = True
                    if chunk.recv_stderr_ready():
                        stderr_data += stderr.channel.recv_stderr(len(chunk.in_stderr_buffer))
                        got_chunk = True

                    if (
                        not got_chunk
                        and stdout.channel.exit_status_ready()
                        and not stderr.channel.recv_stderr_ready()
                        and not stdout.channel.recv_ready()
                    ):
                        # indicate that we're not going to read from this channel anymore
                        stdout.channel.shutdown_read()
                        # close the channel
                        stdout.channel.close()
                        break  # exit as remote side is finished and our buffers are empty

                time.sleep(0.01)

                # timeout after a few minutes

            out = stdout_data.decode("utf-8") or "None"
            err = stderr_data.decode("utf-8") or "None"

            if stdout.channel.recv_exit_status() != 0 or stderr_data != b"":
                raise ValueError(
                    f"Command stdout: {out}\nCommand stderr: {err}",
                )

            RunnerLog(
                self.task,
                self.run_id,
                19,
                f"Command output:\n{out}",
            )

        except BaseException as e:
            raise RunnerException(self.task, self.run_id, 19, f"Failed to run command.\n{e}")

        self.__close()
