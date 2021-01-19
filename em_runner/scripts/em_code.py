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


import datetime
import logging
import pickle
import re
import sys
import time
from pathlib import Path

import requests
import urllib3
from bs4 import BeautifulSoup
from flask import current_app as app

from em_runner import db, redis_client
from em_runner.model import TaskLog

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")

from error_print import full_stack

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
                cookies = None

                # test inc
                session_count = redis_client.zincrby("gitlab_session_count", 1, "inc")

                # data must be loaded from redis one time, then used.
                # if it is loaded multiple times it will have changed
                # and what we throught to be true will no longer be
                # the case.

                # a session is used for login, and then once logged in
                # we only use the auth cookie.

                gitlab_session_date = redis_client.get("gitlab_session_date")

                session_date = (
                    pickle.loads(gitlab_session_date)
                    if gitlab_session_date
                    else datetime.datetime.now() - datetime.timedelta(days=1)
                )

                session_age = (datetime.datetime.now() - session_date).seconds

                if session_age <= 60 and redis_client.get("gitlab_session_cookie"):
                    logging.info(
                        "Found existing gitlab session. Age: %s, Users: %s",
                        str(session_age),
                        str(session_count),
                    )

                    gitlab_session_cookie = redis_client.get("gitlab_session_cookie")

                    cookies = (
                        pickle.loads(gitlab_session_cookie)
                        if gitlab_session_cookie
                        else None
                    )

                else:
                    # remove session if it is old
                    redis_client.delete("gitlab_session_count")
                    redis_client.delete("gitlab_session_date")
                    redis_client.delete("gitlab_session_cookie")

                # create new login if there is not existing login cookie.
                if cookies is None:
                    logging.info("Creating new gitlab session.")

                    session = requests.session()

                    # login
                    page = session.get(app.config["GIT_URL"], verify=False)
                    soup = BeautifulSoup(page.text, "html.parser")
                    page = session.post(
                        app.config["GIT_URL"] + "users/auth/ldapmain/callback",
                        data={
                            "authenticity_token": soup.find(
                                "input", {"name": "authenticity_token"}
                            ).get("value"),
                            "username": app.config["GIT_USERNAME"],
                            "password": app.config["GIT_PASSWORD"],
                        },
                        verify=False,
                    )
                    # save session after logging in
                    redis_client.set(
                        "gitlab_session_cookie", pickle.dumps(session.cookies)
                    )
                    cookies = session.cookies

                logging.info("Source: Getting GitLab: %s", self.url)

                # attempt to get page. notice we use "requests" not "session".
                # the login info is saved into the cookies, and we no longer
                # use sessions. Cookies can persist over several em_runner
                # instances, but a session cannot.
                page = requests.get(
                    self.url, verify=False, cookies=cookies
                )  # noqa: S501

                # if signin page is returned, try to log back in, only a few times.
                # gitlab limit the number of logins (even tho disabled in settings)
                # so it is possible we may have to wait a bit.
                count = 1
                while "Sign in · GitLab" in page.text and count <= 10:
                    logging.info(
                        "Attempting to login again (try %s) in 5 seconds. %s",
                        str(count),
                        self.url,
                    )
                    time.sleep(5)
                    session = requests.session()
                    page = session.get(app.config["GIT_URL"], verify=False)
                    soup = BeautifulSoup(page.text, "html.parser")
                    page = session.post(
                        app.config["GIT_URL"] + "users/auth/ldapmain/callback",
                        data={
                            "authenticity_token": soup.find(
                                "input", {"name": "authenticity_token"}
                            ).get("value"),
                            "username": app.config["GIT_USERNAME"],
                            "password": app.config["GIT_PASSWORD"],
                        },
                        verify=False,
                    )

                    # save session cookies after logging in
                    redis_client.set(
                        "gitlab_session_cookie", pickle.dumps(session.cookies)
                    )

                    page = requests.get(
                        self.url, verify=False, cookies=session.cookies  # noqa: S501
                    )

                    count += 1

                    if page.status_code == 200 and "Sign in · GitLab" not in page.text:
                        break

                if "Sign in · GitLab" in page.text:
                    raise Exception("Failed to login.")

                # decriment session counter
                session_count = redis_client.zincrby("gitlab_session_count", -1, "inc")

                # update session age.
                redis_client.set(
                    "gitlab_session_date", pickle.dumps(datetime.datetime.now())
                )

                # session is left behind in redis - if another new connection
                # comes up w/in the age limit we can still use it.

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

            # pylint: disable=broad-except
            except BaseException:
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
        except BaseException:
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
        query = re.sub(r"(^|\s)use\s+.+", "", query, flags=re.IGNORECASE)
        query = re.sub(r"(^|\s)use\s+.+?;", "", query, flags=re.IGNORECASE)

        # only needed for mssql
        if db_type == "mssql":
            # add no count
            query = "SET NOCOUNT ON;\n" + query

            # disable warnings
            query = "SET ANSI_WARNINGS OFF;\n" + query

            query = "SET STATISTICS IO OFF;\n" + query
            query = "SET STATISTICS TIME OFF;\n" + query

        # remove html tags > should all be on one line
        query = re.sub(r"\<(.+?)\>", r"\1", query, flags=re.IGNORECASE)

        # remove "go"
        query = re.sub(r"go", r"", query, flags=re.IGNORECASE)

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
                re.split(":|=", param.replace(" ", ""))
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

        return query
