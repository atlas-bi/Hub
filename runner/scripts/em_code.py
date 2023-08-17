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

import azure.devops.credentials as cd
from azure.devops.connection import Connection


urllib3.disable_warnings()  # type: ignore

class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

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

    def devops(self, url: str) -> str:
        """get source code from azure devops using authentication"""
        if url:
            try:
                token = app.config["DEVOPS_TOKEN"]
                creds = cd.BasicAuthentication('',token)
                connection = Connection(base_url=app.config["DEVOPS_URL"],creds=creds)
                # Get a client (the "core" client provides access to projects, teams, etc)
                core_client = connection.clients.get_core_client()

                get_projects_response = core_client.get_projects()

                git = connection.clients.get_git_client()


                #get the org, project and repository from the url
                orgName = re.findall(r"\.(?:com)\/(.+?)\/", url)
                project = re.findall(rf"\.(?:com\/{orgName[0]})\/(.+?)\/", url)
                repoName = re.findall(rf"\.(?:com\/{orgName[0]}\/{project[0]}\/_git)\/(.+?)\?", url)
                path = re.findall(r"(path[=])\/(.+?)(&|$)",url)
                branch = re.findall(r"(version[=]GB)(.+?)$",url)
                version = AttributeDict({'version':('main' if len(branch) == 0 else branch[0][1]), 'version_type':0,'version_options':0})  
                #need this to get the projects id
                projects = [i for i in get_projects_response if (i.name == project[0])]

                #this for repository id.
                repos = git.get_repositories([i for i in projects if (i.name == project[0])][0].id)
                repo_id = [i.id for i in repos if (i.name == repoName[0])][0]

                
                item = git.get_item_content(repository_id = repo_id,path=urllib.parse.unquote(path[0][1]), version_descriptor = version)
                text = ""
                for x in item:
                    text = text + x.decode('utf-8')
                if path[0][1].endswith(".sql"):
                    #\ufeff character shows up sometimes. Lets remove it.
                    self.query = text.replace(u'\ufeff','') 
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
                    text
                    if not text.startswith("<!DOCTYPE")
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
                    api_url,
                    verify=app.config["GIT_VERIFY_SSL"],
                    headers=headers,
                    timeout=60,
                )  # noqa: S501

                if page.status_code != 200:
                    # pylint: disable=W0719
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
        if ".git" in str(url):
            return ""
        try:
            page = requests.get(
                str(url), verify=app.config["HTTP_VERIFY_SSL"], timeout=60
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
