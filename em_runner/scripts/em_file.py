"""Local file manager."""
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
import sys
import zipfile
from pathlib import Path

import gnupg
from crypto import em_decrypt
from error_print import full_stack
from flask import current_app as app

from em_runner import db
from em_runner.model import TaskLog
from em_runner.scripts.em_date import DateParsing

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")


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


def file_size(size):
    """Convert file size from bytes to appropriate file size string.

    Input size (string) must be a # of bytes.

    :param size str: number of bytes
    :returns: string of formatted file size.
    """
    size = int(size) if isinstance(size, int) else int(size[:-1])

    step_unit = 1000.0

    for letters in ["bytes", "KB", "MB", "GB", "TB"]:
        if size < step_unit:
            return "%3.1f %s" % (size, letters)
        size /= step_unit

    return size + "bytes"


class File:
    """Files are created in the drive /em/temp/ from any data sent.

    File name and full file path+name are returned.
    """

    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes
    def __init__(self, task, data_file, job_hash):
        """Set up class parameters.

        :param task: task object
        :param data: data to drop into file
        """
        self.task = task
        self.data_file = data_file
        self.file_name = ""
        self.file_path = ""
        self.zip_name = ""
        self.file_hash = ""
        self.job_hash = job_hash
        self.base_path = self.temp_path = "%s/temp/%s/%s/%s/" % (
            str(Path(__file__).parent.parent),
            self.task.project.name.replace(" ", "_"),
            self.task.name.replace(" ", "_"),
            self.job_hash,
        )

    def __quote_level(self):
        """Return quote level based on task values.

        :returns: quote level as an integer.
        """
        task_level = (
            self.task.destination_quote_level_id
            if self.task.destination_quote_level_id is not None
            and self.task.destination_quote_level_id > 0
            and self.task.destination_quote_level_id <= 4
            else 3
        )

        quote_levels = {
            1: 3,  # "csv.QUOTE_NONE",
            2: 1,  # "csv.QUOTE_ALL",
            3: 0,  # "csv.QUOTE_MINIMAL",
            4: 2,  # "csv.QUOTE_NONNUMERIC",
        }

        return quote_levels[task_level]

    def save(self):
        """Create and save the file.

        :returns: [filename, filepath] of final file.
        """
        # pylint: disable=missing-function-docstring
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        logging.info(
            "File: Saving File: Task: %s, with run: %s",
            str(self.task.id),
            str(self.job_hash),
        )
        if (
            self.task.destination_file_name is None
            or self.task.destination_file_name == ""
        ):
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=11,  # 11 = file
                message="No filename specified, log file "
                + self.job_hash
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
                job_id=self.job_hash,
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
                self.task, self.task.destination_file_name, self.job_hash
            ).string_to_date()

        else:
            self.file_name = self.job_hash or (
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

            with open(self.data_file, "r", newline="") as data_file:
                reader = csv.reader(data_file)

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
                        for row in reader:
                            new_row = [
                                (x.strip('"').strip("'") if isinstance(x, str) else x)
                                for x in row
                            ]

                            if (
                                self.task.destination_file_type_id == 1
                                or self.task.destination_file_type_id == 2
                                or self.task.destination_file_type_id == 4
                            ) and (
                                self.task.destination_file_line_terminator is not None
                                and self.task.destination_file_line_terminator != ""
                            ):
                                new_row.append(
                                    self.task.destination_file_line_terminator
                                )

                            wrtr.writerow(new_row)

                    # if xlxs (3)
                    elif self.task.destination_file_type_id == 3:
                        wrtr = csv.writer(
                            myfile,
                            dialect="excel",
                            quoting=self.__quote_level(),
                        )
                        for row in reader:
                            new_row = [
                                (x.strip('"').strip("'") if isinstance(x, str) else x)
                                for x in row
                            ]
                            wrtr.writerow(new_row)

                    else:
                        for line in data_file:
                            myfile.write(line)

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=11,  # 11 = file
                message="File created: " + self.file_path,
            )
            db.session.add(log)
            db.session.commit()

            # encrypt file
            if self.task.file_gpg == 1:
                gpg = gnupg.GPG("/usr/local/bin/gpg")

                # import the key
                keychain = gpg.import_keys(
                    em_decrypt(self.task.file_gpg_conn.key, app.config["PASS_KEY"])
                )

                # set it to trusted
                gpg.trust_keys(keychain.fingerprints, "TRUST_ULTIMATE")

                # encrypt file
                with open(self.file_path, "rb") as my_file:
                    encrypt_status = gpg.encrypt_file(
                        file=my_file,
                        recipients=keychain.fingerprints,
                        output=self.file_path + ".gpg",
                    )

                # remove key
                gpg.delete_keys(keychain.fingerprints)

                # update global file name
                if not encrypt_status.ok:
                    log = TaskLog(
                        task_id=self.task.id,
                        job_id=self.job_hash,
                        status_id=11,  # 11 = file
                        error=1,
                        message="File failed to encrypt: %s\n%s\n%s"
                        % (
                            self.file_path,
                            encrypt_status.status,
                            encrypt_status.stderr,
                        ),
                    )

                    db.session.add(log)
                    db.session.commit()
                    raise ValueError("failed to encrypt file.")

                self.file_path = self.file_path + ".gpg"
                self.file_name = self.file_name + ".gpg"

                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.job_hash,
                    status_id=11,  # 11 = file
                    message="File encrypted: %s\n%s\n%s"
                    % (self.file_path, encrypt_status.status, encrypt_status.stderr),
                )

                db.session.add(log)
                db.session.commit()

            # get file hash.. after encrypting
            with open(self.file_path, "rb") as my_file:
                self.file_hash = hashlib.md5()  # noqa: S303
                while True:
                    chunk = my_file.read(8192)
                    if not chunk:
                        break
                    self.file_hash.update(chunk)

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=11,  # 11 = file
                message="File md5 hash: %s" % (self.file_hash.hexdigest()),
            )

            db.session.add(log)
            db.session.commit()

            # create zip
            if self.task.destination_create_zip == 1:

                self.zip_name = (
                    DateParsing(
                        self.task, self.task.destination_zip_name, self.job_hash
                    )
                    .string_to_date()
                    .replace(".zip", "")
                    + ".zip"
                )

                with zipfile.ZipFile(self.base_path + self.zip_name, "w") as zip_file:
                    zip_file.write(
                        self.file_path,
                        compress_type=zipfile.ZIP_DEFLATED,
                        arcname=self.file_name,
                    )

                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.job_hash,
                    status_id=11,  # 11 = file
                    message="ZIP archive created: " + self.file_path,
                )
                db.session.add(log)
                db.session.commit()

                # now we remove the left behind file and change all file stuff to our zip.
                os.remove(self.file_path)
                self.file_name = self.zip_name
                self.file_path = self.base_path + self.zip_name

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "File: Failed to Save File: Task: %s, with run:%s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                error=1,
                status_id=11,  # 11 = file
                message="Failed to create file: "
                + self.file_path
                + "\n"
                + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

        return self.file_name, self.file_path, self.file_hash.hexdigest()
