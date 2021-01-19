"""Task runner."""
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


import csv
import datetime
import hashlib
import logging
import os
import re
import shutil
import sys
import time
import urllib.parse
from pathlib import Path

from flask import current_app as app
from jinja2 import Environment, PackageLoader, select_autoescape

from em_runner import db
from em_runner.model import Task, TaskFile, TaskLog
from em_runner.scripts.em_cmd import Cmd
from em_runner.scripts.em_code import SourceCode
from em_runner.scripts.em_date import DateParsing
from em_runner.scripts.em_file import File, file_size
from em_runner.scripts.em_ftp import Ftp
from em_runner.scripts.em_postgres import Postgres
from em_runner.scripts.em_python import PyProcesser
from em_runner.scripts.em_sftp import Sftp
from em_runner.scripts.em_smb import Smb
from em_runner.scripts.em_smtp import Smtp
from em_runner.scripts.em_sqlserver import SqlServer
from em_runner.scripts.em_ssh import Ssh
from em_runner.scripts.em_system import Monitor
from em_runner.web.filters import datetime_format

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from crypto import em_decrypt
from error_print import full_stack

env = Environment(
    loader=PackageLoader("em_runner", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


env.filters["datetime_format"] = datetime_format


class Runner:
    """Group of functions used to run a task."""

    # pylint: disable=too-few-public-methods

    def __init__(self, task_id):
        """Set up class parameters.

        :param int task_id: id of the task to be run.
        """
        # Create id for the run instance and assign to tasks being run.
        my_hash = hashlib.sha256()
        my_hash.update(str(time.time() * 1000).encode("utf-8"))
        self.job_hash = my_hash.hexdigest()[:10]
        tasks = Task.query.filter_by(id=task_id).all()

        for task in tasks:
            self.error = 0
            self.data_file = None
            self.file_path = ""
            self.file_name = ""
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

            # load file/ run query/ etc to get some sort of data or process something.
            if self.error == 0:
                self.__get_source()

            # builds the resulting data into a file
            if self.error == 0:
                self.__build_file()

            # any data post-processing
            if self.error == 0 and self.task.processing_type_id is not None:
                self.__process()

            # permanent storage of the file for hystorical purposes
            if self.error == 0:
                self.__store_file()

            # send confirmation/error emails
            self.__send_email()

            # any cleanup process. remove file from local storage
            self.__clean_up()

            log = TaskLog(
                task_id=task.id,
                job_id=self.job_hash,
                status_id=8,
                error=(0 if self.error == 0 else 1),
                message=("Completed task." if self.error == 0 else "Task cancelled."),
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

            if len(error_logs) > 0:
                task.status_id = 2
            else:
                task.status_id = 4

            task.last_run_job_id = None
            task.last_run = datetime.datetime.now()
            db.session.commit()

    def __process(self):
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

            my_file = (
                Smb(
                    task=self.task,
                    connection=self.task.processing_smb_conn,
                    file_path=file_name,
                    job_hash=self.job_hash,
                    overwrite=None,
                    file_name=None,
                )
                .read()
                .decode()
            )

        elif (
            self.task.processing_type_id == 2
            and self.task.processing_sftp_id is not None
        ):
            file_name = DateParsing(
                self.task, self.task.processing_sftp_file, self.job_hash
            ).string_to_date()

            my_file = Sftp(
                task=self.task,
                connection=self.task.processing_sftp_conn,
                overwrite=None,
                file_name=file_name,
                file_path=None,
                job_hash=self.job_hash,
            ).read()

        elif (
            self.task.processing_type_id == 3
            and self.task.processing_ftp_id is not None
        ):
            file_name = DateParsing(
                task=self.task,
                date_string=self.task.processing_ftp_file,
                job_hash=self.job_hash,
            ).string_to_date()

            my_file = Ftp(
                task=self.task,
                connection=self.task.processing_ftp_conn,
                overwrite=None,
                file_name=file_name,
                file_path=None,
                job_hash=self.job_hash,
            ).read()

        elif self.task.processing_type_id == 4 and self.task.processing_git is not None:

            # if a dir is specified then download all files
            if self.task.processing_command is not None:
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
                my_file = SourceCode(
                    task=self.task, url=self.task.processing_git, job_hash=self.job_hash
                ).gitlab()

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
                my_file = SourceCode(
                    task=self.task, url=self.task.processing_url, job_hash=self.job_hash
                ).web_url()
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

    # pylint: disable=R1710
    def __get_source(self):
        try:
            logging.info(
                "Runner: Getting Source: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )

            # pylint: disable=no-else-return
            if self.task.source_type_id == 1:  # sql

                external_db = self.task.source_database_conn
                query = self.__get_query() or "error"

                if query == "error":
                    self.error += 1
                    return query

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

                my_file = (
                    Smb(
                        task=self.task,
                        connection=self.task.source_smb_conn,
                        overwrite=None,
                        file_name=file_name,
                        file_path=file_name,
                        job_hash=self.job_hash,
                    )
                    .read()
                    .decode()
                )

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

                    self.data_file = list(csv_reader)

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
                        overwrite=None,
                        file_name=file_name,
                        file_path=None,
                        job_hash=self.job_hash,
                    ).read()

                # pylint: disable=broad-except
                except BaseException:
                    self.error += 1
                    return False

                self.data_file = my_file

                # pylint: disable=W0105
                """
                # if self.task.source_sftp_ignore_delimiter == 1:
                #     my_delimiter = None

                #     self.data_file = my_file
                # else:

                #     my_delimiter = (
                #         self.task.source_sftp_delimiter
                #         if self.task.source_sftp_delimiter != ""
                #         and self.task.source_sftp_delimiter is not None
                #         else ","
                #     )

                #     csv_reader = csv.reader(
                #         open(my_file, 'r').readlines(),
                #         delimiter=my_delimiter,
                #     )

                #     self.data_file = list(csv_reader)
                """
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
                    overwrite=None,
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

                    self.data_file = list(csv_reader)

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

    def __get_query(self):
        query = "error"
        if self.task.source_query_type_id == 3:  # url
            query = SourceCode(
                task=self.task, url=self.task.source_url, job_hash=self.job_hash
            ).web_url()

        elif self.task.source_query_type_id == 1:  # gitlab url
            query = SourceCode(
                task=self.task, url=self.task.source_git, job_hash=self.job_hash
            ).gitlab()

        elif self.task.source_query_type_id == 4:  # code
            query = SourceCode(
                task=self.task, url=None, job_hash=self.job_hash
            ).cleanup(
                query=self.task.source_code,
                db_type=("mssql" if self.task.source_database_id == 2 else None),
                task_params=self.task.query_params,
                project_params=self.task.project.global_params,
            )

        elif self.task.source_query_type_id == 2:
            query = SourceCode(self.task, None, self.job_hash).cleanup(
                query=Smb(
                    task=self.task,
                    file_path=self.task.source_query_file,
                    connection=self.task.query_source,
                    overwrite=None,
                    file_name=None,
                    job_hash=self.job_hash,
                )
                .read()
                .decode(),
                db_type=("mssql" if self.task.source_database_id == 2 else None),
                task_params=self.task.query_params,
                project_params=self.task.project.global_params,
            )

        return query

    def __build_file(self):
        """File will be built locally then dumped onto a file server.

        Webserver is not used for long-term storage.

        files are kept in /em/em_runner/temp/<extract name>

        """
        if self.data_file:
            logging.info(
                "Runner: Building File: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )

            self.file_name, self.file_path = File(
                task=self.task, data_file=self.data_file, job_hash=self.job_hash
            ).save()

            # remove data file
            os.remove(self.data_file)

    def __store_file(self):
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
            connection="default",
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
                size=file_size(os.path.getsize(self.temp_path)),
            )
        )
        db.session.commit()

        return True

    def __clean_up(self):

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

    def __send_email(self):
        logging.info(
            "Runner: Sending Mail: Task: %s, with run: %s",
            str(self.task.id),
            str(self.job_hash),
        )
        attachment = None

        logs = (
            TaskLog.query.filter_by(task_id=self.task.id, job_id=self.job_hash)
            .order_by(TaskLog.status_date.desc())
            .all()
        )

        error_logs = (
            TaskLog.query.filter_by(task_id=self.task.id, job_id=self.job_hash, error=1)
            .order_by(TaskLog.status_date)
            .all()
        )

        date = str(datetime.datetime.now())

        template = env.get_template("email/email.html.j2")

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

            if (
                self.task.email_completion_file == 1
                and self.file_path != ""
                and self.file_path is not None
            ):
                attachment = self.file_path

            # check attachement file size if the task
            # should not send blank files
            if (
                self.task.email_completion_dont_send_empty_file == 1
                and attachment
                # if query and data is blank, or other types and file is 0
                and (
                    (len(self.data_file) == 0 and self.task.source_type_id == 1)
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
                return

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
