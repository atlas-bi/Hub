"""Task source code handler."""


import logging
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests
import urllib3
from flask import current_app as app

from runner import db
from runner.model import Task, TaskLog
from runner.scripts.em_params import LoadParams, ParamParser

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from error_print import full_stack

urllib3.disable_warnings()


class SourceCode:
    """Group of functions used to get various type of source code for task runner."""

    def __init__(
        self,
        task: Task,
        url: Optional[str],
        job_hash: Optional[str],
        query: str = None,
        project_params: Optional[Dict[Any, Any]] = None,
        task_params: Optional[Dict[Any, Any]] = None,
    ) -> None:
        """Set up class parameters.

        :param task: task object
        :param str url: web address of code source
        """
        self.url = url
        self.task = task
        self.job_hash = job_hash
        self.query = query
        self.db_type = (
            "mssql"
            if self.task.source_database_conn
            and self.task.source_database_conn.type_id == 2
            else None
        )

        if project_params is None and task_params is None:
            self.project_params, self.task_params = LoadParams(
                self.task, self.job_hash
            ).get()

        else:
            self.task_params = task_params or {}
            self.project_params = project_params or {}

    def gitlab(self) -> str:
        """Get source code from gitlab using authentication.

        :returns: String of source code if the url was valid.
        """
        # pylint: disable=too-many-statements
        if ".git" in str(self.url):
            return ""

        if self.url:
            try:
                # convert the "raw" url into an api url
                branch = urllib.parse.quote(
                    urllib.parse.unquote(
                        re.findall(r"\/(?:raw|blob)\/(.+?)\/", self.url)[0]
                    ),
                    safe="",
                )

                project = urllib.parse.quote(
                    urllib.parse.unquote(
                        re.findall(r"\.(?:com|net|org)\/(.+?)\/-", self.url)[0]
                    ),
                    safe="",
                )

                file_path = urllib.parse.quote(
                    urllib.parse.unquote(
                        re.findall(r"\/(?:raw|blob)\/.+?\/(.+?)$", self.url)[0]
                    ),
                    safe="",
                )

                api_url = "%sapi/v4/projects/%s/repository/files/%s/raw?ref=%s" % (
                    app.config["GIT_URL"],
                    project,
                    file_path,
                    branch,
                )

                headers = {"PRIVATE-TOKEN": app.config["GIT_TOKEN"]}
                page = requests.get(
                    api_url, verify=False, headers=headers
                )  # noqa: S501

                if page.status_code != 200:
                    raise Exception("Failed to get code: " + page.text)

                if self.url.lower().endswith(".sql"):
                    self.query = page.text
                    self.db_type = (
                        "mssql"
                        if self.task.source_database_conn
                        and self.task.source_database_conn.type_id == 2
                        else None
                    )
                    return self.cleanup()

                return (
                    page.text
                    if not page.text.startswith("<!DOCTYPE")
                    else "Visit URL to view code"
                )

            # pylint: disable=broad-except
            except BaseException as e:
                logging.error(
                    "Source: Failed Getting GitLab: %s\n%s", self.url, str(full_stack())
                )
                log = TaskLog(
                    task_id=self.task.id,
                    error=1,
                    job_id=self.job_hash,
                    status_id=15,
                    message="Failed to get source from "
                    + self.url
                    + "\n"
                    + str(full_stack()),
                )
                db.session.add(log)
                db.session.commit()

                raise e

        log = TaskLog(
            task_id=self.task.id,
            error=1,
            job_id=self.job_hash,
            status_id=15,
            message="(No Url?) Failed to get source from "
            + str(self.url)
            + "\n"
            + str(full_stack()),
        )
        db.session.add(log)
        db.session.commit()

        return ""

    def web_url(self) -> str:
        """Get contents of a webpage.

        :returns: Contents of webpage.
        """
        try:
            logging.info("Source: Getting Url: %s", self.url)
            page = requests.get(str(self.url), verify=False)  # noqa: S501
            self.query = page.text
            self.db_type = (
                "mssql"
                if self.task.source_database_conn
                and self.task.source_database_conn.type_id == 2
                else None
            )
            if page.status_code != 200:
                raise ValueError(f"{self.url} returned bad status: {page.status_code}")
            return self.cleanup()

        # pylint: disable=broad-except
        except BaseException as e:
            logging.error(
                "Source: Failed Getting GitLab: %s\n%s", self.url, str(full_stack())
            )
            log = TaskLog(
                task_id=self.task.id,
                error=1,
                job_id=self.job_hash,
                status_id=15,
                message="(No Url?) Failed to get source from "
                + str(self.url)
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

            raise e
        return -1

    def source(self) -> Union[str, int]:
        """Get task source code.

        :retruns: Cleaned source code.
        """
        try:
            self.query = self.task.source_code
            self.db_type = (
                "mssql"
                if self.task.source_database_conn
                and self.task.source_database_conn.type_id == 2
                else None
            )
            return self.cleanup()

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "Source: Failed cleaning source code. %s\n%s",
                None,
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                error=1,
                job_id=self.job_hash,
                status_id=15,
                message="Failed cleaning source code. " + "\n" + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
        return -1

    def cleanup(self) -> str:
        """Clean up source code.

        :param str query: query to clean
        :param str db_type: sql query language name
        :param list task_params: list of task level sql parameters to be injected
        :param list project_params: list of project level sql parameters to be injected

        :returns: Cleaned up query.
        """
        # remove database call
        # sql stuff
        query = str(self.query)

        query = re.sub(
            re.compile(r"(^;?\s*;?)\buse\b\s+.+", flags=re.IGNORECASE | re.MULTILINE),
            "",
            query,
        )
        query = re.sub(
            re.compile(r"(^;?\s*;?)\buse\b\s+.+?;", flags=re.IGNORECASE | re.MULTILINE),
            "",
            query,
        )

        # only needed for mssql
        if self.db_type == "mssql":

            # add no count
            query = "SET NOCOUNT ON;\n" + query

            # disable warnings
            query = "SET ANSI_WARNINGS OFF;\n" + query

            query = "SET STATISTICS IO OFF;\n" + query
            query = "SET STATISTICS TIME OFF;\n" + query

        # remove " go"
        query = re.sub(
            re.compile(r"^;?\s*?;?\bgo\b\s*?;?", flags=re.IGNORECASE | re.MULTILINE),
            r"",
            query,
        )

        query = ParamParser(self.task, query, self.job_hash).insert_query_params()

        # add two blank lines on end of query
        return query + "\n\n"
