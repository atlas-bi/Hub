"""EM Param functions to load params and also populate params in a string."""

import re

from em_runner.scripts.em_date import DateParsing


class LoadParams:
    """Load task params.

    Params should be calculated before the task is run, so the same values are used
    throughout the run.

    If both project and task params retrun none, they will be rechecked at each use.
    """

    def __init__(self, task, job_hash=None):
        """Set up class."""
        self.task = task
        self.job_hash = job_hash
        self.task_params = self.task.query_params
        self.project_params = self.task.project.global_params

    def parse_params(self, params):
        """Parse project and task params."""
        # split into key value pairs
        if not params:
            return {}

        params = dict(
            re.split(r"\s?:\s?|\s?=\s?", param.strip())
            for param in params.splitlines()
            if param.strip() != ""
        )

        def insert_date(match):
            """Parse py dates."""
            return DateParsing(
                self.task, match.group(1), self.job_hash
            ).string_to_date()

        # parse python dates
        for key, value in params.items():
            params[key] = re.sub(r"parse\((.*?)\)", insert_date, value, re.IGNORECASE)

        return params

    def get(self):
        """Get current params."""
        return self.parse_params(self.project_params), self.parse_params(
            self.task_params
        )


class ParamParser:
    """Insert params to destination."""

    def __init__(
        self, task, query, job_hash=None, project_params=None, task_params=None
    ):
        """Set up class."""
        self.query = query
        self.task = task
        self.job_hash = job_hash

        if project_params is None and task_params is None:
            self.project_params, self.task_params = LoadParams(
                self.task, self.job_hash
            ).get()

        else:
            self.task_params = task_params
            self.project_params = project_params

    def insert_query_params(self):
        """Replace param place holders with value in queries."""

        def insert_code_params(query, params):
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

        query = self.query
        # add global parameters
        if self.project_params is not None:
            query = insert_code_params(query, self.project_params)

        if self.task_params is not None:
            query = insert_code_params(query, self.task_params)

        # add two blank lines on end of query
        return query + "\n\n"

    def insert_file_params(self):
        """Replace param place holders with value in filenames."""
        file_name = self.query

        def replace_param(file_name, params):
            """Replace all keys with value."""
            for key, value in params.items():
                file_name = file_name.replace(key, value)

            return file_name

        # add global parameters
        if self.project_params is not None:
            file_name = replace_param(file_name, self.project_params)

        if self.task_params is not None:
            file_name = replace_param(file_name, self.task_params)

        return file_name
