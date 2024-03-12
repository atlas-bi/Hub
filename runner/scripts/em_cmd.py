"""Functions used to run system commands."""

import os
import re
import shlex
import subprocess
from typing import Optional

from runner.model import Task
from runner.scripts.em_messages import RunnerLog


class Cmd:
    """System command runner."""

    # pylint: disable=too-few-public-methods
    def __init__(
        self,
        task: Task,
        run_id: Optional[str],
        cmd: str,
        success_msg: str,
        error_msg: str,
    ) -> None:
        """Set system path and variables."""
        self.task = task
        self.cmd = cmd
        self.success_msg = success_msg
        self.error_msg = error_msg
        self.run_id = run_id

    def shell(self) -> str:
        """Run input command as a shell command."""
        try:
            env = {
                **os.environ,
                "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:"
                + os.environ["PATH"],
            }
            cmd_args = shlex.split(self.cmd)
            out_bytes = subprocess.check_output(cmd_args, stderr=subprocess.STDOUT, env=env)
            out = out_bytes.decode("utf-8")

            if "Error" in out:
                RunnerLog(
                    self.task,
                    self.run_id,
                    17,
                    self.error_msg
                    + ("\n" if out != "" else "")
                    + re.sub(
                        r"(?<=:)([^:]+?)(?=@)",
                        "*****",
                        out,
                        flags=re.IGNORECASE | re.MULTILINE,
                    ),
                    1,
                )

                raise ValueError("Error")

            RunnerLog(
                self.task,
                self.run_id,
                17,
                self.success_msg + (("\n" + out) if out != "" else ""),
            )

            return out

        except subprocess.CalledProcessError as e:
            out = e.output.decode("utf-8")
            RunnerLog(
                self.task,
                self.run_id,
                17,
                self.error_msg
                + (("\n" + out) if out != "" else "")
                + "\n"
                + re.sub(
                    r"(?<=:)([^:]+?)(?=@)",
                    "*****",
                    str(e),
                    flags=re.IGNORECASE | re.MULTILINE,
                ),
                1,
            )

            raise

        except BaseException as e:
            RunnerLog(
                self.task,
                self.run_id,
                17,
                "Command failed.\n"
                + (("\n" + out) if out != "" else "")
                + "\n"
                + re.sub(
                    r"(?<=:)([^:]+?)(?=@)",
                    "*****",
                    str(e),
                    flags=re.IGNORECASE | re.MULTILINE,
                ),
                1,
            )
            raise

    def run(self) -> str:
        """Run input command as a subprocess command."""
        try:
            env = {
                **os.environ,
                "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:"
                + os.environ["PATH"],
            }
            cmd_args = shlex.split(self.cmd)
            out = subprocess.Popen(
                cmd_args, stderr=subprocess.PIPE, stdout=subprocess.PIPE, env=env
            ).read()

            if "Error" in out:
                RunnerLog(
                    self.task,
                    self.run_id,
                    17,
                    self.error_msg + ("\n" if out != "" else "") + out,
                    1,
                )

                raise ValueError("Error")

            RunnerLog(self.task, self.run_id, 17, self.success_msg)

            return out

        # pylint: disable=broad-except
        except BaseException as e:
            RunnerLog(
                self.task,
                self.run_id,
                17,
                self.error_msg + ("\n" if out != "" else "") + "\n" + str(e),
                1,
            )
            raise
