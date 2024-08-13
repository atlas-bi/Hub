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
from typing import List, Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import functions

from .extensions import (
    db,
    intpk,
    str_5,
    str_10,
    str_30,
    str_120,
    str_200,
    str_400,
    str_500,
    str_1000,
    str_8000,
    timestamp,
)


class LoginType(db.Model):
    """Lookup table of user login types."""

    __tablename__ = "login_type"

    id: Mapped[intpk]
    name: Mapped[Optional[str_120]]
    login: Mapped[List["Login"]] = relationship(back_populates="login_type", lazy=True)


class Login(db.Model):
    """Table should contain all login attempts."""

    __tablename__ = "login"

    id: Mapped[intpk]
    type_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(LoginType.id))
    username: Mapped[Optional[str_120]]
    login_date: Mapped[Optional[timestamp]]
    login_type: Mapped["LoginType"] = relationship(back_populates="login")


class User(db.Model):
    """Table containing any user-specific information."""

    # pylint: disable=too-many-instance-attributes

    id: Mapped[intpk]
    account_name: Mapped[Optional[str_200]] = mapped_column(index=True)
    email: Mapped[Optional[str_200]] = mapped_column(index=True)
    full_name: Mapped[Optional[str_200]]
    first_name: Mapped[Optional[str_200]]
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


class Project(db.Model):
    """Table containing project details."""

    # pylint: disable=too-many-instance-attributes

    id: Mapped[intpk]
    name: Mapped[Optional[str_120]]
    description: Mapped[Optional[str_8000]]
    owner_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(User.id), index=True)

    cron: Mapped[Optional[int]]
    cron_year: Mapped[Optional[str_120]]
    cron_month: Mapped[Optional[str_120]]
    cron_week: Mapped[Optional[str_120]]
    cron_day: Mapped[Optional[str_120]]
    cron_week_day: Mapped[Optional[str_120]]
    cron_hour: Mapped[Optional[str_120]]
    cron_min: Mapped[Optional[str_120]]
    cron_sec: Mapped[Optional[str_120]]
    cron_start_date: Mapped[Optional[datetime.datetime]]
    cron_end_date: Mapped[Optional[datetime.datetime]]

    intv: Mapped[Optional[int]]
    intv_type: Mapped[Optional[str_5]]
    intv_value: Mapped[Optional[int]]
    intv_start_date: Mapped[Optional[datetime.datetime]]
    intv_end_date: Mapped[Optional[datetime.datetime]]
    ooff: Mapped[Optional[int]]
    ooff_date: Mapped[Optional[datetime.datetime]]

    global_params: Mapped[Optional[str_8000]]
    sequence_tasks: Mapped[Optional[int]]

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

    created: Mapped[Optional[timestamp]]
    creator_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(User.id), index=True)
    updated: Mapped[Optional[datetime.datetime]] = mapped_column(onupdate=functions.now())
    updater_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(User.id), index=True)

    def __str__(self) -> str:
        """Return default string."""
        return str(self.name)


class TaskSourceType(db.Model):
    """Lookup table of task source types."""

    __tablename__ = "task_source_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str_120]]
    task: Mapped["Task"] = relationship(backref="source_type", lazy=True)


class TaskSourceQueryType(db.Model):
    """Lookup table of task query source types."""

    __tablename__ = "task_source_query_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str_120]]
    task: Mapped["Task"] = relationship(backref="query_type", lazy=True)


class TaskProcessingType(db.Model):
    """Lookup table of task query source types."""

    __tablename__ = "task_processing_type"

    id: Mapped[intpk]
    name: Mapped[Optional[str_120]]
    task: Mapped["Task"] = relationship(backref="processing_type", lazy=True)


class TaskStatus(db.Model):
    """Lookup table of task status types.

    This table can link back to a task status, or a task log status.
    """

    __tablename__ = "task_status"

    id: Mapped[intpk]
    name: Mapped[Optional[str_1000]]
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


class Connection(db.Model):
    """Table containing all destination information."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection"

    id: Mapped[intpk]
    name: Mapped[Optional[str_120]]
    description: Mapped[Optional[str_120]]
    address: Mapped[Optional[str_120]]
    primary_contact: Mapped[Optional[str_400]]
    primary_contact_email: Mapped[Optional[str_120]]
    primary_contact_phone: Mapped[Optional[str_120]]
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


class ConnectionSftp(db.Model):
    """Table conntaining sftp connection strings."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection_sftp"

    id: Mapped[intpk]
    connection_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(Connection.id), index=True)
    name: Mapped[Optional[str_500]]
    address: Mapped[Optional[str_500]]
    port: Mapped[Optional[int]]
    path: Mapped[Optional[str_500]]
    username: Mapped[Optional[str_120]]
    key: Mapped[Optional[str_8000]]
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


class ConnectionSsh(db.Model):
    """Table conntaining ssh connection strings."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection_ssh"

    id: Mapped[intpk]
    connection_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(Connection.id), index=True)
    name: Mapped[Optional[str_500]]
    address: Mapped[Optional[str_500]]
    port: Mapped[Optional[int]]
    username: Mapped[Optional[str_120]]
    password: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    task_source: Mapped["Task"] = relationship(
        backref="source_ssh_conn",
        lazy=True,
        foreign_keys="Task.source_ssh_id",
    )

    def __str__(self) -> str:
        """Get string of name."""
        return str(self.name)


class ConnectionGpg(db.Model):
    """Table conntaining gpg keys."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection_gpg"

    id: Mapped[intpk]
    connection_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(Connection.id), index=True)
    name: Mapped[Optional[str_500]]
    key: Mapped[Optional[str_8000]]
    task_source: Mapped["Task"] = relationship(
        backref="file_gpg_conn",
        lazy=True,
        foreign_keys="Task.file_gpg_id",
    )

    def __str__(self) -> str:
        """Get string of name."""
        return str(self.name)


class ConnectionFtp(db.Model):
    """Table conntaining ftp connection strings."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection_ftp"

    id: Mapped[intpk]
    connection_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(Connection.id), index=True)
    name: Mapped[Optional[str_500]]
    address: Mapped[Optional[str_500]]
    path: Mapped[Optional[str_500]]
    username: Mapped[Optional[str_500]]
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


class ConnectionSmb(db.Model):
    """Table conntaining smb connection strings."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection_smb"

    id: Mapped[intpk]
    connection_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(Connection.id), index=True)
    name: Mapped[Optional[str_120]]
    share_name: Mapped[Optional[str_500]]
    path: Mapped[Optional[str_1000]]
    username: Mapped[Optional[str_500]]
    password: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    server_ip: Mapped[Optional[str_500]]
    server_name: Mapped[Optional[str_500]]
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


class ConnectionDatabaseType(db.Model):
    """Lookup table of task source database types."""

    __tablename__ = "connection_database_type"

    id: Mapped[intpk]
    name: Mapped[Optional[str_120]]
    database: Mapped["ConnectionDatabase"] = relationship(backref="database_type", lazy=True)


class ConnectionDatabase(db.Model):
    """List of task source databases and connection strings."""

    __tablename__ = "connection_database"

    id: Mapped[intpk]
    type_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(ConnectionDatabaseType.id))
    connection_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(Connection.id), index=True)
    name: Mapped[Optional[str_500]]
    connection_string: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    timeout: Mapped[Optional[int]]
    task_source: Mapped["Task"] = relationship(
        backref="source_database_conn",
        lazy=True,
        foreign_keys="Task.source_database_id",
    )
    connection: Mapped["Connection"] = relationship(back_populates="database")

    def __str__(self) -> str:
        """Get string of name."""
        return str(self.name)


class TaskDestinationFileType(db.Model):
    """Lookup table of task destination file types."""

    __tablename__ = "task_destination_file_type"

    id: Mapped[intpk]
    name: Mapped[Optional[str_120]]
    ext: Mapped[Optional[str_120]] = mapped_column(nullable=False)
    task: Mapped["Task"] = relationship(backref="file_type", lazy=True)


class QuoteLevel(db.Model):
    """Lookup table for python quote levels."""

    __tablename__ = "quote_level"

    id: Mapped[intpk]
    name: Mapped[Optional[str_120]]
    task: Mapped["Task"] = relationship(backref="destination_file_quote_level", lazy=True)


class ProjectParam(db.Model):
    """Task parameters."""

    __tablename__ = "project_param"

    id: Mapped[intpk]
    key: Mapped[Optional[str_500]]
    value: Mapped[Optional[str_8000]]
    project_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(Project.id), index=True)
    sensitive: Mapped[Optional[int]] = mapped_column(index=True)


class Task(db.Model):
    """Table containing task details."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "task"

    # general information
    id: Mapped[intpk]
    name: Mapped[Optional[str_1000]]
    project_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(Project.id), index=True)
    status_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(TaskStatus.id))
    enabled: Mapped[Optional[int]] = mapped_column(index=True)
    order: Mapped[Optional[int]] = mapped_column(index=True)
    last_run: Mapped[Optional[datetime.datetime]]
    last_run_job_id: Mapped[Optional[str_30]] = mapped_column(index=True)
    next_run: Mapped[Optional[datetime.datetime]] = mapped_column(index=True)
    created: Mapped[Optional[timestamp]] = mapped_column(index=True)
    creator_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(User.id), index=True)
    updated: Mapped[Optional[datetime.datetime]] = mapped_column(
        onupdate=functions.now(), index=True
    )
    updater_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(User.id), index=True)

    """ data source """
    # db/sftp/smb/ftp
    source_type_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(TaskSourceType.id), index=True
    )

    # source locations

    # git/url/code/sftp/ftp/smb/devops
    source_query_type_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(TaskSourceQueryType.id), index=True
    )
    source_query_include_header: Mapped[Optional[int]]

    source_require_sql_output: Mapped[Optional[int]]
    # source git
    source_git: Mapped[Optional[str_1000]]

    # source devops
    source_devops: Mapped[Optional[str_1000]]

    # source web url
    source_url: Mapped[Optional[str_1000]]

    # source typed code
    source_code: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # cached source query
    source_cache: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    enable_source_cache: Mapped[Optional[int]] = mapped_column(index=True)

    query_smb_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(ConnectionSmb.id), index=True
    )
    query_smb_file: Mapped[Optional[str_1000]]

    query_sftp_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(ConnectionSftp.id), index=True
    )
    query_sftp_file: Mapped[Optional[str_1000]]

    query_ftp_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(ConnectionFtp.id), index=True
    )
    query_ftp_file: Mapped[Optional[str_1000]]

    query_params: Mapped[Optional[str_8000]]

    # source smb sql file
    source_smb_file: Mapped[Optional[str_1000]]
    source_smb_delimiter: Mapped[Optional[str_10]]
    source_smb_ignore_delimiter: Mapped[Optional[int]]
    source_smb_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(ConnectionSmb.id), index=True
    )

    # source ftp sql file
    source_ftp_file: Mapped[Optional[str_1000]]
    source_ftp_delimiter: Mapped[Optional[str_10]]
    source_ftp_ignore_delimiter: Mapped[Optional[int]]
    source_ftp_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(ConnectionFtp.id), index=True
    )

    # source sftp sql file
    source_sftp_file: Mapped[Optional[str_1000]]
    source_sftp_delimiter: Mapped[Optional[str_10]]
    source_sftp_ignore_delimiter: Mapped[Optional[int]]
    source_sftp_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(ConnectionSftp.id), index=True
    )

    # source database
    source_database_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(ConnectionDatabase.id), index=True
    )

    source_ssh_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(ConnectionSsh.id), index=True
    )

    """ processing script source """

    processing_type_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(TaskProcessingType.id))

    processing_smb_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(ConnectionSmb.id), index=True
    )
    processing_smb_file: Mapped[Optional[str_1000]]

    processing_sftp_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(ConnectionSftp.id), index=True
    )
    processing_sftp_file: Mapped[Optional[str_1000]]

    processing_ftp_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(ConnectionFtp.id), index=True
    )
    processing_ftp_file: Mapped[Optional[str_1000]]

    processing_code: Mapped[Optional[str_8000]]
    processing_url: Mapped[Optional[str_1000]]
    processing_git: Mapped[Optional[str_1000]]
    processing_devops: Mapped[Optional[str_1000]]
    processing_command: Mapped[Optional[str_1000]]

    """ destination """

    # destination file
    destination_file_name: Mapped[Optional[str_1000]]
    destination_file_delimiter: Mapped[Optional[str_10]]
    destination_ignore_delimiter: Mapped[Optional[int]]
    destination_file_line_terminator: Mapped[Optional[str_10]]

    # destination zip archive
    destination_create_zip: Mapped[Optional[int]]
    destination_zip_name: Mapped[Optional[str_1000]]

    # csv/txt/other
    destination_file_type_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(TaskDestinationFileType.id)
    )

    # save to sftp server
    destination_sftp: Mapped[Optional[int]] = mapped_column(index=True)
    destination_sftp_overwrite: Mapped[Optional[int]]
    destination_sftp_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(ConnectionSftp.id), index=True
    )
    destination_sftp_dont_send_empty_file: Mapped[Optional[int]]

    # save to ftp server
    destination_ftp: Mapped[Optional[int]] = mapped_column(index=True)
    destination_ftp_overwrite: Mapped[Optional[int]]
    destination_ftp_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(ConnectionFtp.id), index=True
    )
    destination_ftp_dont_send_empty_file: Mapped[Optional[int]]
    # save to smb server
    destination_smb: Mapped[Optional[int]] = mapped_column(index=True)
    destination_smb_overwrite: Mapped[Optional[int]]
    destination_smb_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(ConnectionSmb.id), index=True
    )
    destination_smb_dont_send_empty_file: Mapped[Optional[int]]

    file_gpg: Mapped[Optional[int]] = mapped_column(index=True)
    file_gpg_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(ConnectionGpg.id), index=True)

    destination_quote_level_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey(QuoteLevel.id), index=True
    )

    """ email """
    # completion email
    email_completion: Mapped[Optional[int]] = mapped_column(index=True)
    email_completion_log: Mapped[Optional[int]]
    email_completion_file: Mapped[Optional[int]]
    email_completion_file_embed: Mapped[Optional[int]]
    email_completion_recipients: Mapped[Optional[str_1000]]
    email_completion_subject: Mapped[Optional[str_8000]]
    email_completion_message: Mapped[Optional[str_8000]]
    email_completion_dont_send_empty_file: Mapped[Optional[int]]

    # error email
    email_error: Mapped[Optional[int]]
    email_error_recipients: Mapped[Optional[str_1000]]
    email_error_subject: Mapped[Optional[str_8000]]
    email_error_message: Mapped[Optional[str_8000]]

    # rerun on fail
    max_retries: Mapped[Optional[int]] = mapped_column(index=True)

    est_duration: Mapped[Optional[int]] = mapped_column(index=True)

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

    job_id: Mapped[Optional[str_1000]] = mapped_column(index=True)
    id: Mapped[intpk]
    task_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(Task.id), index=True)
    status_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(TaskStatus.id), index=True)
    message: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    status_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        default=datetime.datetime.now, index=True
    )
    error: Mapped[Optional[int]] = mapped_column(index=True)

    __table_args__ = (db.Index("ix_task_log_status_date_error", "status_date", "error"),)


class TaskFile(db.Model):
    """Table containing paths to task backup files."""

    __tablename__ = "task_file"

    id: Mapped[intpk]
    name: Mapped[Optional[str_1000]] = mapped_column(index=True)
    task_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(Task.id), index=True)
    job_id: Mapped[Optional[str_1000]] = mapped_column(index=True)
    size: Mapped[Optional[str_200]] = mapped_column(index=True)
    path: Mapped[Optional[str_1000]] = mapped_column(index=True)
    file_hash: Mapped[Optional[str_1000]]
    created: Mapped[Optional[datetime.datetime]] = mapped_column(
        default=datetime.datetime.now, index=True
    )

    __table_args__ = (db.Index("ix_task_file_id_task_id_job_id", "id", "task_id", "job_id"),)


class TaskParam(db.Model):
    """Task parameters."""

    __tablename__ = "task_param"

    id: Mapped[intpk]
    key: Mapped[Optional[str_500]]
    value: Mapped[Optional[str_8000]]
    task_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey(Task.id), index=True)
    sensitive: Mapped[Optional[int]] = mapped_column(index=True)
