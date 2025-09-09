"""Connection handler for Postgres Databases."""

import csv
import itertools
import sys
import tempfile
from pathlib import Path
from typing import IO, Any, Generator, List, Optional, Tuple

import psycopg2

from runner import db
from runner.model import Task, TaskLog

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


def connect(connection: str, timeout: int) -> Tuple[Any, Any]:
    """Connect to postgres server."""
    try:
        conn = psycopg2.connect(
            connection,
            connect_timeout=timeout * 60,
            options=f"-c statement_timeout={timeout * 60}",
        )
        cur = conn.cursor()
        return conn, cur

    except psycopg2.Error as e:
        raise ValueError(f"Failed to connect to database.\n{e}")


class Postgres:
    """Functions to query against sql server."""

    def __init__(
        self,
        task: Task,
        run_id: Optional[str],
        connection: str,
        timeout: int,
        directory: Path,
    ):
        """Initialize class."""
        self.task = task
        self.connection = connection
        self.run_id = run_id
        self.dir = directory
        self.timeout = timeout
        self.conn, self.cur = self.__connect()
        self.row_count = 0

    def __rows(self, size: int = 50) -> Generator:
        """Return data from query by a generator."""
        log = TaskLog(
            task_id=self.task.id,
            job_id=self.run_id,
            status_id=21,
            message=("Getting first %d query rows." % size),
        )
        db.session.add(log)
        db.session.commit()

        for iteration in itertools.count():
            if self.cur.description is None:
                break

            rows = self.cur.fetchmany(size)

            if not rows:
                break

            self.row_count = size * iteration + len(rows)

            log.message = "Getting query rows %d-%d of ?" % (
                (size * iteration),
                (size * iteration + len(rows)),
            )
            db.session.add(log)
            db.session.commit()

            yield from rows

    def __connect(self) -> Tuple[Any, Any]:
        return connect(self.connection.strip(), self.timeout)

    def __close(self) -> None:
        self.conn.close()

    def run(self, query: str) -> Tuple[int, List[IO[str]]]:
        """Run a sql query.

        Data is loaded into a temp file.

        Returns a path or raises an exception.
        """
        self.cur.execute(query)

        with tempfile.NamedTemporaryFile(
            mode="w+", newline="", delete=False, dir=self.dir
        ) as data_file:
            writer = csv.writer(data_file)

            if self.task.source_query_include_header:
                writer.writerow(
                    [i[0] for i in self.cur.description] if self.cur.description else []
                )

            for row in self.__rows():
                writer.writerow(row)

        self.__close()

        if self.task.source_require_sql_output == 1 and self.row_count == 0:
            raise ValueError("SQL output is required but no records returned.")

        return self.row_count, [data_file]
