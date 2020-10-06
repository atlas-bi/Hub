"""
    task runner

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

import csv
import datetime
import hashlib
import logging
import os
import time
import sqlite3
from pathlib import Path
import shutil
import psycopg2
import pyodbc
from jinja2 import Environment, PackageLoader, select_autoescape
from em import db
from .crypto import em_decrypt
from .ftp import Ftp
from .file import File
from .py_processer import PyProcesser
from .sftp import Sftp
from .smb import Smb
from .smtp import Smtp
from .date_parsing import DateParsing
from .error_print import full_stack
from ..model.model import (
    TaskLog,
    Task,
)
from ..web.filters import datetime_format
from .source_code import SourceCode


env = Environment(
    loader=PackageLoader("em", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


env.filters["datetime_format"] = datetime_format


class Runner:
    """
        several methods..
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, task_id):

        # create ID for the run instance
        my_hash = hashlib.sha256()
        my_hash.update(str(time.time() * 1000).encode("utf-8"))
        self.hash = my_hash.hexdigest()[:10]
        tasks = Task.query.filter_by(id=task_id).all()

        for task in tasks:
            print("starting task " + str(task.id))
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
                task_id=task.id, job_id=self.hash, status_id=8, message="Starting task."
            )
            db.session.add(log)
            db.session.commit()

            self.task = task

            self.temp_path = (
                str(Path(__file__).parent.parent)
                + "/temp/"
                + self.task.project.name.replace(" ", "_")
                + "/"
                + self.task.name.replace(" ", "_")
                + "/"
                + self.task.last_run_job_id
                + "/"
            )
            # load file/ run query/ etc to get some sort of data or process something.
            self.__get_source()

            # builds the resulting data into a file
            self.__build_file()

            # any data post-processing

            if self.task.processing_type_id is not None:
                self.__process()

            # permanent storage of the file for hystorical purposes
            self.__store_file()

            # any cleanup process. remove file from local storage
            self.__send_email()

            self.__clean_up()

            log = TaskLog(
                task_id=task.id,
                job_id=self.hash,
                status_id=8,
                message="Completed task.",
            )
            db.session.add(log)
            db.session.commit()

            # set status to completed if no error logs
            error_logs = (
                TaskLog.query.filter_by(
                    task_id=self.task.id, job_id=self.task.last_run_job_id, error=1
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

        logging.info(
            "Runner: Processing: Task: %s, with run: %s",
            str(self.task.id),
            str(self.task.last_run_job_id),
        )
        # get processing script

        # 1 = smb
        # 2 = sftp
        # 3 = ftp
        # 4 = git url
        # 5 = other url
        # 6 = source code

        processing_script_name = self.temp_path + self.hash + ".py"
        my_file = ""
        if (
            self.task.processing_type_id == 1
            and self.task.processing_smb_id is not None
        ):
            file_name = DateParsing(
                self.task, self.task.source_smb_file
            ).string_to_date()

            my_file = (
                Smb(self.task, self.task.processing_smb_conn, source_path=file_name,)
                .read()
                .decode()
            )

        elif (
            self.task.processing_type_id == 2
            and self.task.processing_sftp_id is not None
        ):
            file_name = DateParsing(
                self.task, self.task.processing_sftp_file
            ).string_to_date()

            my_file = Sftp(
                self.task, self.task.processing_sftp_conn, None, file_name, None
            ).read()

        elif (
            self.task.processing_type_id == 3
            and self.task.processing_ftp_id is not None
        ):
            file_name = DateParsing(
                self.task, self.task.processing_ftp_file
            ).string_to_date()

            my_file = Ftp(
                self.task, self.task.processing_ftp_conn, None, file_name, None
            ).read()
        elif self.task.processing_type_id == 4 and self.task.processing_git is not None:
            my_file = SourceCode(self.task, self.task.processing_git).gitlab()
        elif self.task.processing_type_id == 5 and self.task.processing_url is not None:
            my_file = SourceCode(self.task, self.task.processing_url).web()
        elif (
            self.task.processing_type_id == 6 and self.task.processing_code is not None
        ):
            my_file = self.task.processing_code
        elif self.task.processing_type_id > 0:
            log = TaskLog(
                task_id=self.task.id,
                error=1,
                job_id=self.hash,
                status_id=8,
                message="Not enough information to run a processing script from "
                + self.task.processing_type.name,
            )
            db.session.add(log)
            db.session.commit()

        try:
            if my_file != "" and self.task.processing_type_id > 0:
                with open(processing_script_name, "w") as text_file:
                    text_file.write(my_file)
                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.hash,
                    status_id=8,
                    message="Processing script created.",
                )
                db.session.add(log)
                db.session.commit()

        # pylint: disable=bare-except
        except:
            logging.error(
                "Runner: Failed Processing: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                error=1,
                job_id=self.hash,
                status_id=8,
                message="Processing script failure:\n" + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

        # run processing script
        output = PyProcesser(self.task, processing_script_name, self.file_path,)
        # allow processer to rename file
        if output != "":
            self.file_name = output

    def __get_source(self):
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=inconsistent-return-statements
        try:
            logging.info(
                "Runner: Getting Source: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
            )

            # pylint: disable=no-else-return
            if self.task.source_type_id == 1:  # sql

                external_db = self.task.source_database_conn
                query = self.__get_query() or "error"
                if query == "error":
                    return query

                if external_db.database_type.id == 1:  # postgres
                    conn = psycopg2.connect(em_decrypt(external_db.connection_string))

                elif external_db.database_type.id == 2:  # mssql
                    conn = pyodbc.connect(
                        "Driver={ODBC Driver 17 for SQL Server};"
                        + em_decrypt(external_db.connection_string)
                    )
                    conn.autocommit = True

                elif external_db.database_type.id == 3:  # sqlite

                    # need to save sqlite db locally, then remove it when finished query :/

                    with open(self.temp_path + self.hash + ".sqlite", "a") as database:
                        if self.task.source_query_type_id == 2:  # smb
                            database.write(
                                Smb(self.task, self.task.query_smb_conn,)
                                .read()
                                .decode()
                            )
                        elif self.task.source_query_type_id == 6:  # ftp
                            database.write(
                                Ftp(self.task, self.task.query_ftp_conn,).read()
                            )
                        elif self.task.source_query_type_id == 5:  # sftp
                            database.write(
                                Sftp(self.task, self.task.query_stp_conn,).read()
                            )

                    conn = sqlite3.connect(self.temp_path + self.hash + ".sqlite")

                cur = conn.cursor()

                cur.execute(query)

                head = []
                if self.task.source_query_include_header:
                    head = [i[0] for i in cur.description] if cur.description else []

                x = cur.fetchall()

                if self.task.source_query_include_header and cur.description != []:
                    # add header to data
                    x.insert(0, tuple(head))

                cur.close()
                conn.close()
                self.data = x

                if external_db.database_type.id == 3:  # sqlite
                    # remove temp db
                    os.remove(self.temp_path + self.hash + ".sqlite")

                return True

            elif self.task.source_type_id == 2:  # smb file

                file_name = DateParsing(
                    self.task, self.task.source_smb_file
                ).string_to_date()

                my_file = (
                    Smb(
                        self.task,
                        self.task.source_smb_conn,
                        None,
                        file_name,
                        file_name,
                    )
                    .read()
                    .decode()
                )

                if self.task.source_smb_ignore_delimiter == 1:
                    my_delimiter = None

                    self.data = my_file

                else:

                    my_delimiter = (
                        self.task.source_smb_delimiter
                        if self.task.source_smb_delimiter != ""
                        and self.task.source_smb_delimiter is not None
                        else ","
                    )

                    csv_reader = csv.reader(
                        my_file.splitlines(), delimiter=my_delimiter,
                    )

                    x = []
                    for row in csv_reader:
                        x.append(row)

                    self.data = x

                return True

            elif self.task.source_type_id == 3:  # sftp file

                file_name = DateParsing(
                    self.task, self.task.source_sftp_file
                ).string_to_date()

                my_file = Sftp(
                    self.task, self.task.source_sftp_conn, None, file_name, None
                ).read()

                if self.task.source_sftp_ignore_delimiter == 1:
                    my_delimiter = None

                    self.data = my_file

                else:

                    my_delimiter = (
                        self.task.source_sftp_delimiter
                        if self.task.source_sftp_delimiter != ""
                        and self.task.source_sftp_delimiter is not None
                        else ","
                    )

                    csv_reader = csv.reader(
                        my_file.splitlines(), delimiter=my_delimiter,
                    )

                    x = []
                    for row in csv_reader:
                        x.append(row)

                    self.data = x

                return True

            elif self.task.source_type_id == 4:  # ftp file

                file_name = DateParsing(
                    self.task, self.task.source_ftp_file
                ).string_to_date()

                my_file = Ftp(
                    self.task, self.task.source_ftp_conn, None, file_name, None
                ).read()

                if self.task.source_ftp_ignore_delimiter == 1:
                    my_delimiter = None

                    self.data = my_file

                else:

                    my_delimiter = (
                        self.task.source_ftp_delimiter
                        if self.task.source_ftp_delimiter != ""
                        and self.task.source_ftp_delimiter is not None
                        else ","
                    )

                    csv_reader = csv.reader(
                        my_file.splitlines(), delimiter=my_delimiter,
                    )

                    x = []
                    for row in csv_reader:
                        x.append(row)

                    self.data = x

                return True

        # pylint: disable=bare-except
        except:
            logging.error(
                "Runner: Failed Getting Source: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                error=1,
                job_id=self.hash,
                status_id=8,
                message="Failed to get data source.\n" + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
            self.data = None

            return False

    def __get_query(self):
        query = "error"
        if self.task.source_query_type_id == 3:  # url
            query = SourceCode(self.task, self.task.source_url).web()

        elif self.task.source_query_type_id == 1:  # gitlab url
            query = SourceCode(self.task, self.task.source_git).gitlab()

        elif self.task.source_query_type_id == 4:  # code
            query = SourceCode(self.task, None).cleanup(
                self.task.source_code,
                ("mssql" if self.task.source_database_id == 2 else None),
                self.task.query_params,
                self.task.project.global_params,
            )

        elif self.task.source_query_type_id == 2:
            query = SourceCode(self.task, None).cleanup(
                Smb(self.task, source_path=self.task.source_query_file,)
                .read()
                .decode(),
                ("mssql" if self.task.source_database_id == 2 else None),
                self.task.query_params,
                self.task.project.global_params,
            )

        return query

    def __build_file(self):

        """
            file will be built locally then dumped onto a file server.
            webserver is not used for long-term storage.

            files are kept in /em/em/temp/<extract name>

        """
        logging.info(
            "Runner: Building File: Task: %s, with run: %s",
            str(self.task.id),
            str(self.task.last_run_job_id),
        )
        self.file_name, self.file_path = File(self.task, self.data).save()

    def __store_file(self):
        
         # only store if there are no errors.
        error_logs = (
            TaskLog.query.filter_by(
                task_id=self.task.id, job_id=self.task.last_run_job_id, error=1
            )
            .order_by(TaskLog.status_date)
            .all()
        )

        if len(error_logs) > 0:
            logging.error(
                "Runner: Files not stored because of run error: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                error=1,
                job_id=self.hash,
                status_id=8,
                message="Files not stored because of run error.",
            )
            db.session.add(log)
            db.session.commit()
            return False


        logging.info(
            "Runner: Storing file: Task: %s, with run: %s",
            str(self.task.id),
            str(self.task.last_run_job_id),
        )
        # send to sftp
        if self.task.destination_sftp == 1:

            Sftp(
                self.task,
                self.task.destination_sftp_conn,
                self.task.destination_sftp_overwrite,
                self.file_name,
                self.file_path,
            ).save()

        # send to ftp
        if self.task.destination_ftp == 1:
            Ftp(
                self.task,
                self.task.destination_ftp_conn,
                self.task.destination_ftp_overwrite,
                self.file_name,
                self.file_path,
            ).save()

        # save to smb
        if self.task.destination_smb == 1:
            Smb(
                self.task,
                self.task.destination_smb_conn,
                self.task.destination_smb_overwrite,
                self.file_name,
                self.file_path,
            ).save()

        # save historical copy
        Smb(
            self.task,
            "default",
            self.task.destination_smb_overwrite,
            self.file_name,
            self.file_path,
        ).save()

        return True

    def __clean_up(self):

        # remove file
        try:
            shutil.rmtree(self.temp_path)

        # pylint: disable=bare-except
        except:
            logging.error(
                "Runner: Failed cleanup: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                error=1,
                job_id=self.hash,
                status_id=8,
                message="Failed to clean up job.\n" + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
            self.data = None

    def __send_email(self):
        logging.info(
            "Runner: Sending Mail: Task: %s, with run: %s",
            str(self.task.id),
            str(self.task.last_run_job_id),
        )
        attachment = None

        logs = (
            TaskLog.query.filter_by(
                task_id=self.task.id, job_id=self.task.last_run_job_id
            )
            .order_by(TaskLog.status_date.desc())
            .all()
        )

        error_logs = (
            TaskLog.query.filter_by(
                task_id=self.task.id, job_id=self.task.last_run_job_id, error=1
            )
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
                job_id=self.task.last_run_job_id,
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

            Smtp(
                self.task,
                self.task.email_completion_recipients,
                "Project: "
                + self.task.project.name
                + " / Task: "
                + self.task.name
                + " / Run: "
                + self.task.last_run_job_id
                + " "
                + date,
                template.render(task=self.task, success=1, date=date, logs=logs,),
                attachment,
                None,
            )

        # error email
        if self.task.email_error == 1 and len(error_logs) > 0:

            # check if there were any errors

            error_logs = (
                TaskLog.query.filter_by(
                    task_id=self.task.id, job_id=self.task.last_run_job_id, error=1
                )
                .order_by(TaskLog.status_date)
                .all()
            )

            if len(error_logs) > 0:
                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.task.last_run_job_id,
                    status_id=8,
                    message="Sending error email.",
                )
                db.session.add(log)
                db.session.commit()

                Smtp(
                    self.task,
                    self.task.email_error_recipients,
                    "Error in Project: "
                    + self.task.project.name
                    + " / Task: "
                    + self.task.name
                    + " / Run: "
                    + self.task.last_run_job_id
                    + " "
                    + date,
                    template.render(task=self.task, success=0, date=date, logs=logs,),
                    None,
                    None,
                )
