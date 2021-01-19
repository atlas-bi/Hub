"""Python script runner."""
# Extract Management 2.0
# Copyright (C) 2020  Riverside Healthcare, Kankakee, IL

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import logging
import re
import sys
from itertools import chain
from pathlib import Path

from em_runner import db
from em_runner.model import TaskLog
from em_runner.scripts.em_cmd import Cmd

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")

from error_print import full_stack


class PyProcesser:
    """Python Script Runner.

    Script will create a virtual environment, run a script or module, and then
    cleanup by removing all files.
    """

    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes

    def __init__(self, task, script, input_path, job_hash):
        """Set up class parameters.

        :param task: task object
        :param script: name of python function to run in environment
        :param input_path (optional):  pass filename as parameter to script
        """
        self.task = task
        self.job_hash = job_hash
        self.script = script
        self.input_path = input_path
        self.output = ""

        self.env_name = self.job_hash + "_env"
        self.job_path = (
            str(Path(__file__).parent.parent)
            + "/temp/"
            + self.task.project.name.replace(" ", "_")
            + "/"
            + self.task.name.replace(" ", "_")
            + "/"
            + self.job_hash
        )
        self.base_path = self.job_path + "/venv/"

        Path(self.base_path).mkdir(parents=True, exist_ok=True)

        self.env_path = self.base_path  # + self.env_name

    def run(self):
        """Run processing script.

        :returns: Any output from the script.
        """
        self.__build_env()
        self.__pip_install()
        self.__run_script()

        if self.output != "":
            return self.output
        return ""

    def __build_env(self):
        """Build a virtual environment.

        Runs command:
        .. code-block:: console

            virtualenv <path>

        """
        try:
            logging.info(
                "PyProcesser: Building Env: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )

            Cmd(
                self.task,
                "virtualenv " + self.env_path,
                "Environment  " + self.env_path + " created.",
                "Failed to create environment  " + self.env_path,
                self.job_hash,
            ).shell()

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "PyProcesser: Failed to build environment: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=14,  # py
                error=1,
                message="Failed to build environment. "
                + str(self.base_path)
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

    def __pip_install(self):
        r"""Get includes from script.

        get import (...)
        (?<=^import)\s+[^\.][^\s]+?\\s+?$

        get import (...) as ...
        (?<=^import)\s+[^\.][^\s]+?(?=\s)

        get from (...) imoprt (...)
        (?<=^from)\s+[^\.].+?(?=import)
        """
        try:
            logging.info(
                "PyProcesser: Pip Install: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )

            imports = []

            # find all scripts in dir, but not in venv
            paths = list(
                set(Path(self.job_path).rglob("*.py"))
                - set(Path(self.env_path).rglob("*.py"))
            )

            for this_file in paths:
                with open(this_file, "r") as my_file:
                    for line in my_file:

                        imports.append(
                            re.findall(r"(?<=^import)\s+[^\.][^\s]+?\s+?$", line)
                        )
                        imports.append(
                            re.findall(r"(?<=^from)\s+[^\.].+?(?=import)", line)
                        )
                        imports.append(
                            re.findall(r"(?<=^import)\s+[^\.][^\s]+?(?=\s)", line)
                        )

            # clean list
            imports = [x[0].strip().split(".")[0] for x in imports if x != []]

            # remove any relative imports
            names = [my_file.stem for my_file in paths]

            imports = list(set(imports) - set(names))

            # remove preinstalled packages from imports
            cmd = self.env_path + "bin/python -c \"help('modules')\""
            built_in_packages = Cmd(
                self.task,
                cmd,
                "Python packages loaded.",
                "Failed to get preloaded packages: " + "\n" + cmd,
                self.job_hash,
            ).shell()

            built_in_packages = built_in_packages.split(
                "Please wait a moment while I gather a list of all available modules..."
            )[1].split("Enter any module name to get more help.")[0]

            built_in_packages = [
                this_out.strip()
                for this_out in list(
                    chain.from_iterable(
                        [g.split(" ") for g in built_in_packages.split("\n") if g != ""]
                    )
                )
                if this_out != ""
            ]

            # remove default python packages from list
            imports = list(set(imports) - set(built_in_packages))

            # try to install
            if len(imports) > 0:
                cmd = (
                    self.env_path
                    + "bin/pip install --disable-pip-version-check --quiet "
                    + " ".join(imports)
                )
                Cmd(
                    self.task,
                    cmd,
                    "Imports succesfully installed: "
                    + ", ".join(imports)
                    + " with command: "
                    + "\n"
                    + cmd,
                    "Failed to install imports with command: " + "\n" + cmd,
                    self.job_hash,
                ).shell()

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "PyProcesser: Failed to install packages: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=14,  # py
                error=1,
                message="Failed to build install packages. "
                + str(self.base_path)
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

    def __run_script(self):
        try:
            logging.info(
                "PyProcesser: Running: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )
            cmd = (
                self.env_path
                + "bin/python "
                + self.script
                + (" " + self.input_path if self.input_path is not None else "")
            )

            self.output = Cmd(
                self.task,
                cmd,
                "Script successfully run.",
                "Failed run script: " + "\n" + cmd,
                self.job_hash,
            ).shell()
        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "PyProcesser: Failed to run script: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=14,  # py
                error=1,
                message="Failed to build run script. "
                + str(self.base_path)
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
