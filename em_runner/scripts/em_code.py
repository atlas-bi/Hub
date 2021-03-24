"""Task source code handler."""
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
import urllib.parse
from pathlib import Path

import requests
import urllib3
from error_print import full_stack
from flask import current_app as app

from em_runner import db
from em_runner.model import TaskLog

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")


urllib3.disable_warnings()


class SourceCode:
    """Group of functions used to get various type of source code for task runner."""

    def __init__(self, task, url, job_hash):
        """Set up class parameters.

        :param task: task object
        :param str url: web address of code source
        """
        self.url = url
        self.task = task
        self.job_hash = job_hash

    def gitlab(self):
        """Get source code from gitlab using authentication.

        :returns: String of source code if the url was valid.
        """
        # pylint: disable=too-many-statements
        if ".git" in self.url:
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

                    return self.cleanup(
                        (
                            page.text
                            if not page.text.startswith("<!DOCTYPE")
                            else "Visit URL to view code"
                        ),
                        ("mssql" if self.task.source_database_id == 2 else None),
                        self.task.query_params,
                        self.task.project.global_params,
                    )

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
            + self.url
            + "\n"
            + str(full_stack()),
        )
        db.session.add(log)
        db.session.commit()

        return -1

    def web_url(self):
        """Get contents of a webpage.

        :returns: Contents of webpage.
        """
        try:
            logging.info("Source: Getting Url: %s", self.url)
            page = requests.get(self.url, verify=False)  # noqa: S501
            return (
                self.cleanup(
                    page.text,
                    ("mssql" if self.task.source_database_id == 2 else None),
                    self.task.query_params,
                    self.task.project.global_params,
                )
                if page.status_code == 200
                else -1
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
                message="(No Url?) Failed to get source from "
                + self.url
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

            raise e
        return -1

    def source(self):
        """Get task source code.

        :retruns: Cleaned source code.
        """
        try:
            return self.cleanup(
                query=self.task.source_code,
                db_type=("mssql" if self.task.source_database_id == 2 else None),
                task_params=self.task.query_params,
                project_params=self.task.project.global_params,
            )

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

    @staticmethod
    def cleanup(query, db_type, task_params, project_params):
        """Clean up source code.

        :param str query: query to clean
        :param str db_type: sql query language name
        :param list task_params: list of task level sql parameters to be injected
        :param list project_params: list of project level sql parameters to be injected

        :returns: Cleaned up query.
        """
        # remove database call
        # sql stuff

        query = re.sub(
            r"(^;?\s*;?)use\s+.+", "", query, flags=re.IGNORECASE | re.MULTILINE
        )
        query = re.sub(
            r"(^;?\s*;?)use\s+.+?;", "", query, flags=re.IGNORECASE | re.MULTILINE
        )

        # only needed for mssql
        if db_type == "mssql":
            # add no count
            query = "SET NOCOUNT ON;\n" + query

            # disable warnings
            query = "SET ANSI_WARNINGS OFF;\n" + query

            query = "SET STATISTICS IO OFF;\n" + query
            query = "SET STATISTICS TIME OFF;\n" + query

        # remove " go"
        query = re.sub(r" go", r"", query, flags=re.IGNORECASE)

        # add global parameters
        if project_params is not None:

            params = [
                re.split(r"\s?:\s?|\s?=\s?", param)
                for param in project_params.split("\n")
                if param != ""
            ]

            for param in params:
                query = re.sub(
                    r"(?<=SET\s" + param[0] + r")\s?=\s?.*;?",
                    " = " + param[1] + ";",
                    query,
                    flags=re.IGNORECASE,
                )
                query = re.sub(
                    r"(?<=Declare\s" + param[0] + r"\s)(.+?)\s?=\s?.*;?",
                    r"\1 = " + param[1] + ";",
                    query,
                    flags=re.IGNORECASE,
                )

        if task_params is not None:
            params = [
                re.split(r"(?:\s*:\s*|\s*=\s*)", param)
                for param in task_params.split("\n")
                if param != ""
            ]

            for param in params:
                query = re.sub(
                    r"(?<=SET\s" + param[0] + r")\s?=\s?.*;?",
                    " = " + param[1] + ";",
                    query,
                    flags=re.IGNORECASE,
                )
                query = re.sub(
                    r"(?<=Declare\s" + param[0] + r"\s)(.+?)\s?=\s?.*;?",
                    r"\1 = " + param[1] + ";",
                    query,
                    flags=re.IGNORECASE,
                )

        # add two blank lines on end of query
        return query + "\n\n"
