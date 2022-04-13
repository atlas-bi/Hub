"""Task source code handler."""


import re
import urllib.parse
from typing import Optional

import requests
import urllib3
from flask import current_app as app

from runner.extensions import db
from runner.model import Task
from runner.scripts.em_messages import RunnerException, RunnerLog
from runner.scripts.em_params import ParamLoader

urllib3.disable_warnings()  # type: ignore


class SourceCode:
    """Group of functions used to get various type of source code for task runner."""

    def __init__(
        self,
        task: Task,
        run_id: Optional[str],
        params: ParamLoader,
        refresh_cache: Optional[bool] = False,
    ) -> None:
        """Set up class parameters."""
        self.task = task
        self.run_id = run_id
        self.params = params
        self.db_type = (
            "mssql"
            if self.task.source_database_conn
            and self.task.source_database_conn.type_id == 2
            else None
        )

        self.query: str = ""
        self.refresh_cache = refresh_cache

    def gitlab(self, url: str) -> str:
        """Get source code from gitlab using authentication."""
        # pylint: disable=too-many-statements
        if ".git" in str(url):
            return ""

        if url:
            try:
                # convert the "raw" url into an api url
                branch = urllib.parse.quote(
                    urllib.parse.unquote(
                        re.findall(r"\/(?:raw|blob)\/(.+?)\/", url)[0]
                    ),
                    safe="",
                )

                project = urllib.parse.quote(
                    urllib.parse.unquote(
                        re.findall(r"\.(?:com|net|org)\/(.+?)\/-", url)[0]
                    ),
                    safe="",
                )

                file_path = urllib.parse.quote(
                    urllib.parse.unquote(
                        re.findall(r"\/(?:raw|blob)\/.+?\/(.+?)$", url)[0]
                    ),
                    safe="",
                )

                api_url = "%sapi/v4/projects/%s/repository/files/%s/raw?ref=%s" % (
                    app.config["GIT_URL"],
                    project,
                    file_path,
                    branch,
                )

                headers = {
                    "PRIVATE-TOKEN": app.config["GIT_TOKEN"],
                    "Connection": "close",
                }
                page = requests.get(
                    api_url, verify=app.config["GIT_VERIFY_SSL"], headers=headers
                )  # noqa: S501

                if page.status_code != 200:
                    raise Exception("Failed to get code: " + page.text)

                if url.lower().endswith(".sql"):
                    self.query = page.text
                    self.db_type = (
                        "mssql"
                        if self.task.source_database_conn
                        and self.task.source_database_conn.type_id == 2
                        else None
                    )

                    # save query cache before cleanup.
                    if self.run_id or self.refresh_cache:
                        self.task.source_cache = self.query
                        db.session.commit()

                        if self.refresh_cache:
                            RunnerLog(
                                self.task,
                                self.run_id,
                                15,
                                "Source cache manually refreshed.",
                            )

                    # insert params
                    return self.cleanup()

                return (
                    page.text
                    if not page.text.startswith("<!DOCTYPE")
                    else "Visit URL to view code"
                )

            # pylint: disable=broad-except
            except BaseException as e:
                # only use cache if we have a run id. Otherwise failures are from code preview.
                if (
                    self.run_id
                    and self.task.enable_source_cache == 1
                    and self.task.source_cache
                ):
                    RunnerLog(
                        self.task,
                        self.run_id,
                        15,
                        f"Failed to get source from {url}. Using cached query.\nFull trace:\n{e}",
                    )

                    self.db_type = (
                        "mssql"
                        if self.task.source_database_conn
                        and self.task.source_database_conn.type_id == 2
                        else None
                    )

                    self.query = self.task.source_cache
                    return self.cleanup()

                elif (
                    self.run_id
                    and self.task.enable_source_cache == 1
                    and not self.task.source_cache
                ):
                    raise RunnerException(
                        self.task,
                        self.run_id,
                        15,
                        f"Failed to get source from {url}. Cache enabled, but no cache available.\n{e}",
                    )
                else:
                    raise RunnerException(
                        self.task,
                        self.run_id,
                        15,
                        f"Failed to get source from {url}.\n{e}",
                    )

        raise RunnerException(
            self.task, self.run_id, 15, "No url specified to get source from."
        )

    def web_url(self, url: str) -> str:
        """Get contents of a webpage."""
        try:
            page = requests.get(
                str(url), verify=app.config["HTTP_VERIFY_SSL"]
            )  # noqa: S501
            self.query = page.text
            self.db_type = (
                "mssql"
                if self.task.source_database_conn
                and self.task.source_database_conn.type_id == 2
                else None
            )
            if page.status_code != 200:
                raise ValueError(f"{url} returned bad status: {page.status_code}")

            # save query cache before cleanup.
            if self.run_id or self.refresh_cache:
                self.task.source_cache = self.query
                db.session.commit()

                if self.refresh_cache:
                    RunnerLog(
                        self.task, self.run_id, 15, "Source cache manually refreshed."
                    )

            # insert params
            return self.cleanup()

        # pylint: disable=broad-except
        except BaseException as e:
            if (
                self.run_id
                and self.task.enable_source_cache == 1
                and self.task.source_cache
            ):
                RunnerLog(
                    self.task,
                    self.run_id,
                    15,
                    f"Failed to get source from {url}. Using cached query.\nFull trace:\n{e}",
                )

                self.db_type = (
                    "mssql"
                    if self.task.source_database_conn
                    and self.task.source_database_conn.type_id == 2
                    else None
                )

                self.query = self.task.source_cache

                return self.cleanup()

            elif (
                self.run_id
                and self.task.enable_source_cache == 1
                and not self.task.source_cache
            ):
                raise RunnerException(
                    self.task,
                    self.run_id,
                    15,
                    f"Failed to get source from {url}. Cache enabled, but no cache available.\n{e}",
                )
            else:
                raise RunnerException(
                    self.task, self.run_id, 15, f"Failed to get source from {url}\n{e}."
                )

    def source(self, query: Optional[str] = None) -> str:
        """Get task source code."""
        try:
            self.query = query or self.task.source_code or ""
            self.db_type = (
                "mssql"
                if self.task.source_database_conn
                and self.task.source_database_conn.type_id == 2
                else None
            )
            return self.cleanup()

        # pylint: disable=broad-except
        except BaseException as e:
            raise RunnerException(
                self.task, self.run_id, 15, f"Failed to clean source code.\n{e}."
            )

    def cleanup(self, query: Optional[str] = None) -> str:
        """Clean up source code.

        :param str query: query to clean
        :param str db_type: sql query language name
        :param list task_params: list of task level sql parameters to be injected
        :param list project_params: list of project level sql parameters to be injected

        :returns: Cleaned up query.
        """
        # remove database call
        # sql stuff
        query = query or self.query

        # only needed for mssql
        if self.task.source_type_id == 1 and self.db_type == "mssql":
            query = re.sub(
                re.compile(
                    r"(^;?\s*;?)\buse\b\s+.+", flags=re.IGNORECASE | re.MULTILINE
                ),
                "",
                query,
            )
            query = re.sub(
                re.compile(
                    r"(^;?\s*;?)\buse\b\s+.+?;", flags=re.IGNORECASE | re.MULTILINE
                ),
                "",
                query,
            )

            # add no count
            query = "SET NOCOUNT ON;\n" + query

            # disable warnings
            query = "SET ANSI_WARNINGS OFF;\n" + query

            query = "SET STATISTICS IO OFF;\n" + query
            query = "SET STATISTICS TIME OFF;\n" + query

            # remove " go"
            query = re.sub(
                re.compile(
                    r"^;?\s*?;?\bgo\b\s*?;?", flags=re.IGNORECASE | re.MULTILINE
                ),
                r"",
                query,
            )

        return self.params.insert_query_params(query)
