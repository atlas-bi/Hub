"""Extension script to seed the database.

Database must be seeded on first run of atlas hub.

.. code-block:: console

    export FLASK_APP=web
    flask db init
    flask db migrate
    flask db upgrade
    flask seed

    # and for demo
    flask seed_demo

"""
# pylint: disable=C0301

from sqlalchemy.orm import Session

from web.model import (
    Connection,
    ConnectionDatabase,
    ConnectionDatabaseType,
    ConnectionFtp,
    LoginType,
    Project,
    QuoteLevel,
    Task,
    TaskDestinationFileType,
    TaskProcessingType,
    TaskSourceQueryType,
    TaskSourceType,
    TaskStatus,
    User,
)

from .extensions import db, get_or_create


def seed(session: Session) -> None:
    """Insert seed records to database."""
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    # login types

    get_or_create(session, LoginType, name="login")
    get_or_create(session, LoginType, name="logout")
    get_or_create(session, LoginType, name="bad login")

    # quote level
    get_or_create(session, QuoteLevel, name="Quote None")
    get_or_create(session, QuoteLevel, name="Quote All")
    get_or_create(session, QuoteLevel, name="Quote Minimal (default)")
    get_or_create(session, QuoteLevel, name="Quote Non-numeric")

    # task source type
    get_or_create(session, TaskSourceType, name="Database")
    get_or_create(session, TaskSourceType, name="Network File (SMB Connection)")
    get_or_create(session, TaskSourceType, name="File (SFTP Connection)")
    get_or_create(session, TaskSourceType, name="File (FTP Connection)")
    get_or_create(session, TaskSourceType, name="Python Script")
    get_or_create(session, TaskSourceType, name="SSH Command")

    # task processing type
    get_or_create(session, TaskProcessingType, name="Network File (SMB Connection)")
    get_or_create(session, TaskProcessingType, name="File (SFTP Connection)")
    get_or_create(session, TaskProcessingType, name="File (FTP Connection)")
    get_or_create(session, TaskProcessingType, name="Git URL")
    get_or_create(session, TaskProcessingType, name="Other URL (no auth)")
    get_or_create(session, TaskProcessingType, name="Source Code")

    # task source query type
    get_or_create(session, TaskSourceQueryType, name="Git URL")
    get_or_create(session, TaskSourceQueryType, name="File Path (SMB Connection)")
    get_or_create(session, TaskSourceQueryType, name="Other URL (no auth)")
    get_or_create(session, TaskSourceQueryType, name="Source Code")
    get_or_create(session, TaskSourceQueryType, name="File Path (SFTP Connection)")
    get_or_create(session, TaskSourceQueryType, name="File Path (FTP Connection)")

    # database type
    get_or_create(session, ConnectionDatabaseType, name="Postgres")
    get_or_create(session, ConnectionDatabaseType, name="SQL Sever")

    # file types
    get_or_create(session, TaskDestinationFileType, name="CSV (.csv)", ext="csv")
    get_or_create(session, TaskDestinationFileType, name="Text (.txt)", ext="txt")
    get_or_create(session, TaskDestinationFileType, name="Excel (.csv)", ext="csv")
    get_or_create(
        session, TaskDestinationFileType, name="Other (specify in filename)", ext=""
    )

    # task status
    get_or_create(session, TaskStatus, name="Running")
    get_or_create(session, TaskStatus, name="Errored")
    get_or_create(session, TaskStatus, name="Stopped")
    get_or_create(session, TaskStatus, name="Completed")
    get_or_create(session, TaskStatus, name="Starting")
    get_or_create(session, TaskStatus, name="Scheduler")
    get_or_create(session, TaskStatus, name="User")
    get_or_create(session, TaskStatus, name="Runner")
    get_or_create(session, TaskStatus, name="SFTP")
    get_or_create(session, TaskStatus, name="SMB")
    get_or_create(session, TaskStatus, name="File")
    get_or_create(session, TaskStatus, name="Email")
    get_or_create(session, TaskStatus, name="FTP")
    get_or_create(session, TaskStatus, name="Py Processer")
    get_or_create(session, TaskStatus, name="Git/Web Code")
    get_or_create(session, TaskStatus, name="Date Parser")
    get_or_create(session, TaskStatus, name="Cmd Runner")
    get_or_create(session, TaskStatus, name="System")
    get_or_create(session, TaskStatus, name="SSH")
    get_or_create(session, TaskStatus, name="SQL Server")
    get_or_create(session, TaskStatus, name="Postgres")


def seed_demo() -> None:
    """Seed info for demo."""
    # demo user
    get_or_create(
        db.session,
        User,
        full_name="Mr Cool",
        first_name="Mr",
        account_name="mr-cool",
        email="mr@co.ol",
    )

    # demo connection group
    get_or_create(
        db.session,
        Connection,
        name="Extract Organization",
        description="The best place to send data.",
        address="Organization Extract",
        primary_contact="Boss Man",
        primary_contact_email="boss@ma.n",
        primary_contact_phone="(000)-000-0000",
    )

    # demo db
    get_or_create(
        db.session,
        ConnectionDatabase,
        name="Public Database",
        type_id=1,
        connection_string=(
            "host=hh-pgsql-public.ebi.ac.uk"
            + " dbname=pfmegrnargs user=reader password=NWDMCE5xdipIjRrp"
        ),
        connection_id=1,
    )

    # demo ftp connection (ro)
    get_or_create(  # noqa: S106
        db.session,
        ConnectionFtp,
        connection_id=1,
        name="Speed Test Tele2",
        address="speedtest.tele2.net/",
        path="/upload/",
        username="anonymous",
        password="anonymous",
    )

    # ssh project
    get_or_create(
        db.session,
        Project,
        name="SSH Project",
        description="Group of SSH tasks.",
        owner_id=1,
        creator_id=1,
        updater_id=1,
        intv=1,
        intv_type="h",
        intv_value="1",
    )

    # sql project
    get_or_create(
        db.session,
        Project,
        name="SQL Project",
        description="Group of SQL tasks.",
        owner_id=1,
        creator_id=1,
        updater_id=1,
        intv=1,
        intv_type="h",
        intv_value="1",
    )

    # python project
    get_or_create(
        db.session,
        Project,
        name="Python Project",
        description="Group of Python tasks.",
        owner_id=1,
        creator_id=1,
        updater_id=1,
        intv=1,
        intv_type="h",
        intv_value="1",
    )

    # demo ssh task
    get_or_create(
        db.session,
        Task,
        name="SSH task 1 - check Windows Server CPU",
        source_type_id=6,
        source_code="""powershell  if ((gwmi -class Win32_Processor).LoadPercentage -gt 95){exit 1}""",
        project_id=1,
        source_query_type_id=4,
        enabled=0,
    )
    # demo sql task
    get_or_create(
        db.session,
        Task,
        name="Postgres task 1",
        source_type_id=1,
        source_code="""SELECT
  precomputed.id
FROM rnc_rna_precomputed precomputed
JOIN rnc_taxonomy tax
ON
  tax.id = precomputed.taxid
WHERE
  tax.lineage LIKE 'cellular organisms; Bacteria; %'
  AND precomputed.is_active = true    -- exclude sequences without active cross-references
  AND rna_type = 'rRNA'""",
        destination_ftp=1,
        destination_ftp_id=1,
        project_id=2,
        source_query_type_id=4,
        source_database_id=1,
        enabled=0,
        destination_file_name="test_%d_%m",
        destination_file_type_id=2,
        destination_file_delimiter="|",
    )

    # demo python task
    get_or_create(
        db.session,
        Task,
        name="Python task 1",
        source_type_id=5,
        source_code="""

# Copyright [2009-present] EMBL-European Bioinformatics Institute
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#      http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# An example Python script showing how to access the public RNAcentral Postgres database.
# Usage:
# python example-rnacentral-postgres-script.py



import psycopg2
import psycopg2.extras


def main():
    conn_string = "host='hh-pgsql-public.ebi.ac.uk' dbname='pfmegrnargs' user='reader' password='NWDMCE5xdipIjRrp'"
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # retrieve a list of RNAcentral databases
    query = "SELECT * FROM rnc_database"

    cursor.execute(query)
    for row in cursor:
        print(row)


if __name__ == "__main__":
    main())
""",
        destination_ftp=1,
        destination_ftp_id=1,
        project_id=3,
        source_query_type_id=4,
        enabled=0,
        destination_file_name="test_%d_%m",
        destination_file_type_id=2,
        destination_file_delimiter="|",
    )
