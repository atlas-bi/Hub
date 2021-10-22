"""Task runner."""

import csv
import datetime
import hashlib
import logging
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path
from typing import Optional, Union

import requests
from flask import current_app as app
from jinja2 import Environment, PackageLoader, select_autoescape

from runner import db, redis_client
from runner.model import Task, TaskFile, TaskLog
from runner.scripts.em_cmd import Cmd
from runner.scripts.em_code import SourceCode
from runner.scripts.em_date import DateParsing
from runner.scripts.em_file import File, file_size
from runner.scripts.em_ftp import Ftp
from runner.scripts.em_params import LoadParams
from runner.scripts.em_postgres import Postgres
from runner.scripts.em_python import PyProcesser
from runner.scripts.em_sftp import Sftp
from runner.scripts.em_smb import Smb
from runner.scripts.em_smtp import Smtp
from runner.scripts.em_sqlserver import SqlServer
from runner.scripts.em_ssh import Ssh
from runner.scripts.em_system import Monitor
from runner.web.filters import datetime_format

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from crypto import em_decrypt
from error_print import full_stack

env = Environment(
    loader=PackageLoader("runner", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


env.filters["datetime_format"] = datetime_format


# set the limit for a csv cell value to something massive.
# this is needed when users are building xml in a sql query
# and have one very large column.

MAX_INT = sys.maxsize

while True:
    # decrease the MAX_INT value by factor 10
    # as long as the OverflowError occurs.

    try:
        csv.field_size_limit(MAX_INT)
        break
    except OverflowError:
        MAX_INT = int(MAX_INT / 10)


class Runner:
    """Group of functions used to run a task."""

    # pylint: disable=too-few-public-methods

    def __init__(self, task_id: int) -> None:
        """Set up class parameters.

        On sequence jobs, only the first enabled job in the
        sequence should be in the scheduler.
        """
        # Create id for the run instance and assign to tasks being run.
        my_hash = hashlib.sha256()
        my_hash.update(str(time.time() * 1000).encode("utf-8"))
        self.job_hash = my_hash.hexdigest()[:10]
        tasks = Task.query.filter_by(id=task_id).all()

        for task in tasks:
            self.error = 0
            self.data_file: Optional[str] = None
            self.file_path = ""
            self.file_name = ""
            self.file_hash = ""
            print("starting task " + str(task.id))  # noqa: T001
            logging.info(
                "Runner: Starting task: %s, with run: %s",
                str(task.id),
                str(my_hash.hexdigest()[:10]),
            )

            # set status to running
            task.status_id = 1
            task.last_run_job_id = my_hash.hexdigest()[:10]
            task.last_run = datetime.datetime.now()
            db.session.commit()

            log = TaskLog(
                task_id=task.id,
                job_id=self.job_hash,
                status_id=8,
                message="Starting task.",
            )
            db.session.add(log)
            db.session.commit()

            self.task = task

            # If monitor fails then cancel task.
            if Monitor(self.task, self.job_hash).check_all():

                # set task status to errored.
                task.status_id = 2
                task.last_run = datetime.datetime.now()
                db.session.commit()

                # log a cancellation message from the runner.
                log = TaskLog(
                    task_id=task.id,
                    job_id=self.job_hash,
                    status_id=8,
                    error=1,
                    message="Task cancelled.",
                )
                db.session.add(log)
                db.session.commit()

                continue

            self.temp_path = "%s/temp/%s/%s/%s/" % (
                str(Path(__file__).parent.parent),
                self.task.project.name.replace(" ", "_"),
                self.task.name.replace(" ", "_"),
                self.job_hash,
            )

            log = TaskLog(
                task_id=task.id,
                job_id=self.job_hash,
                status_id=8,
                message="Loading parameters.",
            )

            db.session.add(log)
            db.session.commit()

            self.project_params, self.task_params = LoadParams(
                self.task, self.job_hash
            ).get()

            log = TaskLog(
                task_id=task.id,
                job_id=self.job_hash,
                status_id=8,
                message="Parameters loaded.",
            )
            db.session.add(log)
            db.session.commit()

            # load file/ run query/ etc to get some sort of data or process something.
            if self.error == 0:
                log = TaskLog(
                    task_id=task.id,
                    job_id=self.job_hash,
                    status_id=8,
                    message="Loading source.",
                )
                db.session.add(log)
                db.session.commit()

                self.__get_source()

                log = TaskLog(
                    task_id=task.id,
                    job_id=self.job_hash,
                    status_id=8,
                    message="Source loaded.",
                )
                db.session.add(log)
                db.session.commit()

            # builds the resulting data into a file
            if self.error == 0:
                log = TaskLog(
                    task_id=task.id,
                    job_id=self.job_hash,
                    status_id=8,
                    message="Building output.",
                )
                db.session.add(log)
                db.session.commit()

                self.__build_file()

                log = TaskLog(
                    task_id=task.id,
                    job_id=self.job_hash,
                    status_id=8,
                    message="Output built.",
                )
                db.session.add(log)
                db.session.commit()

            # any data post-processing
            if self.error == 0 and self.task.processing_type_id is not None:
                log = TaskLog(
                    task_id=task.id,
                    job_id=self.job_hash,
                    status_id=8,
                    message="Starting processing script.",
                )
                db.session.add(log)
                db.session.commit()

                self.__process()

                log = TaskLog(
                    task_id=task.id,
                    job_id=self.job_hash,
                    status_id=8,
                    message="Processing script complete.",
                )
                db.session.add(log)
                db.session.commit()

            # permanent storage of the file for historical purposes
            if self.error == 0:
                log = TaskLog(
                    task_id=task.id,
                    job_id=self.job_hash,
                    status_id=8,
                    message="Storing file.",
                )
                db.session.add(log)
                db.session.commit()

                self.__store_file()

                log = TaskLog(
                    task_id=task.id,
                    job_id=self.job_hash,
                    status_id=8,
                    message="Finished storing file.",
                )
                db.session.add(log)
                db.session.commit()

            # send confirmation/error emails
            self.__send_email()

            # any cleanup process. remove file from local storage
            self.__clean_up()

            log = TaskLog(
                task_id=task.id,
                job_id=self.job_hash,
                status_id=8,
                error=(0 if self.error == 0 else 1),
                message=("Completed task." if self.error == 0 else "Task canceled."),
            )
            db.session.add(log)
            db.session.commit()

            # set status to completed if no error logs
            error_logs = (
                TaskLog.query.filter_by(
                    task_id=self.task.id, job_id=self.job_hash, error=1
                )
                .order_by(TaskLog.status_date)
                .all()
            )

            if len(error_logs) > 0 or self.error != 0:
                # increment attempt counter
                redis_client.zincrby("runner_" + str(task_id) + "_attempt", 1, "inc")
                task.status_id = 2

                # if task ended with a non-catastrophic error, it is possible that we can rerun it.
                if (
                    redis_client.zincrby(
                        "runner_" + str(task_id) + "_attempt", 0, "inc"
                    )
                    or 1
                ) <= (task.max_retries or 0):
                    # schedule a rerun in 5 minutes.
                    log = TaskLog(
                        task_id=task.id,
                        job_id=self.job_hash,
                        status_id=8,
                        message=(
                            "Scheduling re-attempt %d of %d."
                            % (
                                redis_client.zincrby(
                                    "runner_" + str(task_id) + "_attempt", 0, "inc"
                                ),
                                task.max_retries,
                            )
                        ),
                    )
                    db.session.add(log)
                    db.session.commit()

                    requests.get(
                        "%s/run/%s/delay/5" % (app.config["SCHEDULER_HOST"], task_id)
                    )
                else:
                    redis_client.delete("runner_" + str(task_id) + "_attempt")

                    # if the project runs in series, mark all following enabled tasks as errored
                    if task.project.sequence_tasks == 1:
                        task_id_list = [
                            x.id
                            for x in Task.query.filter_by(enabled=1)
                            .filter_by(project_id=task.project_id)
                            .order_by(Task.order.asc(), Task.name.asc())  # type: ignore[union-attr]
                            .all()
                        ]
                        for this_id in task_id_list[
                            task_id_list.index(int(task_id)) + 1 :
                        ]:
                            Task.query.filter_by(id=this_id).update({"status_id": 2})

            else:
                # remove any retry tracking
                redis_client.delete("runner_" + str(task_id) + "_attempt")
                task.status_id = 4
                task.est_duration = (
                    datetime.datetime.now() - task.last_run
                ).total_seconds()

                # if this is a sequence job, trigger the next job.
                if task.project.sequence_tasks == 1:
                    task_id_list = [
                        x.id
                        for x in Task.query.filter_by(enabled=1)
                        .filter_by(project_id=task.project_id)
                        .order_by(Task.order.asc(), Task.name.asc())  # type: ignore[union-attr]
                        .all()
                    ]
                    # potentially the task was disabled while running
                    # and removed from list. when that happens we should
                    # quit.
                    if task.id in task_id_list:
                        next_task_id = task_id_list[
                            task_id_list.index(task.id)
                            + 1 : task_id_list.index(task.id)
                            + 2
                        ]
                        if next_task_id:
                            # trigger next task
                            log = TaskLog(
                                task_id=task.id,
                                job_id=self.job_hash,
                                status_id=8,
                                message=(
                                    f"Triggering run of next sequence job: {next_task_id}"
                                ),
                            )
                            db.session.add(log)
                            db.session.commit()

                            log = TaskLog(
                                task_id=next_task_id[0],
                                status_id=8,
                                message=(
                                    f"Run triggered by previous sequence job:: {task.id}"
                                ),
                            )
                            db.session.add(log)
                            db.session.commit()

                            requests.get(
                                app.config["RUNNER_HOST"] + "/" + str(next_task_id[0])
                            )
                        else:
                            log = TaskLog(
                                task_id=task.id,
                                job_id=self.job_hash,
                                status_id=8,
                                message=("Sequence completed!"),
                            )
                            db.session.add(log)
                            db.session.commit()

            task.last_run_job_id = None
            task.last_run = datetime.datetime.now()
            db.session.commit()

    # pylint: disable=inconsistent-return-statements
    def __process(self) -> bool:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        logging.info(
            "Runner: Processing: Task: %s, with run: %s",
            str(self.task.id),
            str(self.job_hash),
        )
        # get processing script

        # 1 = smb
        # 2 = sftp
        # 3 = ftp
        # 4 = git url
        # 5 = other url
        # 6 = source code

        processing_script_name = self.temp_path + self.job_hash + ".py"

        my_file = ""
        if (
            self.task.processing_type_id == 1
            and self.task.processing_smb_id is not None
        ):
            file_name = DateParsing(
                self.task, self.task.source_smb_file, self.job_hash
            ).string_to_date()

            try:
                my_file = Path(
                    Smb(
                        task=self.task,
                        connection=self.task.processing_smb_conn,
                        file_path=file_name,
                        job_hash=self.job_hash,
                        overwrite=0,
                        file_name=None,
                    ).read()
                ).read_text("utf8")
            # pylint: disable=broad-except
            except BaseException:
                self.error += 1
                return False

        elif (
            self.task.processing_type_id == 2
            and self.task.processing_sftp_id is not None
        ):
            file_name = DateParsing(
                self.task, self.task.processing_sftp_file, self.job_hash
            ).string_to_date()

            try:
                my_file = Sftp(
                    task=self.task,
                    connection=self.task.processing_sftp_conn,
                    overwrite=0,
                    file_name=file_name,
                    file_path=None,
                    job_hash=self.job_hash,
                ).read()
            # pylint: disable=broad-except
            except BaseException:
                self.error += 1
                return False

        elif (
            self.task.processing_type_id == 3
            and self.task.processing_ftp_id is not None
        ):
            file_name = DateParsing(
                task=self.task,
                date_string=self.task.processing_ftp_file,
                job_hash=self.job_hash,
            ).string_to_date()

            try:
                my_file = Ftp(
                    task=self.task,
                    connection=self.task.processing_ftp_conn,
                    overwrite=0,
                    file_name=file_name,
                    file_path=None,
                    job_hash=self.job_hash,
                ).read()
            # pylint: disable=broad-except
            except BaseException:
                self.error += 1
                return False

        elif self.task.processing_type_id == 4 and self.task.processing_git is not None:

            # if a dir is specified then download all files
            if (
                self.task.processing_command is not None
                and self.task.processing_command != ""
            ):
                try:
                    url = (
                        re.sub(
                            r"(https?://)(.+?)",
                            r"\1<username>:<password>@\2",
                            self.task.processing_git,
                            flags=re.IGNORECASE,
                        )
                        .replace(
                            "<username>", urllib.parse.quote(app.config["GIT_USERNAME"])
                        )
                        .replace(
                            "<password>", urllib.parse.quote(app.config["GIT_PASSWORD"])
                        )
                    )

                    cmd = (
                        "$(which git) clone -q --depth 1 "
                        + "--recurse-submodules --shallow-submodules %s %s"
                        % (url, self.temp_path)
                    )

                    output = Cmd(
                        self.task,
                        cmd,
                        "Repo cloned.",
                        "Failed to clone repo: %s" % (self.task.processing_git,),
                        self.job_hash,
                    ).shell()

                    processing_script_name = self.temp_path + (
                        self.task.processing_command
                        if self.task.processing_command is not None
                        else ""
                    )
                # pylint: disable=broad-except
                except BaseException:
                    logging.error(
                        "Runner: Processor failed to clone repo: Task: %s, with run: %s\n%s",
                        str(self.task.id),
                        str(self.job_hash),
                        str(full_stack()),
                    )
                    log = TaskLog(
                        task_id=self.task.id,
                        error=1,
                        job_id=self.job_hash,
                        status_id=8,
                        message="Processor failed to clone repo:\n%s"
                        % (str(full_stack()),),
                    )
                    db.session.add(log)
                    db.session.commit()

            # otherwise get py file
            else:
                try:
                    my_file = SourceCode(
                        task=self.task,
                        url=self.task.processing_git,
                        job_hash=self.job_hash,
                        project_params=self.project_params,
                        task_params=self.task_params,
                    ).gitlab()
                # pylint: disable=broad-except
                except BaseException:
                    self.error += 1
                    return False

        elif self.task.processing_type_id == 5 and self.task.processing_url is not None:
            if self.task.processing_command is not None:
                try:

                    cmd = (
                        "$(which git) clone -q --depth 1 "
                        + "--recurse-submodules --shallow-submodules %s %s"
                        % (self.task.processing_url, self.temp_path)
                    )

                    output = Cmd(
                        task=self.task,
                        cmd=cmd,
                        success_msg="Repo cloned",
                        error_msg="Failed to clone repo: %s"
                        % (self.task.processing_url,),
                        job_hash=self.job_hash,
                    ).shell()

                    processing_script_name = self.temp_path + (
                        self.task.processing_command
                        if self.task.processing_command is not None
                        else ""
                    )
                # pylint: disable=broad-except
                except BaseException:
                    logging.error(
                        "Runner: Processor failed to clone repo: Task: %s, with run: %s\n%s",
                        str(self.task.id),
                        str(self.job_hash),
                        str(full_stack()),
                    )
                    log = TaskLog(
                        task_id=self.task.id,
                        error=1,
                        job_id=self.job_hash,
                        status_id=8,
                        message="Processor failed to clone repo:\n%s"
                        % (str(full_stack()),),
                    )
                    db.session.add(log)
                    db.session.commit()
            else:
                try:
                    my_file = SourceCode(
                        task=self.task,
                        url=self.task.processing_url,
                        job_hash=self.job_hash,
                        task_params=self.task_params,
                        project_params=self.project_params,
                    ).web_url()
                # pylint: disable=broad-except
                except BaseException:
                    self.error += 1
                    return False
        elif (
            self.task.processing_type_id == 6 and self.task.processing_code is not None
        ):
            my_file = self.task.processing_code
        elif self.task.processing_type_id > 0:
            log = TaskLog(
                task_id=self.task.id,
                error=1,
                job_id=self.job_hash,
                status_id=8,
                message="Not enough information to run a processing script from %s"
                % (self.task.processing_type.name,),
            )
            db.session.add(log)
            db.session.commit()

        try:
            if my_file != "" and self.task.processing_type_id > 0:
                Path(processing_script_name).parent.mkdir(parents=True, exist_ok=True)
                with open(processing_script_name, "w") as text_file:
                    text_file.write(my_file)
                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.job_hash,
                    status_id=8,
                    message="Processing script created.",
                )
                db.session.add(log)
                db.session.commit()

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "Runner: Failed Processing: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                error=1,
                job_id=self.job_hash,
                status_id=8,
                message="Processing script failure:\n%s" % (str(full_stack()),),
            )
            db.session.add(log)
            db.session.commit()

        # run processing script
        output = PyProcesser(
            task=self.task,
            script=processing_script_name,
            input_path=self.file_path,
            job_hash=self.job_hash,
        ).run()

        # allow processer to rename file
        if output and output != "":
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=8,
                message="Processing script output:\n%s" % (output,),
            )
            db.session.add(log)
            db.session.commit()
            self.file_name = output
        return True

    # pylint: disable=R1710
    def __get_source(self) -> Union[bool, str]:
        try:
            logging.info(
                "Runner: Getting Source: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )

            # pylint: disable=no-else-return
            if self.task.source_type_id == 1:  # sql
                external_db = self.task.source_database_conn

                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.job_hash,
                    status_id=8,
                    message="Loading query.",
                )
                db.session.add(log)
                db.session.commit()

                query = self.__get_query() or "error"
                if query == "error":
                    self.error += 1
                    return query

                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.job_hash,
                    status_id=8,
                    message="Starting to run sql query, waiting for results.",
                )
                db.session.add(log)
                db.session.commit()

                if external_db.database_type.id == 1:  # postgres
                    self.data_file = Postgres(
                        task=self.task,
                        query=query,
                        connection=em_decrypt(
                            external_db.connection_string, app.config["PASS_KEY"]
                        ),
                        job_hash=self.job_hash,
                    ).run()

                    if not self.data_file:
                        self.error += 1
                        return False

                    return True

                elif external_db.database_type.id == 2:  # mssql

                    self.data_file = SqlServer(
                        task=self.task,
                        query=query,
                        connection=em_decrypt(
                            external_db.connection_string, app.config["PASS_KEY"]
                        ),
                        job_hash=self.job_hash,
                    ).run()

                    if not self.data_file:
                        self.error += 1
                        return False

                    return True

            elif self.task.source_type_id == 2:  # smb file

                file_name = DateParsing(
                    self.task, self.task.source_smb_file, self.job_hash
                ).string_to_date()

                my_file = Path(
                    Smb(
                        task=self.task,
                        connection=self.task.source_smb_conn,
                        overwrite=0,
                        file_name=file_name,
                        file_path=file_name,
                        job_hash=self.job_hash,
                    ).read()
                ).read_text("utf8")

                if self.task.source_smb_ignore_delimiter == 1:
                    my_delimiter = None

                    self.data_file = my_file

                else:

                    my_delimiter = (
                        self.task.source_smb_delimiter
                        if self.task.source_smb_delimiter != ""
                        and self.task.source_smb_delimiter is not None
                        else ","
                    )

                    csv_reader = csv.reader(
                        my_file.splitlines(),
                        delimiter=my_delimiter,
                    )

                    # dump back into a temp file
                    with tempfile.NamedTemporaryFile(
                        mode="w+", newline="", delete=False
                    ) as data_file:
                        writer = csv.writer(data_file)
                        writer.writerows(csv_reader)

                    self.data_file = data_file.name

                return True

            elif self.task.source_type_id == 3:  # sftp file

                file_name = DateParsing(
                    task=self.task,
                    date_string=self.task.source_sftp_file,
                    job_hash=self.job_hash,
                ).string_to_date()

                try:
                    my_file = Sftp(
                        task=self.task,
                        connection=self.task.source_sftp_conn,
                        overwrite=0,
                        file_name=file_name,
                        file_path=None,
                        job_hash=self.job_hash,
                    ).read()

                # pylint: disable=broad-except
                except BaseException:
                    self.error += 1
                    return False

                self.data_file = my_file

                return True

            elif self.task.source_type_id == 4:  # ftp file

                file_name = DateParsing(
                    task=self.task,
                    date_string=self.task.source_ftp_file,
                    job_hash=self.job_hash,
                ).string_to_date()

                my_file = Ftp(
                    task=self.task,
                    connection=self.task.source_ftp_conn,
                    overwrite=0,
                    file_name=file_name,
                    file_path=None,
                    job_hash=self.job_hash,
                ).read()

                if self.task.source_ftp_ignore_delimiter == 1:
                    my_delimiter = None

                    self.data_file = my_file

                else:

                    my_delimiter = (
                        self.task.source_ftp_delimiter
                        if self.task.source_ftp_delimiter != ""
                        and self.task.source_ftp_delimiter is not None
                        else ","
                    )

                    csv_reader = csv.reader(
                        my_file.splitlines(),
                        delimiter=my_delimiter,
                    )

                    # dump back into a temp file
                    with tempfile.NamedTemporaryFile(
                        mode="w+", newline="", delete=False
                    ) as data_file:
                        writer = csv.writer(data_file)
                        writer.writerows(csv_reader)

                    self.data_file = data_file.name

                return True
            elif self.task.source_type_id == 6:  # ssh command
                query = self.__get_query() or "error"
                if query == "error":
                    self.error += 1
                    return query

                my_file = Ssh(
                    task=self.task,
                    connection=self.task.source_ssh_conn,
                    command=query,
                    job_hash=self.job_hash,
                ).run()

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "Runner: Failed Getting Source: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                error=1,
                job_id=self.job_hash,
                status_id=8,
                message="Failed to get data source.\n" + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
            self.data_file = None

            self.error += 1

            return False
        return True

    def __get_query(self) -> str:
        query = "error"
        if self.task.source_query_type_id == 3:  # url
            try:
                query = SourceCode(
                    task=self.task,
                    url=self.task.source_url,
                    job_hash=self.job_hash,
                    project_params=self.project_params,
                    task_params=self.task_params,
                ).web_url()
            # pylint: disable=broad-except
            except BaseException:
                self.error += 1
                return ""

        elif self.task.source_query_type_id == 1:  # gitlab url
            try:
                query = SourceCode(
                    task=self.task,
                    url=self.task.source_git,
                    job_hash=self.job_hash,
                    project_params=self.project_params,
                    task_params=self.task_params,
                ).gitlab()
            # pylint: disable=broad-except
            except BaseException:
                self.error += 1
                return ""

        elif self.task.source_query_type_id == 4:  # code
            query = SourceCode(
                task=self.task,
                url=None,
                job_hash=self.job_hash,
                query=self.task.source_code,
                project_params=self.project_params,
                task_params=self.task_params,
            ).cleanup()

        elif self.task.source_query_type_id == 2:
            query = SourceCode(
                task=self.task,
                url=None,
                job_hash=self.job_hash,
                query=(
                    Path(
                        Smb(
                            task=self.task,
                            file_path=self.task.source_query_file,
                            connection=self.task.query_source,
                            overwrite=0,
                            file_name=None,
                            job_hash=self.job_hash,
                        ).read()
                    ).read_text("utf8")
                ),
                project_params=self.project_params,
                task_params=self.task_params,
            ).cleanup()

        return query

    def __build_file(self) -> None:
        """File will be built locally then dumped onto a file server.

        Webserver is not used for long-term storage.

        files are kept in /em/runner/temp/<extract name>

        """
        if self.data_file:
            logging.info(
                "Runner: Building File: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )

            self.file_name, self.file_path, self.file_hash = File(
                task=self.task, data_file=self.data_file, job_hash=self.job_hash
            ).save()

            # remove data file
            os.remove(self.data_file)

    def __store_file(self) -> bool:
        if self.task.source_type_id in [5, 6]:
            return False
        # only store if there are no errors.
        error_logs = (
            TaskLog.query.filter_by(task_id=self.task.id, job_id=self.job_hash, error=1)
            .order_by(TaskLog.status_date)
            .all()
        )

        if len(error_logs) > 0 and self.file_name != "" and self.file_path != "":
            logging.error(
                "Runner: Files not stored because of run error: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                error=1,
                job_id=self.job_hash,
                status_id=8,
                message="Files not stored because of run error.",
            )
            db.session.add(log)
            db.session.commit()

            self.error += 1

            return False

        logging.info(
            "Runner: Storing file: Task: %s, with run: %s",
            str(self.task.id),
            str(self.job_hash),
        )

        # send to sftp
        if self.task.destination_sftp == 1 and self.task.destination_sftp_conn:

            Sftp(
                task=self.task,
                connection=self.task.destination_sftp_conn,
                overwrite=self.task.destination_sftp_overwrite,
                file_name=self.file_name,
                file_path=self.file_path,
                job_hash=self.job_hash,
            ).save()

        # send to ftp
        if self.task.destination_ftp == 1 and self.task.destination_ftp_conn:
            Ftp(
                task=self.task,
                connection=self.task.destination_ftp_conn,
                overwrite=self.task.destination_ftp_overwrite,
                file_name=self.file_name,
                file_path=self.file_path,
                job_hash=self.job_hash,
            ).save()

        # save to smb
        if self.task.destination_smb == 1 and self.task.destination_smb_conn:
            Smb(
                task=self.task,
                connection=self.task.destination_smb_conn,
                overwrite=self.task.destination_smb_overwrite,
                file_name=self.file_name,
                file_path=self.file_path,
                job_hash=self.job_hash,
            ).save()

        # save historical copy
        smb_path = Smb(
            task=self.task,
            connection=None,  # "default",
            overwrite=self.task.destination_smb_overwrite,
            file_name=self.file_name,
            file_path=self.file_path,
            job_hash=self.job_hash,
        ).save()

        # log file details
        db.session.add(
            TaskFile(
                name=self.file_name,
                path=smb_path,
                task_id=self.task.id,
                job_id=self.job_hash,
                file_hash=self.file_hash,
                size=file_size(str(os.path.getsize(self.file_path))),
            )
        )
        db.session.commit()

        return True

    def __clean_up(self) -> None:

        # remove file
        try:
            if Path(self.temp_path).exists():
                shutil.rmtree(self.temp_path)

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "Runner: Failed cleanup: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                error=1,
                job_id=self.job_hash,
                status_id=8,
                message="Failed to clean up job.\n%s" % (str(full_stack()),),
            )
            db.session.add(log)
            db.session.commit()
            self.data_file = None

    def __send_email(self) -> Union[bool, None]:
        logging.info(
            "Runner: Sending Mail: Task: %s, with run: %s",
            str(self.task.id),
            str(self.job_hash),
        )
        attachment = None

        logs = (
            TaskLog.query.filter_by(task_id=self.task.id, job_id=self.job_hash)
            .order_by(TaskLog.status_date.desc())  # type: ignore[union-attr]
            .all()
        )

        error_logs = (
            TaskLog.query.filter_by(task_id=self.task.id, job_id=self.job_hash, error=1)
            .order_by(TaskLog.status_date)
            .all()
        )

        date = str(datetime.datetime.now())

        # pylint: disable=broad-except
        try:
            template = env.get_template("email/email.html.j2")
        except BaseException:
            logging.error(
                "Runner: Failed to get email template: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                error=1,
                job_id=self.job_hash,
                status_id=8,
                message="Failed tto get email template.\n%s" % (str(full_stack()),),
            )
            db.session.add(log)
            db.session.commit()

            self.error += 1
            return False

        # success email
        if self.task.email_completion == 1 and (
            (len(error_logs) < 1 and self.task.email_error == 1)
            or self.task.email_error != 1
        ):
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=8,
                message="Sending completion email.",
            )
            db.session.add(log)
            db.session.commit()

            output = None
            if (
                self.task.email_completion_file == 1
                and self.file_path != ""
                and self.file_path is not None
            ):
                attachment = self.file_path
                if self.task.email_completion_file_embed == 1:
                    with open(self.file_path, newline="") as csvfile:
                        output = list(csv.reader(csvfile))

            # check attachement file size if the task
            # should not send blank files
            if (
                self.task.email_completion_dont_send_empty_file == 1
                and attachment
                # if query and data is blank, or other types and file is 0
                and (
                    (len(self.data_file or "") == 0 and self.task.source_type_id == 1)
                    or os.path.getsize(attachment) == 0
                )
            ):
                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.job_hash,
                    status_id=8,
                    message="Not sending completion email, file is emtpy.",
                )
                db.session.add(log)
                db.session.commit()
                return True

            Smtp(
                task=self.task,
                recipients=self.task.email_completion_recipients,
                subject="Project: %s / Task: %s / Run: %s %s"
                % (
                    self.task.project.name,
                    self.task.name,
                    self.job_hash,
                    date,
                ),
                message=template.render(
                    task=self.task,
                    success=1,
                    date=date,
                    logs=logs,
                    output=output,
                    host=app.config["WEB_HOST"],
                ),
                attachment=attachment,
                attachment_name=None,
                job_hash=self.job_hash,
            )

        # error email
        if self.task.email_error == 1 and len(error_logs) > 0:

            # check if there were any errors

            error_logs = (
                TaskLog.query.filter_by(
                    task_id=self.task.id, job_id=self.job_hash, error=1
                )
                .order_by(TaskLog.status_date)
                .all()
            )

            if len(error_logs) > 0:
                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.job_hash,
                    status_id=8,
                    message="Sending error email.",
                )
                db.session.add(log)
                db.session.commit()

                Smtp(
                    task=self.task,
                    recipients=self.task.email_error_recipients,
                    subject="Error in Project: %s / Task: %s / Run: %s %s"
                    % (
                        self.task.project.name,
                        self.task.name,
                        self.job_hash,
                        date,
                    ),
                    message=template.render(
                        task=self.task,
                        success=0,
                        date=date,
                        logs=logs,
                    ),
                    attachment=None,
                    attachment_name=None,
                    job_hash=self.job_hash,
                )
        return True
