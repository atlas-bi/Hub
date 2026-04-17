"""Functions used to run system commands."""

import os
import re
import shlex
import subprocess
from typing import List, Optional, Union

from runner.model import Task
from runner.scripts.em_messages import RunnerLog

_SHELL_META = re.compile(r"[|&;<>$`\\!]")


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
        self.env = os.environ.copy()
        self.env["PATH"] = (
            "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:"
            + self.env.get("PATH", "")
        )
        self.success_msg = success_msg
        self.error_msg = error_msg
        self.run_id = run_id

    @staticmethod
    def _build_cmd(cmd: str) -> Union[List[str], str]:
        """Return a safe argv list, or ['/bin/sh', '-c', cmd] for shell metacharacters.

        Using an explicit argv list with shell=False avoids shell=True entirely.
        """
        if _SHELL_META.search(cmd):
            return ["/bin/sh", "-c", cmd]
        return shlex.split(cmd)

    def shell(self) -> str:
        """Run input command as a shell command."""
        try:
            cmd_arg = self._build_cmd(self.cmd)
            out_bytes = subprocess.check_output(
                cmd_arg,
                stderr=subprocess.STDOUT,
                shell=False,  # noqa: S603  # nosec B603
                env=self.env,
            )
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
            cmd_arg = self._build_cmd(self.cmd)
            result = subprocess.run(
                cmd_arg,
                shell=False,  # noqa: S603  # nosec B603
                capture_output=True,
                check=False,
                text=True,
                env=self.env,
            )
            out = result.stdout + result.stderr

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
