"""

    Script is used to build a python eviron and run a script

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

from itertools import chain
from pathlib import Path
import logging
import re
from em import app, db
from .error_print import full_stack
from .cmd import Cmd
from ..model.model import (
    TaskLog,
    Task,
)


class PyProcesser:

    """
    create env
    run script in env
    remove env
    """

    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes

    def __init__(self, task, script, input_path):
        self.task = task
        self.script = script
        self.input_path = input_path
        self.output = ""

        self.env_name = self.task.last_run_job_id + "_env"
        self.job_path = (
            str(Path(__file__).parent.parent)
            + "/temp/"
            + self.task.project.name.replace(" ", "_")
            + "/"
            + self.task.name.replace(" ", "_")
            + "/"
            + self.task.last_run_job_id
        )
        self.base_path = self.job_path + "/venv/"

        Path(self.base_path).mkdir(parents=True, exist_ok=True)
        # Path("/home/venv/").mkdir(exist_ok=True)

        self.env_path = self.base_path  # + self.env_name
        if app.config["DEBUG"]:
            self.env_path = "/home/venv/" + self.env_name + "/"

    def run(self):
        """ run processing script """
        self.__build_env()
        self.__pip_install()
        self.__run_script()

        if self.output != "":
            return self.output
        return ""

    def __build_env(self):
        try:
            logging.info(
                "PyProcesser: Building Env: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )

            Cmd(
                self.task,
                "virtualenv " + self.env_path,
                "Environment  " + self.env_path + " created.",
                "Failed to create environment  " + self.env_path,
            ).shell()

        # pylint: disable=bare-except
        except:
            logging.error(
                "PyProcesser: Failed to build environment: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
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

        # get includes from script

        # get import (...)
        # (?<=^import)\s+[^\.][^\s]+?\s+?$

        # get import (...) as ...
        # (?<=^import)\s+[^\.][^\s]+?(?=\s)

        # get from (...) imoprt (...)
        # (?<=^from)\s+[^\.].+?(?=import)

        try:
            logging.info(
                "PyProcesser: Pip Install: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )

            imports = []

            # find all scripts in dir, but not in venv
            paths = list(
                set(Path(self.job_path).rglob("*.py"))
                - set(Path(self.env_path).rglob("*.py"))
            )

            for file in paths:
                for line in open(file):

                    imports.append(
                        re.findall(r"(?<=^import)\s+[^\.][^\s]+?\s+?$", line)
                    )
                    imports.append(re.findall(r"(?<=^from)\s+[^\.].+?(?=import)", line))
                    imports.append(
                        re.findall(r"(?<=^import)\s+[^\.][^\s]+?(?=\s)", line)
                    )

            # clean list
            imports = [x[0].strip() for x in imports if x != []]

            # remove any relative imports
            names = [file.stem for file in paths]

            imports = list(set(imports) - set(names))

            # remove preinstalled packages from imports
            cmd = self.env_path + "bin/python -c \"help('modules')\""
            x = Cmd(
                self.task,
                cmd,
                "Python packages loaded.",
                "Failed to get preloaded packages: " + "\n" + cmd,
            ).shell()

            x = x.split(
                "Please wait a moment while I gather a list of all available modules..."
            )[1].split("Enter any module name to get more help.")[0]

            x = [
                l.strip()
                for l in list(
                    chain.from_iterable(
                        [g.split(" ") for g in x.split("\n") if g != ""]
                    )
                )
                if l != ""
            ]

            # remove default python packages from list
            imports = list(set(imports) - set(x))

            # try to install
            if len(imports) > 0:
                cmd = self.env_path + "bin/pip install " + " ".join(imports)
                Cmd(
                    self.task,
                    cmd,
                    "Imports succesfully installed: "
                    + " ".join(imports)
                    + " with command: "
                    + "\n"
                    + cmd,
                    "Failed to install imports with command: " + "\n" + cmd,
                ).shell()

        # pylint: disable=bare-except
        except:
            logging.error(
                "PyProcesser: Failed to install packages: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
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
                str(self.task.last_run_job_id),
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
            ).shell()
        # pylint: disable=bare-except
        except:
            logging.error(
                "PyProcesser: Failed to run script: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=14,  # py
                error=1,
                message="Failed to build run script. "
                + str(self.base_path)
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
