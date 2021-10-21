"""Connection handler for Postgres Databases."""

import csv
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Generator, Tuple

import psycopg2

from runner import db
from runner.model import Task, TaskLog

from .em_file import file_size

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from error_print import full_stack

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


class Postgres:
    """Functions to query against sql server."""

    def __init__(self, task: Task, query: str, connection: str, job_hash: str):
        """Initialize class.

        :param task: task requesting the query
        :param query: query to run
        :param connection: connection string
        """
        self.task = task
        self.query = query
        self.connection = connection
        self.job_hash = job_hash
        self.conn, self.cur = self.__connect()

    def __rows(self, size: int = 50) -> Generator:
        """Return data from query by a generator.

        :param cursor: curser containing query output
        :param size: chunk size of rows to return
        """
        while True:
            rows = self.cur.fetchmany(size)
            if not rows:
                break
            yield from rows

    def __connect(self) -> Tuple[Any, Any]:
        try:
            conn = psycopg2.connect(self.connection)
            cur = conn.cursor()
            return conn, cur

        except psycopg2.OperationalError as e:
            logging.error(
                "Postgres: Failed to connect: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(e),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=21,
                error=1,
                message="Failed to connect.\n%s" % (str(e),),
            )
            db.session.add(log)
            db.session.commit()
            return None, None

    def __close(self) -> None:
        self.conn.close()

    def run(self) -> str:
        """Run a sql query and return temp file location.

        Data from query is written to disk in a tempfile. Tempfile
        must be removed after data is consumed!
        """
        if not self.conn or not self.cur:
            # pylint: disable=R1732
            data_file = tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False)

            return data_file.name

        # pylint: disable=broad-except
        try:

            self.cur.execute(self.query)

            with tempfile.NamedTemporaryFile(
                mode="w+", newline="", delete=False
            ) as data_file:
                writer = csv.writer(data_file)

                if self.task.source_query_include_header:
                    writer.writerow(
                        [i[0] for i in self.cur.description]
                        if self.cur.description
                        else []
                    )

                for row in self.__rows():
                    writer.writerow(row)

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=21,
                message=(
                    "Query completed. Data file %s created. Data size: %s."
                    % (data_file.name, file_size(str(os.path.getsize(data_file.name))))
                ),
            )
            db.session.add(log)
            db.session.commit()

            self.__close()

            return data_file.name

        except BaseException:
            logging.error(
                "Postgresql: Failed to run query: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=20,
                error=1,
                message="Failed to run query.\n%s" % (str(full_stack()),),
            )
            db.session.add(log)
            db.session.commit()

            self.__close()
            # pylint: disable=R1732
            data_file = tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False)

            return data_file.name