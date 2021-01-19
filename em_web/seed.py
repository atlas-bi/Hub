"""Extension script to seed EM2's database.

Database must be seeded on first run of EM2.

.. code-block:: console

    export FLASK_APP=em_web
    flask db init
    flask db migrate
    flask db upgrade
    flask seed

    # and for demo
    flask seed_demo

"""
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

from em_web.model import (
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

from .extensions import db


def seed():
    """Insert seed records to database."""
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    # login types
    if LoginType.query.filter_by(name="login").first() is None:
        db.session.add(LoginType(name="login"))
    if LoginType.query.filter_by(name="logout").first() is None:
        db.session.add(LoginType(name="logout"))
    if LoginType.query.filter_by(name="bad login").first() is None:
        db.session.add(LoginType(name="bad login"))

    # quote level
    if QuoteLevel.query.filter_by(name="Quote None").first() is None:
        db.session.add(QuoteLevel(name="Quote None"))
    if QuoteLevel.query.filter_by(name="Quote All").first() is None:
        db.session.add(QuoteLevel(name="Quote All"))
    if QuoteLevel.query.filter_by(name="Quote Minimal (default)").first() is None:
        db.session.add(QuoteLevel(name="Quote Minimal (default)"))
    if QuoteLevel.query.filter_by(name="Quote Non-numeric").first() is None:
        db.session.add(QuoteLevel(name="Quote Non-numeric"))

    # task source type
    if TaskSourceType.query.filter_by(name="Database").first() is None:
        db.session.add(TaskSourceType(name="Database"))
    if (
        TaskSourceType.query.filter_by(name="Network File (SMB Connection)").first()
        is None
    ):
        db.session.add(TaskSourceType(name="Network File (SMB Connection)"))
    if TaskSourceType.query.filter_by(name="File (SFTP Connection)").first() is None:
        db.session.add(TaskSourceType(name="File (SFTP Connection)"))
    if TaskSourceType.query.filter_by(name="File (FTP Connection)").first() is None:
        db.session.add(TaskSourceType(name="File (FTP Connection)"))
    if TaskSourceType.query.filter_by(name="Python Script").first() is None:
        db.session.add(TaskSourceType(name="Python Script"))
    if TaskSourceType.query.filter_by(name="SSH Command").first() is None:
        db.session.add(TaskSourceType(name="SSH Command"))

    # task processing type
    if (
        TaskProcessingType.query.filter_by(name="Network File (SMB Connection)").first()
        is None
    ):
        db.session.add(TaskProcessingType(name="Network File (SMB Connection)"))
    if (
        TaskProcessingType.query.filter_by(name="File (SFTP Connection)").first()
        is None
    ):
        db.session.add(TaskProcessingType(name="File (SFTP Connection)"))
    if TaskProcessingType.query.filter_by(name="File (FTP Connection)").first() is None:
        db.session.add(TaskProcessingType(name="File (FTP Connection)"))
    if TaskProcessingType.query.filter_by(name="Git URL").first() is None:
        db.session.add(TaskProcessingType(name="Git URL"))
    if TaskProcessingType.query.filter_by(name="Other URL (no auth)").first() is None:
        db.session.add(TaskProcessingType(name="Other URL (no auth)"))
    if TaskProcessingType.query.filter_by(name="Source Code").first() is None:
        db.session.add(TaskProcessingType(name="Source Code"))

    # task source query type
    if TaskSourceQueryType.query.filter_by(name="Git URL").first() is None:
        db.session.add(TaskSourceQueryType(name="Git URL"))
    if (
        TaskSourceQueryType.query.filter_by(name="File Path (SMB Connection)").first()
        is None
    ):
        db.session.add(TaskSourceQueryType(name="File Path (SMB Connection)"))
    if TaskSourceQueryType.query.filter_by(name="Other URL (no auth)").first() is None:
        db.session.add(TaskSourceQueryType(name="Other URL (no auth)"))
    if TaskSourceQueryType.query.filter_by(name="Source Code").first() is None:
        db.session.add(TaskSourceQueryType(name="Source Code"))
    if (
        TaskSourceQueryType.query.filter_by(name="File Path (SFTP Connection)").first()
        is None
    ):
        db.session.add(TaskSourceQueryType(name="File Path (SFTP Connection)"))
    if (
        TaskSourceQueryType.query.filter_by(name="File Path (FTP Connection)").first()
        is None
    ):
        db.session.add(TaskSourceQueryType(name="File Path (FTP Connection)"))

    # database type
    if ConnectionDatabaseType.query.filter_by(name="Postgres").first() is None:
        db.session.add(ConnectionDatabaseType(name="Postgres"))
    if ConnectionDatabaseType.query.filter_by(name="SQL Sever").first() is None:
        db.session.add(ConnectionDatabaseType(name="SQL Sever"))

    # file types
    if (
        TaskDestinationFileType.query.filter_by(name="CSV (.csv)", ext="csv").first()
        is None
    ):
        db.session.add(TaskDestinationFileType(name="CSV (.csv)", ext="csv"))
    if (
        TaskDestinationFileType.query.filter_by(name="Text (.txt)", ext="txt").first()
        is None
    ):
        db.session.add(TaskDestinationFileType(name="Text (.txt)", ext="txt"))
    if (
        TaskDestinationFileType.query.filter_by(name="Excel (.csv)", ext="csv").first()
        is None
    ):
        db.session.add(TaskDestinationFileType(name="Excel (.csv)", ext="csv"))
    if (
        TaskDestinationFileType.query.filter_by(
            name="Other (specify in filename)", ext=""
        ).first()
        is None
    ):
        db.session.add(
            TaskDestinationFileType(name="Other (specify in filename)", ext="")
        )

    # task status
    if TaskStatus.query.filter_by(name="Running").first() is None:
        db.session.add(TaskStatus(name="Running"))
    if TaskStatus.query.filter_by(name="Errored").first() is None:
        db.session.add(TaskStatus(name="Errored"))
    if TaskStatus.query.filter_by(name="Stopped").first() is None:
        db.session.add(TaskStatus(name="Stopped"))
    if TaskStatus.query.filter_by(name="Completed").first() is None:
        db.session.add(TaskStatus(name="Completed"))
    if TaskStatus.query.filter_by(name="Starting").first() is None:
        db.session.add(TaskStatus(name="Starting"))
    if TaskStatus.query.filter_by(name="Scheduler").first() is None:
        db.session.add(TaskStatus(name="Scheduler"))
    if TaskStatus.query.filter_by(name="User").first() is None:
        db.session.add(TaskStatus(name="User"))
    if TaskStatus.query.filter_by(name="Runner").first() is None:
        db.session.add(TaskStatus(name="Runner"))
    if TaskStatus.query.filter_by(name="SFTP").first() is None:
        db.session.add(TaskStatus(name="SFTP"))
    if TaskStatus.query.filter_by(name="SMB").first() is None:
        db.session.add(TaskStatus(name="SMB"))
    if TaskStatus.query.filter_by(name="File").first() is None:
        db.session.add(TaskStatus(name="File"))
    if TaskStatus.query.filter_by(name="Email").first() is None:
        db.session.add(TaskStatus(name="Email"))
    if TaskStatus.query.filter_by(name="FTP").first() is None:
        db.session.add(TaskStatus(name="FTP"))
    if TaskStatus.query.filter_by(name="Py Processer").first() is None:
        db.session.add(TaskStatus(name="Py Processer"))
    if TaskStatus.query.filter_by(name="Git/Web Code").first() is None:
        db.session.add(TaskStatus(name="Git/Web Code"))
    if TaskStatus.query.filter_by(name="Date Parser").first() is None:
        db.session.add(TaskStatus(name="Date Parser"))
    if TaskStatus.query.filter_by(name="Cmd Runner").first() is None:
        db.session.add(TaskStatus(name="Cmd Runner"))
    if TaskStatus.query.filter_by(name="System").first() is None:
        db.session.add(TaskStatus(name="System"))
    if TaskStatus.query.filter_by(name="SSH").first() is None:
        db.session.add(TaskStatus(name="SSH"))
    if TaskStatus.query.filter_by(name="SQL Server").first() is None:
        db.session.add(TaskStatus(name="SQL Server"))
    if TaskStatus.query.filter_by(name="Postgres").first() is None:
        db.session.add(TaskStatus(name="Postgres"))

    db.session.commit()


def seed_demo():
    """Seed info for demo."""
    # demo user
    if User.query.filter_by(full_name="Mr Cool", user_id="1234").first() is None:
        db.session.add(User(full_name="Mr Cool", user_id="1234"))

    # demo db
    if (
        ConnectionDatabase.query.filter_by(
            name="Public Database",
            type_id=1,
            connection_string=(
                "host=hh-pgsql-public.ebi.ac.uk"
                + " dbname=pfmegrnargs user=reader password=NWDMCE5xdipIjRrp"
            ),
            connection_id=1,
        ).first()
        is None
    ):
        db.session.add(
            ConnectionDatabase(
                name="Public Database",
                type_id=1,
                connection_string=(
                    "host=hh-pgsql-public.ebi.ac.uk"
                    + " dbname=pfmegrnargs user=reader password=NWDMCE5xdipIjRrp"
                ),
                connection_id=1,
            )
        )

    # demo connection group
    if (
        Connection.query.filter_by(
            name="Extract Organization",
            description="The best place to send data.",
            address="Organization Extract",
            primary_contact="Boss Man",
            primary_contact_email="boss@ma.n",
            primary_contact_phone="(000)-000-0000",
        ).first()
        is None
    ):
        db.session.add(
            Connection(
                name="Extract Organization",
                description="The best place to send data.",
                address="Organization Extract",
                primary_contact="Boss Man",
                primary_contact_email="boss@ma.n",
                primary_contact_phone="(000)-000-0000",
            )
        )

    # demo ftp connection (ro)
    if (
        ConnectionFtp.query.filter_by(  # noqa: S106
            connection_id=1,
            name="Speed Test Tele2",
            address="speedtest.tele2.net/",
            path="/upload/",
            username="anonymous",
            password="anonymous",
        ).first()
        is None
    ):
        db.session.add(
            ConnectionFtp(  # noqa: S106
                connection_id=1,
                name="Speed Test Tele2",
                address="speedtest.tele2.net/",
                path="/upload/",
                username="anonymous",
                password="anonymous",
            )
        )

    # demo project
    if (
        Project.query.filter_by(
            name="Demo Project",
            description="This description must be the best.",
            owner_id=1,
            creator_id=1,
            updater_id=1,
            intv=1,
            intv_type="m",
            intv_value="1",
        ).first()
        is None
    ):
        db.session.add(
            Project(
                name="Demo Project",
                description="This description must be the best.",
                owner_id=1,
                creator_id=1,
                updater_id=1,
                intv=1,
                intv_type="m",
                intv_value="1",
            )
        )

    # demo task
    if (
        Task.query.filter_by(
            name="Task 1",
            source_type_id=1,
            source_code="select " "1" "",
            destination_ftp=1,
            destination_ftp_id=1,
            project_id=1,
            source_query_type_id=4,
            source_database_id=1,
            enabled=1,
            destination_file_name="test_%d_%m",
            destination_file_type_id=2,
            destination_file_delimiter="|",
        ).first()
        is None
    ):
        db.session.add(
            Task(
                name="Task 1",
                source_type_id=1,
                source_code="select " "1" "",
                destination_ftp=1,
                destination_ftp_id=1,
                project_id=1,
                source_query_type_id=4,
                source_database_id=1,
                enabled=1,
                destination_file_name="test_%d_%m",
                destination_file_type_id=2,
                destination_file_delimiter="|",
            )
        )

    db.session.commit()
