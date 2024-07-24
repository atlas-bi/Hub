"""Param functions to load params and also populate params in a string."""

import re
from typing import Any, Dict, Optional, Tuple, Union

from crypto import em_decrypt
from flask import current_app as app

from runner.model import ProjectParam, Task, TaskParam
from runner.scripts.em_date import DateParsing


class ParamLoader:
    """Load parameters and insert later on as needed."""

    def __init__(self, task: Task, run_id: Optional[str] = None) -> None:
        """Set up class."""
        self.task = task
        self.run_id = run_id
        self.project_params, self.task_params = self.__load()

    def __load(self) -> Tuple[Dict[Any, Any], Dict[Any, Any]]:
        """Get current params."""
        project_params = {}
        task_params = {}

        if self.task.project and self.task.project.params:
            project_params = self.__parse_params(self.task.project.params)

        if self.task.params:
            task_params = self.__parse_params(self.task.params)  # type: ignore

        return project_params, task_params

    def __parse_params(self, params: Union[TaskParam, ProjectParam]) -> dict:
        """Parse project and task params."""
        # split into key value pairs

        params_dict: Dict[Any, Any] = {}

        for param in params:
            params_dict[param.key] = em_decrypt(param.value, app.config["PASS_KEY"])

        def insert_date(match: re.Match) -> str:
            """Parse py dates."""
            return DateParsing(self.task, self.run_id, match.group(1)).string_to_date()

        # parse python dates
        for key, value in params_dict.items():
            params_dict[key] = re.sub(r"\bparse\((.*?)\)", insert_date, value, re.IGNORECASE)
        # sort by key length.. longest first to avoid replacing wrong values
        return dict(sorted(params_dict.items(), key=lambda x: len(x[0]), reverse=True))

    def insert_query_params(self, query: str) -> str:
        """Replace param place holders with value in queries."""

        def insert_code_params(query: str, params: dict) -> str:
            """Replace all keys with values in queries."""
            for key, value in params.items():
                query = re.sub(
                    r"(?<=SET\s" + key + r")\s?=\s?.*;?",
                    " = " + value + ";",
                    query,
                    flags=re.IGNORECASE,
                )
                query = re.sub(
                    r"(?<=Declare\s" + re.escape(key) + r"\s)(.+?)\s?=\s?.*;?",
                    r"\1 = " + value + ";",
                    query,
                    flags=re.IGNORECASE,
                )

            return query

        # add global parameters
        query = insert_code_params(query, self.project_params)
        query = insert_code_params(query, self.task_params)

        return query

    def insert_file_params(self, file_name: str) -> str:
        """Replace param place holders with value in filenames."""

        def replace_param(file_name: str, params: dict) -> str:
            """Replace all keys with value."""
            for key, value in params.items():
                file_name = file_name.replace(key, value)

            return file_name

        # add global parameters
        file_name = replace_param(file_name, self.project_params)
        file_name = replace_param(file_name, self.task_params)

        return file_name

    def read(self) -> dict:
        """Return a dict of consolidated params."""
        return {**self.project_params, **self.task_params}
