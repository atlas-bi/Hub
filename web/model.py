"""Data Model.

Model resides in EM Web, but must be copied to :obj:`scheduler` and
:obj:`runner` before running app.

Database migrations are run through a manager script.

.. code-block:: console

    warning, this will use db from prod config.
    poetry run flask --app=web db migrate
    poetry run flask --app=web db upgrade

Sometimes there is a conflict between flask-migrations (Alembic migrations)
and the Postgresql db - Postgres will add some indexes that flask-migrations
doesn't think exist yet.

When this happens just remove the index from the migration file onto the previous
migrations file - so flask-migrations think it has already applied the migration.

"""

import datetime
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import functions

from .extensions import db


@dataclass
class LoginType(db.Model):
    """Lookup table of user login types."""

    __tablename__ = "login_type"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    login: Mapped[List["Login"]] = relationship(back_populates="login_type", lazy=True)


@dataclass
class Login(db.Model):
    """Table should contain all login attempts."""

    __tablename__ = "login"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    type_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(LoginType.id), nullable=True
    )
    username: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    login_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        db.DateTime, server_default=functions.now()
    )
    login_type: Mapped["LoginType"] = relationship(back_populates="login")


@dataclass
class User(db.Model):
    """Table containing any user-specific information."""

    # pylint: disable=too-many-instance-attributes

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    account_name: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
    project_owner: Mapped["Project"] = relationship(
        backref="project_owner", lazy=True, foreign_keys="Project.owner_id"
    )
    project_creator: Mapped["Project"] = relationship(
        backref="project_creator",
        lazy=True,
        foreign_keys="Project.creator_id",
    )
    project_updater: Mapped["Project"] = relationship(
        backref="project_updater",
        lazy=True,
        foreign_keys="Project.updater_id",
    )
    task_creator: Mapped["Task"] = relationship(
        backref="task_creator", lazy=True, foreign_keys="Task.creator_id"
    )
    task_updater: Mapped["Task"] = relationship(
        backref="task_updater", lazy=True, foreign_keys="Task.updater_id"
    )
    is_authenticated = True
    is_active = True
    is_anonymous = False

    def get_id(self) -> str:
        """Convert id to unicode."""
        return str(self.id).encode("utf-8").decode("utf-8")

    def __str__(self) -> str:
        """Return default string."""
        return self.full_name or f"User {self.id}"


@dataclass
class Project(db.Model):
    """Table containing project details."""

    # pylint: disable=too-many-instance-attributes

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(db.String(8000), nullable=True)
    owner_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(User.id), nullable=True, index=True
    )

    cron: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    cron_year: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    cron_month: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    cron_week: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    cron_day: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    cron_week_day: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    cron_hour: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    cron_min: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    cron_sec: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    cron_start_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        db.DateTime, nullable=True
    )
    cron_end_date: Mapped[Optional[datetime.datetime]] = mapped_column(db.DateTime, nullable=True)

    intv: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    intv_type: Mapped[Optional[str]] = mapped_column(db.String(5), nullable=True)
    intv_value: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    intv_start_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        db.DateTime, nullable=True
    )
    intv_end_date: Mapped[Optional[datetime.datetime]] = mapped_column(db.DateTime, nullable=True)

    ooff: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    ooff_date: Mapped[Optional[datetime.datetime]] = mapped_column(db.DateTime, nullable=True)

    global_params: Mapped[Optional[str]] = mapped_column(db.String(8000), nullable=True)

    sequence_tasks: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    task: Mapped[List["Task"]] = relationship(
        backref="project",
        lazy="dynamic",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )

    # projectparams link
    params: Mapped[List["ProjectParam"]] = relationship(
        backref="project",
        lazy=True,
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )

    created: Mapped[Optional[datetime.datetime]] = mapped_column(
        db.DateTime, server_default=functions.now()
    )
    creator_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(User.id), nullable=True, index=True
    )
    updated: Mapped[Optional[datetime.datetime]] = mapped_column(
        db.DateTime, onupdate=functions.now()
    )
    updater_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(User.id), nullable=True, index=True
    )

    def __str__(self) -> str:
        """Return default string."""
        return str(self.name)


@dataclass
class TaskSourceType(db.Model):
    """Lookup table of task source types."""

    __tablename__ = "task_source_type"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    task: Mapped["Task"] = relationship(backref="source_type", lazy=True)


@dataclass
class TaskSourceQueryType(db.Model):
    """Lookup table of task query source types."""

    __tablename__ = "task_source_query_type"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    task: Mapped["Task"] = relationship(backref="query_type", lazy=True)


@dataclass
class TaskProcessingType(db.Model):
    """Lookup table of task query source types."""

    __tablename__ = "task_processing_type"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    task: Mapped["Task"] = relationship(backref="processing_type", lazy=True)


@dataclass
class TaskStatus(db.Model):
    """Lookup table of task status types.

    This table can link back to a task status, or a task log status.
    """

    __tablename__ = "task_status"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)
    task: Mapped[List["Task"]] = relationship(
        backref="status",
        lazy="dynamic",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )
    task_log: Mapped[List["TaskLog"]] = relationship(
        backref="status",
        lazy="dynamic",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )


@dataclass
class Connection(db.Model):
    """Table containing all destination information."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    primary_contact: Mapped[Optional[str]] = mapped_column(db.String(400), nullable=True)
    primary_contact_email: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    primary_contact_phone: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    ssh: Mapped[List["ConnectionSsh"]] = relationship(
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionSsh.connection_id",
    )
    sftp: Mapped[List["ConnectionSftp"]] = relationship(
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionSftp.connection_id",
    )
    ftp: Mapped[List["ConnectionFtp"]] = relationship(
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionFtp.connection_id",
    )
    smb: Mapped[List["ConnectionSmb"]] = relationship(
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionSmb.connection_id",
    )
    database: Mapped[List["ConnectionDatabase"]] = relationship(
        back_populates="connection",
        lazy=True,
    )
    gpg: Mapped[List["ConnectionGpg"]] = relationship(
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionGpg.connection_id",
    )

    def __str__(self) -> str:
        """Get string of name."""
        return str(self.name)


@dataclass
class ConnectionSftp(db.Model):
    """Table conntaining sftp connection strings."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection_sftp"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    connection_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(Connection.id), nullable=True, index=True
    )
    name: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    port: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    path: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    key: Mapped[Optional[str]] = mapped_column(db.String(8000), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    key_password: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    task: Mapped["Task"] = relationship(
        backref="destination_sftp_conn",
        lazy=True,
        foreign_keys="Task.destination_sftp_id",
    )
    task_source: Mapped["Task"] = relationship(
        backref="source_sftp_conn",
        lazy=True,
        foreign_keys="Task.source_sftp_id",
    )
    query_source: Mapped["Task"] = relationship(
        backref="query_sftp_conn", lazy=True, foreign_keys="Task.query_sftp_id"
    )
    processing_source: Mapped["Task"] = relationship(
        backref="processing_sftp_conn",
        lazy=True,
        foreign_keys="Task.processing_sftp_id",
    )

    def __str__(self) -> str:
        """Get string of name."""
        return str(self.name)


@dataclass
class ConnectionSsh(db.Model):
    """Table conntaining sftp connection strings."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection_ssh"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    connection_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(Connection.id), nullable=True, index=True
    )
    name: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    port: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    task_source: Mapped["Task"] = relationship(
        backref="source_ssh_conn",
        lazy=True,
        foreign_keys="Task.source_ssh_id",
    )

    def __str__(self) -> str:
        """Get string of name."""
        return str(self.name)


@dataclass
class ConnectionGpg(db.Model):
    """Table conntaining gpg keys."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection_gpg"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    connection_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(Connection.id), nullable=True, index=True
    )
    name: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    key: Mapped[Optional[str]] = mapped_column(db.String(8000), nullable=True)
    task_source: Mapped["Task"] = relationship(
        backref="file_gpg_conn",
        lazy=True,
        foreign_keys="Task.file_gpg_id",
    )

    def __str__(self) -> str:
        """Get string of name."""
        return str(self.name)


@dataclass
class ConnectionFtp(db.Model):
    """Table conntaining sftp connection strings."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection_ftp"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    connection_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(Connection.id), nullable=True, index=True
    )
    name: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    path: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    task: Mapped["Task"] = relationship(
        backref="destination_ftp_conn",
        lazy=True,
        foreign_keys="Task.destination_ftp_id",
    )
    task_source: Mapped["Task"] = relationship(
        backref="source_ftp_conn", lazy=True, foreign_keys="Task.source_ftp_id"
    )
    query_source: Mapped["Task"] = relationship(
        backref="query_ftp_conn", lazy=True, foreign_keys="Task.query_ftp_id"
    )
    processing_source: Mapped["Task"] = relationship(
        backref="processing_ftp_conn",
        lazy=True,
        foreign_keys="Task.processing_ftp_id",
    )

    def __str__(self) -> str:
        """Get string of name."""
        return str(self.name)


@dataclass
class ConnectionSmb(db.Model):
    """Table conntaining sftp connection strings."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection_smb"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    connection_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(Connection.id), nullable=True, index=True
    )
    name: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    share_name: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    path: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    server_ip: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    server_name: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    task: Mapped["Task"] = relationship(
        backref="destination_smb_conn",
        lazy=True,
        foreign_keys="Task.destination_smb_id",
    )
    task_source: Mapped["Task"] = relationship(
        backref="source_smb_conn", lazy=True, foreign_keys="Task.source_smb_id"
    )
    query_source: Mapped["Task"] = relationship(
        backref="query_smb_conn", lazy=True, foreign_keys="Task.query_smb_id"
    )
    processing_source: Mapped["Task"] = relationship(
        backref="processing_smb_conn",
        lazy=True,
        foreign_keys="Task.processing_smb_id",
    )

    def __str__(self) -> str:
        """Get string of name."""
        return str(self.name)


@dataclass
class ConnectionDatabaseType(db.Model):
    """Lookup table of task source database types."""

    __tablename__ = "connection_database_type"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    database: Mapped["ConnectionDatabase"] = relationship(backref="database_type", lazy=True)


@dataclass
class ConnectionDatabase(db.Model):
    """List of task source databases and connection strings."""

    __tablename__ = "connection_database"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    type_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionDatabaseType.id), nullable=True, index=True
    )
    connection_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(Connection.id), nullable=True, index=True
    )
    name: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    connection_string: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    timeout: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    task_source: Mapped["Task"] = relationship(
        backref="source_database_conn",
        lazy=True,
        foreign_keys="Task.source_database_id",
    )
    connection: Mapped["Connection"] = relationship(back_populates="database")

    def __str__(self) -> str:
        """Get string of name."""
        return str(self.name)


@dataclass
class TaskDestinationFileType(db.Model):
    """Lookup table of task destination file types."""

    __tablename__ = "task_destination_file_type"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    ext: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=False)
    task: Mapped["Task"] = relationship(backref="file_type", lazy=True)


@dataclass
class QuoteLevel(db.Model):
    """Lookup table for python quote levels."""

    __tablename__ = "quote_level"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    task: Mapped["Task"] = relationship(backref="destination_file_quote_level", lazy=True)


@dataclass
class ProjectParam(db.Model):
    """Task parameters."""

    __tablename__ = "project_param"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    key: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    value: Mapped[Optional[str]] = mapped_column(db.String(8000), nullable=True)
    project_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(Project.id), nullable=True, index=True
    )
    sensitive: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)


@dataclass
class Task(db.Model):
    """Table containing task details."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "task"

    # general information
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)
    project_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(Project.id), nullable=True, index=True
    )
    status_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(TaskStatus.id), nullable=True, index=True
    )
    enabled: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)
    order: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)
    last_run: Mapped[Optional[datetime.datetime]] = mapped_column(db.DateTime, nullable=True)
    last_run_job_id: Mapped[Optional[str]] = mapped_column(
        db.String(30), nullable=True, index=True
    )
    next_run: Mapped[Optional[datetime.datetime]] = mapped_column(
        db.DateTime, nullable=True, index=True
    )
    created: Mapped[Optional[datetime.datetime]] = mapped_column(
        db.DateTime, server_default=functions.now(), index=True
    )
    creator_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(User.id), nullable=True, index=True
    )
    updated: Mapped[Optional[datetime.datetime]] = mapped_column(
        db.DateTime, onupdate=functions.now(), index=True
    )
    updater_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(User.id), nullable=True, index=True
    )

    """ data source """
    # db/sftp/smb/ftp
    source_type_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(TaskSourceType.id), nullable=True, index=True
    )

    # source locations

    # git/url/code/sftp/ftp/smb/devops
    source_query_type_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(TaskSourceQueryType.id), nullable=True, index=True
    )
    source_query_include_header: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    source_require_sql_output: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    # source git
    source_git: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)

    # source devops
    source_devops: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)

    # source web url
    source_url: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)

    # source typed code
    source_code: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # cached source query
    source_cache: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    enable_source_cache: Mapped[Optional[int]] = mapped_column(
        db.Integer, nullable=True, index=True
    )

    query_smb_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionSmb.id), nullable=True, index=True
    )
    query_smb_file: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)

    query_sftp_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionSftp.id), nullable=True, index=True
    )
    query_sftp_file: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)

    query_ftp_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionFtp.id), nullable=True, index=True
    )
    query_ftp_file: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)

    query_params: Mapped[Optional[str]] = mapped_column(db.String(8000), nullable=True)

    # source smb sql file
    source_smb_file: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)
    source_smb_delimiter: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    source_smb_ignore_delimiter: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    source_smb_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionSmb.id), nullable=True, index=True
    )

    # source ftp sql file
    source_ftp_file: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)
    source_ftp_delimiter: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    source_ftp_ignore_delimiter: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    source_ftp_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionFtp.id), nullable=True, index=True
    )

    # source sftp sql file
    source_sftp_file: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)
    source_sftp_delimiter: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    source_sftp_ignore_delimiter: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    source_sftp_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionSftp.id), nullable=True, index=True
    )

    # source database
    source_database_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionDatabase.id), nullable=True, index=True
    )

    source_ssh_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionSsh.id), nullable=True, index=True
    )

    """ processing script source """

    processing_type_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(TaskProcessingType.id), nullable=True, index=True
    )

    processing_smb_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionSmb.id), nullable=True, index=True
    )
    processing_smb_file: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)

    processing_sftp_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionSftp.id), nullable=True, index=True
    )
    processing_sftp_file: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)

    processing_ftp_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionFtp.id), nullable=True, index=True
    )
    processing_ftp_file: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)

    processing_code: Mapped[Optional[str]] = mapped_column(db.String(8000), nullable=True)
    processing_url: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)
    processing_git: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)
    processing_devops: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)
    processing_command: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)

    """ destination """

    # destination file
    destination_file_name: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)
    destination_file_delimiter: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    destination_ignore_delimiter: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    destination_file_line_terminator: Mapped[Optional[str]] = mapped_column(
        db.String(10), nullable=True
    )

    # destination zip archive
    destination_create_zip: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    destination_zip_name: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)

    # csv/txt/other
    destination_file_type_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(TaskDestinationFileType.id), nullable=True, index=True
    )

    # save to sftp server
    destination_sftp: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)
    destination_sftp_overwrite: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    destination_sftp_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionSftp.id), nullable=True, index=True
    )
    destination_sftp_dont_send_empty_file: Mapped[Optional[int]] = mapped_column(
        db.Integer, nullable=True
    )

    # save to ftp server
    destination_ftp: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)
    destination_ftp_overwrite: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    destination_ftp_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionFtp.id), nullable=True, index=True
    )
    destination_ftp_dont_send_empty_file: Mapped[Optional[int]] = mapped_column(
        db.Integer, nullable=True
    )

    # save to smb server
    destination_smb: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)
    destination_smb_overwrite: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    destination_smb_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionSmb.id), nullable=True, index=True
    )
    destination_smb_dont_send_empty_file: Mapped[Optional[int]] = mapped_column(
        db.Integer, nullable=True
    )

    file_gpg: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)
    file_gpg_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(ConnectionGpg.id), nullable=True, index=True
    )

    destination_quote_level_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(QuoteLevel.id), nullable=True, index=True
    )

    """ email """
    # completion email
    email_completion: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)
    email_completion_log: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    email_completion_file: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    email_completion_file_embed: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    email_completion_recipients: Mapped[Optional[str]] = mapped_column(
        db.String(1000), nullable=True
    )
    email_completion_subject: Mapped[Optional[str]] = mapped_column(db.String(8000), nullable=True)
    email_completion_message: Mapped[Optional[str]] = mapped_column(db.String(8000), nullable=True)
    email_completion_dont_send_empty_file: Mapped[Optional[int]] = mapped_column(
        db.Integer, nullable=True
    )

    # error email
    email_error: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)
    email_error_recipients: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)
    email_error_subject: Mapped[Optional[str]] = mapped_column(db.String(8000), nullable=True)
    email_error_message: Mapped[Optional[str]] = mapped_column(db.String(8000), nullable=True)

    # rerun on fail
    max_retries: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)

    est_duration: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)

    # tasklog link
    task: Mapped[List["TaskLog"]] = relationship(
        backref="task",
        lazy=True,
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )

    # taskparams link
    params: Mapped[List["TaskParam"]] = relationship(
        backref="task",
        lazy=True,
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )

    # taskfiles link
    files: Mapped[List["TaskFile"]] = relationship(
        backref="task",
        lazy=True,
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )

    def __str__(self) -> str:
        """Return default string."""
        return str(self.name)


class TaskLog(db.Model):
    """Table containing job run history."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "task_log"

    job_id: Mapped[Optional[int]] = mapped_column(db.String(1000), nullable=True, index=True)
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    task_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(Task.id), nullable=True, index=True
    )
    status_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(TaskStatus.id), nullable=True, index=True
    )
    message: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    status_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        db.DateTime, default=datetime.datetime.now, index=True
    )
    error: Mapped[Optional[str]] = mapped_column(db.Integer, nullable=True, index=True)

    __table_args__ = (db.Index("ix_task_log_status_date_error", "status_date", "error"),)


@dataclass
class TaskFile(db.Model):
    """Table containing paths to task backup files."""

    __tablename__ = "task_file"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True, index=True)
    task_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(Task.id), nullable=True, index=True
    )
    job_id: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True, index=True)
    size: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True, index=True)
    path: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True, index=True)
    file_hash: Mapped[Optional[str]] = mapped_column(db.String(1000), nullable=True)
    created: Mapped[Optional[datetime.datetime]] = mapped_column(
        db.DateTime, default=datetime.datetime.now, index=True
    )

    __table_args__ = (db.Index("ix_task_file_id_task_id_job_id", "id", "task_id", "job_id"),)


@dataclass
class TaskParam(db.Model):
    """Task parameters."""

    __tablename__ = "task_param"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, index=True)
    key: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    value: Mapped[Optional[str]] = mapped_column(db.String(8000), nullable=True)
    task_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey(Task.id), nullable=True, index=True
    )
    sensitive: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)
