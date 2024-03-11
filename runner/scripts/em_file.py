"""Local file manager."""

import csv
import hashlib
import os
import sys
import zipfile
from pathlib import Path
from typing import IO, Optional, Tuple, Union

import gnupg
from crypto import em_decrypt
from flask import current_app as app

from runner.model import Task
from runner.scripts.em_date import DateParsing
from runner.scripts.em_messages import RunnerException, RunnerLog
from runner.scripts.em_params import ParamLoader

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


def file_size(size: Union[str, int]) -> str:
    """Convert file size from bytes to appropriate file size string.

    Input size (int) must be a # of bytes.
    """
    if isinstance(size, int) or size.isdigit():
        step_unit = 1000.0
        out: float = float(size)
        for letters in ["bytes", "KB", "MB", "GB", "TB"]:
            if float(out) < step_unit:
                return "%3.1f %s" % (out, letters)
            out /= step_unit

    return str(size) + " bytes"


class File:
    """Files are created in the drive /em/temp/ from any data sent.

    File name and full file path+name are returned.
    """

    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes
    def __init__(
        self, task: Task, run_id: Optional[str], data_file: IO[bytes], params: ParamLoader
    ) -> None:
        """Set up class parameters."""
        self.task = task
        self.data_file = data_file
        self.file_name = ""
        self.file_path = ""
        self.zip_name = ""
        self.file_hash = hashlib.md5()  # noqa: S303
        self.run_id = run_id
        self.base_path = str(
            Path(
                data_file.name,
            ).parent
        )
        self.params = params

    def __quote_level(self) -> int:
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

    def __quotechar(self) -> str:
        if self.__quote_level() == 3:  # quote none
            return ""

        return '"'

    def save(self) -> Tuple[str, str, str]:
        """Create and save the file.

        returns [filename, filepath] of final file.
        """
        if self.task.destination_file_name is None or self.task.destination_file_name == "":
            RunnerLog(
                self.task,
                self.run_id,
                11,
                f"No filename specified, {Path(self.data_file.name).name} will be used.",
            )

        if self.task.destination_file_name != "" and self.task.destination_file_name is not None:
            # insert params
            self.file_name = self.params.insert_file_params(
                self.task.destination_file_name.strip()
            )

            # parse python dates
            self.file_name = DateParsing(self.task, self.run_id, self.file_name).string_to_date()

        else:
            self.file_name = Path(self.data_file.name).name

        # 4 is other
        if self.task.destination_file_type_id != 4 and self.task.file_type is not None:
            self.file_name += "." + (self.task.file_type.ext or "csv")

        self.file_path = str(Path(self.base_path).joinpath(self.file_name))

        # if the source name matches the destination name, rename the source and update tmp file name.
        if self.data_file.name == self.file_path:
            data_file_as_path = Path(self.data_file.name)
            new_data_file_name = str(
                data_file_as_path.parent
                / (data_file_as_path.stem + "_tmp" + data_file_as_path.suffix)
            )
            os.rename(self.data_file.name, new_data_file_name)
            self.data_file.name = new_data_file_name  # type: ignore[misc]

        # if ignore delimiter is checked, then use binary to copy contents
        if self.task.destination_ignore_delimiter == 1:
            with open(self.data_file.name, "rb") as data_file_binary, open(
                self.file_path, mode="wb"
            ) as myfile_binary:
                for line_binary in data_file_binary:
                    myfile_binary.write(line_binary)

        # otherwise use unicode.
        else:
            with open(self.data_file.name, "r", newline="") as data_file:
                reader = csv.reader(data_file)

                with open(self.file_path, mode="w", encoding="utf-8") as myfile:
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
                                quotechar=self.__quotechar(),
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
                                quotechar=self.__quotechar(),
                            )
                        )
                        for row in reader:
                            new_row = [
                                (x.strip('"').strip("'") if isinstance(x, str) else x) for x in row
                            ]

                            if (
                                self.task.destination_file_type_id == 1
                                or self.task.destination_file_type_id == 2
                                or self.task.destination_file_type_id == 4
                            ) and (
                                self.task.destination_file_line_terminator is not None
                                and self.task.destination_file_line_terminator != ""
                            ):
                                new_row.append(self.task.destination_file_line_terminator)

                            wrtr.writerow(new_row)

                    # if xlxs (3)
                    elif self.task.destination_file_type_id == 3:
                        wrtr = csv.writer(
                            myfile,
                            dialect="excel",
                            quoting=self.__quote_level(),
                            quotechar=self.__quotechar(),
                        )
                        for row in reader:
                            new_row = [
                                (x.strip('"').strip("'") if isinstance(x, str) else x) for x in row
                            ]
                            wrtr.writerow(new_row)

                    else:
                        for line in data_file:
                            myfile.write(line)

        RunnerLog(
            self.task,
            self.run_id,
            11,
            f"File {self.file_name} created. Size: {file_size(Path(self.file_path).stat().st_size)}.\n{self.file_path}",
        )

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
                    my_file,  # the file
                    keychain.fingerprints,  # the recipients
                    output=self.file_path + ".gpg",
                )

            # remove key
            gpg.delete_keys(keychain.fingerprints)

            # update global file name
            if not encrypt_status.ok:
                raise RunnerException(
                    self.task,
                    self.run_id,
                    11,
                    "File failed to encrypt.\n%s\n%s\n%s"
                    % (
                        self.file_path,
                        encrypt_status.status,
                        encrypt_status.stderr,
                    ),
                )

            self.file_path = self.file_path + ".gpg"
            self.file_name = self.file_name + ".gpg"

            RunnerLog(
                self.task,
                self.run_id,
                11,
                "File encrypted.\n%s\n%s\n%s"
                % (self.file_path, encrypt_status.status, encrypt_status.stderr),
            )

        # get file hash.. after encrypting
        with open(self.file_path, "rb") as my_file:
            while True:
                chunk = my_file.read(8192)
                if not chunk:
                    break
                self.file_hash.update(chunk)

        RunnerLog(self.task, self.run_id, 11, f"File md5 hash: {self.file_hash.hexdigest()}")

        # create zip
        if self.task.destination_create_zip == 1:
            self.zip_name = DateParsing(
                self.task, self.run_id, str(self.task.destination_zip_name)
            ).string_to_date()

            # parse params
            self.zip_name = self.params.insert_file_params(self.zip_name)

            self.zip_name = self.zip_name.replace(".zip", "") + ".zip"

            with zipfile.ZipFile(
                str(Path(self.base_path).joinpath(self.zip_name)), "w"
            ) as zip_file:
                zip_file.write(
                    self.file_path,
                    compress_type=zipfile.ZIP_DEFLATED,
                    arcname=self.file_name,
                )

            # now we change all file stuff to our zip.

            self.file_name = self.zip_name
            self.file_path = str(Path(self.base_path).joinpath(self.zip_name))

            RunnerLog(self.task, self.run_id, 11, f"ZIP archive created.\n{self.file_path}")

        return self.file_name, self.file_path, self.file_hash.hexdigest()
