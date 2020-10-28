"""
    Module used to create local files from data

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
import logging
import os
from pathlib import Path
import re
import zipfile
from em import app, db
from .error_print import full_stack
from ..model.model import TaskLog
from .date_parsing import DateParsing


class File:
    """
    files are created in the drive /em/temp/ from any data sent.
    file name and full file path+name are returned.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, task, data):

        self.task = task
        self.data = data
        self.file_name = ""
        self.file_path = ""
        self.zip_name = ""
        self.base_path = self.temp_path = (
            str(Path(__file__).parent.parent)
            + "/temp/"
            + self.task.project.name.replace(" ", "_")
            + "/"
            + self.task.name.replace(" ", "_")
            + "/"
            + self.task.last_run_job_id
            + "/"
        )

    def __quote_level(self):
        """ sets quote level based on task values """

        task_level = (
            self.task.destination_quote_level_id
            if self.task.destination_quote_level_id is not None
            and self.task.destination_quote_level_id > 0
            and self.task.destination_quote_level_id <= 4
            else 3
        )

        quote_levels = {
            1: 2,  # "csv.QUOTE_NONE",
            2: 1,  # "csv.QUOTE_ALL",
            3: 0,  # "csv.QUOTE_MINIMAL",
            4: 3,  # "csv.QUOTE_NONNUMERIC",
        }

        return quote_levels[task_level]

    def save(self):
        # pylint: disable=missing-function-docstring
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        logging.info(
            "File: Saving File: Task: %s, with run: %s",
            str(self.task.id),
            str(self.task.last_run_job_id),
        )
        if (
            self.task.destination_file_name is None
            or self.task.destination_file_name == ""
        ):
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=11,  # 11 = file
                message="No filename specified, log file "
                + self.task.last_run_job_id
                + ".log will be used.",
            )
            db.session.add(log)
            db.session.commit()

        if (
            self.task.destination_file_type_id is None
            or self.task.destination_file_type_id == ""
            and ("." not in self.task.destination_file_name)
        ):
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=11,  # 11 = file
                message="No filetype specified, default file type will be used.",
            )
            db.session.add(log)
            db.session.commit()

        if (
            self.task.destination_file_name != ""
            and self.task.destination_file_name is not None
        ):

            self.file_name = DateParsing(
                self.task, self.task.destination_file_name
            ).string_to_date()

        else:
            self.file_name = self.task.last_run_job_id or (
                datetime.datetime.now().strftime("%s") + ".log"
            )

        if self.task.destination_file_type_id != 4:  # 4=other
            if self.task.file_type is not None:
                self.file_name += "." + (self.task.file_type.ext or "csv")

            else:
                self.file_name += ".csv"

        self.file_name = re.sub(r"\s+", "", self.file_name)

        self.file_path = self.base_path + self.file_name

        Path(
            self.base_path,
        ).mkdir(parents=True, exist_ok=True)

        try:

            if self.data is None:
                data = "No data to load."
            else:
                data = self.data

            with open(self.file_path, mode="w") as myfile:
                # if csv (1) or text (2) and had delimiter

                if (
                    self.task.destination_file_type_id == 1
                    or self.task.destination_file_type_id == 2
                    or self.task.destination_file_type_id == 4
                ) and (
                    self.task.destination_ignore_delimiter is None
                    or self.task.destination_ignore_delimiter != 1
                ):
                    wrtr = (
                        csv.writer(
                            myfile,
                            delimiter=str(self.task.destination_file_delimiter)
                            .encode("utf-8")
                            .decode("unicode_escape"),
                            quoting=self.__quote_level(),
                        )
                        if self.task.destination_file_delimiter is not None
                        and len(self.task.destination_file_delimiter) > 0
                        and (
                            self.task.destination_file_type_id == 2
                            or self.task.destination_file_type_id == 4
                        )  # txt or other
                        else csv.writer(
                            myfile,
                            quoting=self.__quote_level(),
                        )
                    )
                    for row in data:
                        new_row = [
                            (x.strip('"').strip("'") if isinstance(x, str) else x)
                            for x in row
                        ]
                        wrtr.writerow(new_row)

                # if xlxs (3)
                elif self.task.destination_file_type_id == 3:
                    wrtr = csv.writer(
                        myfile,
                        dialect="excel",
                        quoting=self.__quote_level(),
                    )
                    for row in data:
                        new_row = [
                            (x.strip('"').strip("'") if isinstance(x, str) else x)
                            for x in row
                        ]
                        wrtr.writerow(new_row)

                else:
                    myfile.write(str(data))

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=11,  # 11 = file
                message="File created: " + self.file_path,
            )
            db.session.add(log)
            db.session.commit()

            # create zip
            if self.task.destination_create_zip == 1:

                self.zip_name = (
                    DateParsing(self.task, self.task.destination_zip_name)
                    .string_to_date()
                    .replace(".zip", "")
                    + ".zip"
                )

                zip_file = zipfile.ZipFile(self.base_path + self.zip_name, "w")
                zip_file.write(
                    self.file_path,
                    compress_type=zipfile.ZIP_DEFLATED,
                    arcname=self.file_name,
                )
                zip_file.close()

                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.task.last_run_job_id,
                    status_id=11,  # 11 = file
                    message="ZIP archive created: " + self.file_path,
                )
                db.session.add(log)
                db.session.commit()

                # now we remove the left behind file and change all file stuff to our zip.
                os.remove(self.file_path)
                self.file_name = self.zip_name
                self.file_path = self.base_path + self.zip_name

        # pylint: disable=bare-except
        except:
            logging.error(
                "File: Failed to Save File: Task: %s, with run:%s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                error=1,
                status_id=11,  # 11 = file
                message="Failed to create file: "
                + self.file_path
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

        return self.file_name, self.file_path
