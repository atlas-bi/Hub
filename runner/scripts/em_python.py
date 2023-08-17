"""Python script runner."""


import datetime
import sys
from itertools import chain
from pathlib import Path
from typing import IO, List, Optional, Union

import regex as re
from flask import current_app as app
from flask import json

from runner.model import Task
from runner.scripts import em_ftp, em_sftp, em_smb, em_ssh
from runner.scripts.em_cmd import Cmd
from runner.scripts.em_messages import RunnerLog
from runner.scripts.em_params import ParamLoader

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")

from crypto import em_decrypt


class PyProcesser:
    """Python Script Runner.

    Script will create a virtual environment, run a script or module, and then
    cleanup by removing all files.
    """

    def __init__(
        self,
        task: Task,
        run_id: str,
        directory: Path,
        script: str,
        source_files: List[IO[str]],
        params: ParamLoader,
    ) -> None:
        """Set up class parameters."""
        self.task = task
        self.run_id = run_id
        self.script = script
        self.params = params
        self.output = ""

        self.env_name = self.run_id + "_env"
        self.job_path = directory
        self.source_files = source_files
        # self.base_path = str(self.job_path / "venv")

        self.env_path = str(self.job_path / self.env_name)

        Path(self.env_path).mkdir(parents=True, exist_ok=True)

    def run(self) -> Optional[List[Path]]:
        """Run processing script.

        :returns: Any output from the script.
        """
        self.__build_env()
        self.__pip_install()
        self.__run_script()

        # if output is not a file list, then swallow it.

        if isinstance(self.output, List):
            return self.output
        return None

    def __build_env(self) -> None:
        """Build a virtual environment.

        Runs command:
        .. code-block:: console

            virtualenv <path>

        """
        try:
            Cmd(
                task=self.task,
                run_id=self.run_id,
                cmd=f'virtualenv "{self.env_path}"',
                success_msg=f"Environment created.\n{self.env_path}",
                error_msg=f"Failed to create environment.\n{self.env_path}",
            ).shell()

        # pylint: disable=broad-except
        except BaseException as e:
            RunnerLog(
                self.task,
                self.run_id,
                14,
                f"Failed to build environment.\n{self.env_path}\n{e}",
                1,
            )

            raise

    def __pip_install(self) -> None:
        r"""Get includes from script.

        get import (...)
        ^\s*?import\K\s+[^\.][^\s]+?\\s+?$

        get import (...) as ...
        ^\s*?import\K\s+[^\.][^\s]+?(?=\s)

        get from (...) import (...)
        ^\s*?from\K\s+[^\.].+?(?=import)
        """
        try:
            imports = []

            # use requirements.txt
            requirements_text = list(Path(self.job_path).rglob("requirements.txt"))

            # use pyproject.toml
            pyproject_toml = Path(self.job_path / "pyproject.toml")

            if len(requirements_text) > 0:
                cmd = (
                    f'"{self.env_path}/bin/pip" install --disable-pip-version-check --quiet -r '
                    + " -r ".join([f'"{x.resolve()}"' for x in requirements_text])
                )
                Cmd(
                    task=self.task,
                    run_id=self.run_id,
                    cmd=cmd,
                    success_msg="Imports successfully installed from requirements.txt: "
                    + " with command: "
                    + "\n"
                    + cmd,
                    error_msg="Failed to install imports with command: " + "\n" + cmd,
                ).shell()

            elif pyproject_toml.is_file():
                # install and setup poetry
                cmd = (
                    f'cd "{self.job_path}" &&'
                    + "virtualenv poetry_env && "
                    + "poetry_env/bin/pip install --disable-pip-version-check --quiet poetry && "
                    + "poetry_env/bin/poetry config --local virtualenvs.create false && "
                    + "poetry_env/bin/poetry lock --no-update"
                )

                Cmd(
                    task=self.task,
                    run_id=self.run_id,
                    cmd=cmd,
                    success_msg="Poetry successfully installed.",
                    error_msg="Failed to install poetry.",
                ).shell()

                # install deps with poetry
                cmd = (
                    f'cd "{self.job_path}" && '
                    + f'. "{self.env_name}/bin/activate" && '
                    + "poetry_env/bin/poetry install && "
                    + "deactivate"
                )
                Cmd(
                    task=self.task,
                    run_id=self.run_id,
                    cmd=cmd,
                    success_msg="Imports successfully installed",
                    error_msg="Failed to install imports.",
                ).shell()

            else:
                # find all scripts in dir, but not in venv
                paths = list(
                    set(Path(self.job_path).rglob("*.py"))
                    - set(Path(self.env_path).rglob("*.py"))
                )

                for this_file in paths:
                    with open(this_file, "r") as my_file:
                        for line in my_file:
                            imports.extend(
                                re.findall(r"^\s*?import\K\s+[^\.][^\s]+?\s+?$", line)
                            )
                            imports.extend(
                                re.findall(r"^\s*?from\K\s+[^\.].+?(?=import)", line)
                            )
                            imports.extend(
                                re.findall(r"^\s*?import\K\s+[^\.][^\s]+?(?=\s)", line)
                            )

                package_map = {
                    "dateutil": "python-dateutil",
                    "smb": "pysmb",
                    "dotenv": "python-dotenv",
                    "azure": "azure-devops",
                }

                # clean list
                imports = [
                    str(
                        package_map.get(
                            x.strip().split(".")[0], x.strip().split(".")[0]
                        )
                    )
                    for x in imports
                    if x.strip() != ""
                ]

                # remove any relative imports
                names = [my_file.stem for my_file in paths]

                imports = list(set(imports) - set(names))

                # remove preinstalled packages from imports
                cmd = f'"{self.env_path}/bin/python" -c "help(\'modules\')"'
                built_in_packages = Cmd(
                    task=self.task,
                    run_id=self.run_id,
                    cmd=cmd,
                    success_msg="Python packages loaded.",
                    error_msg="Failed to get preloaded packages: " + "\n" + cmd,
                ).shell()

                built_in_packages = built_in_packages.split(
                    "Please wait a moment while I gather a list of all available modules..."
                )[1].split("Enter any module name to get more help.")[0]

                cleaned_built_in_packages = [
                    this_out.strip()
                    for this_out in list(
                        chain.from_iterable(
                            [
                                g.split(" ")
                                for g in built_in_packages.split("\n")
                                if g != ""
                            ]
                        )
                    )
                    if this_out.strip() != ""
                ]

                # remove default python packages from list
                imports = [
                    x.strip()
                    for x in imports
                    if x not in cleaned_built_in_packages and x.strip()
                ]

                # try to install
                if len(imports) > 0:
                    cmd = (
                        f'"{self.env_path}/bin/pip" install --disable-pip-version-check --quiet '
                        + " ".join([str(x) for x in imports])
                    )
                    Cmd(
                        task=self.task,
                        run_id=self.run_id,
                        cmd=cmd,
                        success_msg="Imports successfully installed: "
                        + ", ".join([str(x) for x in imports])
                        + " with command: "
                        + "\n"
                        + cmd,
                        error_msg="Failed to install imports with command: "
                        + "\n"
                        + cmd,
                    ).shell()

        except BaseException as e:
            RunnerLog(
                self.task,
                self.run_id,
                14,
                f"Failed to install packages.\n{self.env_path}\n{e}",
                1,
            )
            raise

    def __run_script(self) -> None:
        try:
            # pass the source connection info into the script
            env = ""
            connection = {}
            if self.task.source_type_id == 1:  # sql
                external_db = self.task.source_database_conn
                if external_db.database_type.id == 1:  # postgres
                    connection = {
                        "connection_string": em_decrypt(
                            external_db.connection_string, app.config["PASS_KEY"]
                        ),
                        "timeout": external_db.timeout
                        or app.config["DEFAULT_SQL_TIMEOUT"],
                    }

                elif external_db.database_type.id == 2:  # mssql
                    connection = {
                        "connection_string": em_decrypt(
                            external_db.connection_string, app.config["PASS_KEY"]
                        ),
                        "timeout": external_db.timeout
                        or app.config["DEFAULT_SQL_TIMEOUT"],
                    }
            elif self.task.source_type_id == 2:  # smb file
                connection = em_smb.connection_json(self.task.source_smb_conn)
            elif self.task.source_type_id == 3:  # sftp file
                connection = em_sftp.connection_json(self.task.source_sftp_conn)
            elif self.task.source_type_id == 4:  # ftp file
                connection = em_ftp.connection_json(self.task.source_ftp_conn)
            elif self.task.source_type_id == 6:  # ssh command
                connection = em_ssh.connection_json(self.task.source_ssh_conn)

            def clean_string(text: Optional[Union[str, int, datetime.datetime]]) -> str:
                return str(text).replace("'", "").replace('"', "")

            project_data = {
                "id": clean_string(self.task.project.id),
                "name": clean_string(self.task.project.name),
                "description": clean_string(self.task.project.description),
                "owner_id": clean_string(self.task.project.owner_id),
                "cron": clean_string(self.task.project.cron),
                "cron_year": clean_string(self.task.project.cron_year),
                "cron_month": clean_string(self.task.project.cron_month),
                "cron_week": clean_string(self.task.project.cron_week),
                "cron_day": clean_string(self.task.project.cron_day),
                "cron_week_day": clean_string(self.task.project.cron_week_day),
                "cron_hour": clean_string(self.task.project.cron_hour),
                "cron_min": clean_string(self.task.project.cron_min),
                "cron_sec": clean_string(self.task.project.cron_sec),
                "cron_start_date": clean_string(self.task.project.cron_start_date),
                "cron_end_date": clean_string(self.task.project.cron_end_date),
                "intv": clean_string(self.task.project.intv),
                "intv_type": clean_string(self.task.project.intv_type),
                "intv_value": clean_string(self.task.project.intv_value),
                "intv_start_date": clean_string(self.task.project.intv_start_date),
                "intv_end_date": clean_string(self.task.project.intv_end_date),
                "ooff_date": clean_string(self.task.project.ooff),
                "created": clean_string(self.task.project.created),
                "creator_id": clean_string(self.task.project.creator_id),
                "updated": clean_string(self.task.project.updated),
                "updater_id": clean_string(self.task.project.updater_id),
                "sequence_tasks": clean_string(self.task.project.sequence_tasks),
            }

            env += f"PROJECT='{json.dumps(project_data)}' "

            task_data = {
                "id": clean_string(self.task.id),
                "name": clean_string(self.task.name),
                "project_id": clean_string(self.task.project_id),
                "status_id": clean_string(self.task.status_id),
                "status": clean_string(self.task.status.name),
                "enabled": clean_string(self.task.enabled),
                "order": clean_string(self.task.order),
                "last_run": clean_string(self.task.last_run),
                "next_run": clean_string(self.task.next_run),
                "last_run_job_id": clean_string(self.task.last_run_job_id),
                "created": clean_string(self.task.created),
                "creator_id": clean_string(self.task.creator_id),
                "updated": clean_string(self.task.updated),
                "updater_id": clean_string(self.task.updater_id),
                "source_type_id": clean_string(self.task.source_type_id),
                "source_database_id": clean_string(self.task.source_database_id),
                "source_query_type_id": clean_string(self.task.source_query_type_id),
                "source_query_include_header": clean_string(
                    self.task.source_query_include_header
                ),
                "source_git": clean_string(self.task.source_git),
                "source_devops": clean_string(self.task.source_devops),
                "source_url": clean_string(self.task.source_url),
                "source_require_sql_output": clean_string(
                    self.task.source_require_sql_output
                ),
                "enable_source_cache": clean_string(self.task.enable_source_cache),
                "destination_file_delimiter": clean_string(
                    self.task.destination_file_delimiter
                ),
                "destination_file_name": clean_string(self.task.destination_file_name),
                "destination_ignore_delimiter": clean_string(
                    self.task.destination_ignore_delimiter
                ),
                "destination_file_line_terminator": clean_string(
                    self.task.destination_file_line_terminator
                ),
                "destination_quote_level_id": clean_string(
                    self.task.destination_quote_level_id
                ),
                "destination_create_zip": clean_string(
                    self.task.destination_create_zip
                ),
                "destination_zip_name": clean_string(self.task.destination_zip_name),
                "destination_file_type_id": clean_string(
                    self.task.destination_file_type_id
                ),
                "email_completion": clean_string(self.task.email_completion),
                "email_completion_log": clean_string(self.task.email_completion_log),
                "email_completion_file": clean_string(self.task.email_completion_file),
                "email_completion_file_embed": clean_string(
                    self.task.email_completion_file_embed
                ),
                "email_completion_dont_send_empty_file": clean_string(
                    self.task.email_completion_dont_send_empty_file
                ),
                "email_completion_recipients": clean_string(
                    self.task.email_completion_recipients
                ),
                "email_completion_message": clean_string(
                    self.task.email_completion_message
                ),
                "email_error": clean_string(self.task.email_error),
                "email_error_recipients": clean_string(
                    self.task.email_error_recipients
                ),
                "email_error_message": clean_string(self.task.email_error_message),
                "max_retries": clean_string(self.task.max_retries),
                "est_duration": clean_string(self.task.est_duration),
            }

            env = f"TASK='{json.dumps(task_data)}' "

            # if data files exist, pass them as a param.
            env += f"CONNECTION='{json.dumps(connection)}' " if connection else ""

            # create environment from params
            env += ("").join(
                [
                    f'{re.sub(r"[^a-zA-Z_]", "", key)}="{value}" '
                    for key, value in self.params.read().items()
                ]
            )

            cmd = (
                f'{env}"{self.env_path}/bin/python" "{self.job_path}/{self.script}" '
            ) + " ".join([f'"{x.name}"' for x in self.source_files])

            self.output = Cmd(
                task=self.task,
                run_id=self.run_id,
                cmd=cmd,
                success_msg="Script successfully run.",
                error_msg="Failed run script: " + "\n" + cmd,
            ).shell()

        except BaseException as e:
            RunnerLog(
                self.task,
                self.run_id,
                14,
                f"Failed to build run script.\n{self.env_path}\n{e}",
                1,
            )
            raise
