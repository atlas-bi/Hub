"""
    script used to get source code

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

import logging
import re
import time
from bs4 import BeautifulSoup
import requests
import urllib3
from em import app, db
from ..model.model import TaskLog
from .error_print import full_stack

urllib3.disable_warnings()


class SourceCode:
    """ combination of methods to get code """

    def __init__(self, task, url):
        self.url = url
        self.task = task

    def gitlab(self):
        """ get source code from gitlab using auth """
        if self.url:
            try:
                logging.info("Source: Getting GitLab: %s", self.url)
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

                # try up to 10 times, with 5 second delays.
                count = 1

                page = session.get(self.url, verify=False)

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
                    page = session.get(self.url, verify=False)
                    if page.status_code == 200 and "Sign in · GitLab" not in page.text:
                        break

                assert "Sign in · GitLab" not in page.text

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

            # pylint: disable=bare-except
            except:
                logging.error(
                    "Source: Failed Getting GitLab: %s\n%s", self.url, str(full_stack())
                )
                log = TaskLog(
                    task_id=self.task.id,
                    error=1,
                    job_id=self.task.last_run_job_id,
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
            job_id=self.task.last_run_job_id,
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
        """ get contents of webpage """
        try:
            logging.info("Source: Getting Url: %s", self.url)
            page = requests.get(self.url, verify=False)
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

        # pylint: disable=bare-except
        except:
            logging.error(
                "Source: Failed Getting GitLab: %s\n%s", self.url, str(full_stack())
            )
            log = TaskLog(
                task_id=self.task.id,
                error=1,
                job_id=self.task.last_run_job_id,
                status_id=15,
                message="(No Url?) Failed to get source from "
                + self.url
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
        return -1

    @staticmethod
    def cleanup(query, my_type, task_params, project_params):
        """ used to clean code """
        # remove database call
        query = re.sub(r"use\s+.+", "", query, flags=re.IGNORECASE)
        query = re.sub(r"use\s+.+?;", "", query, flags=re.IGNORECASE)

        # only needed for mssql
        if my_type == "mssql":
            # add no count
            query = "SET NOCOUNT ON;\n" + query

            # disable warnings
            query = "SET ANSI_WARNINGS OFF;\n" + query

            query = "SET STATISTICS IO OFF;\n" + query
            query = "SET STATISTICS TIME OFF;\n" + query

        # remove html tags > should all be on one line
        query = re.sub(r"\<(.+?)\>", r"\1", query, flags=re.IGNORECASE)

        # add global parameters
        if project_params is not None:

            params = [
                re.split(r"\s?:\s?|\s?=\s?", x)
                for x in project_params.split("\n")
                if x != ""
            ]

            for x in params:
                query = re.sub(
                    r"(?<=SET\s" + x[0] + r")\s?=\s?.*;?",
                    " = " + x[1] + ";",
                    query,
                    flags=re.IGNORECASE,
                )
                query = re.sub(
                    r"(?<=Declare\s" + x[0] + r"\s)(.+?)\s?=\s?.*;?",
                    r"\1 = " + x[1] + ";",
                    query,
                    flags=re.IGNORECASE,
                )

        if task_params is not None:

            params = [
                re.split(":|=", x.replace(" ", ""))
                for x in task_params.split("\n")
                if x != ""
            ]

            for x in params:
                query = re.sub(
                    r"(?<=SET\s" + x[0] + r")\s?=\s?.*;?",
                    " = " + x[1] + ";",
                    query,
                    flags=re.IGNORECASE,
                )
                query = re.sub(
                    r"(?<=Declare\s" + x[0] + r"\s)(.+?)\s?=\s?.*;?",
                    r"\1 = " + x[1] + ";",
                    query,
                    flags=re.IGNORECASE,
                )

        return query
