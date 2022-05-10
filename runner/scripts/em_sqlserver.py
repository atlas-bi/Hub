"""Connection handler for SQL Server Databases."""

import csv
import itertools
import sys
import tempfile
from pathlib import Path
from typing import IO, Any, Generator, List, Optional, Tuple

import pyodbc

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
    """Connect to sql server."""
    try:
        conn = pyodbc.connect(
            "Driver={ODBC Driver 18 for SQL Server};" + connection, timeout=timeout * 60
        )
        conn.autocommit = True
        conn.timeout = timeout * 60
        cur = conn.cursor()
        return conn, cur
    except pyodbc.Error as e:
        raise ValueError(f"Failed to connection to database.\n{e}")


class SqlServer:
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
        self.run_id = run_id
        self.connection = connection
        self.timeout = timeout
        self.conn, self.cur = self.__connect()
        self.run_id = run_id
        self.dir = directory
        self.row_count = 0

    def __rows(self, size: int = 500) -> Generator:
        """Return data from query by a generator."""
        log = TaskLog(
            task_id=self.task.id,
            job_id=self.run_id,
            status_id=20,
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

            log.message = "Getting query rows %d-%d of %s" % (
                (size * iteration),
                (size * iteration + len(rows)),
                (str(size * iteration + len(rows)) if len(rows) < size else "?"),
            )
            db.session.add(log)
            db.session.commit()
            yield from rows

    def __connect(self) -> Tuple[Any, Any]:
        return connect(self.connection.strip(), self.timeout)

    def __close(self) -> None:
        self.conn.close()

    def run(self, query: str) -> Tuple[int, List[IO[str]]]:
        """Run a sql query and return temp file location.

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
