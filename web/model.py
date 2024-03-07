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
from typing import Optional

from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import functions

from .extensions import db

Base = declarative_base()


@dataclass
class LoginType(db.Model):
    """Lookup table of user login types."""

    __tablename__ = "login_type"
    id: Optional[int] = None
    name: Optional[str] = None

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(120), nullable=True)
    login = db.relationship("Login", backref="login_type", lazy=True)


@dataclass
class Login(db.Model):
    """Table should contain all login attempts."""

    __tablename__ = "login"
    id: Optional[int] = None
    username: Optional[str] = None
    login_date: Optional[datetime.datetime] = None
    type_id: Optional[int] = None

    id = db.Column(db.Integer, primary_key=True, index=True)
    type_id = db.Column(db.Integer, db.ForeignKey(LoginType.id), nullable=True)
    username = db.Column(db.String(120), nullable=True)
    login_date = db.Column(db.DateTime, server_default=functions.now())


@dataclass
class User(db.Model):
    """Table containing any user-specific information."""

    # pylint: disable=too-many-instance-attributes

    id: Optional[int] = None
    account_name: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    first_name: Optional[str] = None

    id = db.Column(db.Integer, primary_key=True, index=True)
    account_name = db.Column(db.String(200), nullable=True, index=True)
    email = db.Column(db.String(200), nullable=True, index=True)
    full_name = db.Column(db.String(200), nullable=True)
    first_name = db.Column(db.String(200), nullable=True)
    project_owner = db.relationship(
        "Project", backref="project_owner", lazy=True, foreign_keys="Project.owner_id"
    )
    project_creator = db.relationship(
        "Project",
        backref="project_creator",
        lazy=True,
        foreign_keys="Project.creator_id",
    )
    project_updater = db.relationship(
        "Project",
        backref="project_updater",
        lazy=True,
        foreign_keys="Project.updater_id",
    )
    task_creator = db.relationship(
        "Task", backref="task_creator", lazy=True, foreign_keys="Task.creator_id"
    )
    task_updater = db.relationship(
        "Task", backref="task_updater", lazy=True, foreign_keys="Task.updater_id"
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

    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None
    cron: Optional[int] = None
    cron_year: Optional[str] = None
    cron_month: Optional[str] = None
    cron_week: Optional[str] = None
    cron_day: Optional[str] = None
    cron_week_day: Optional[str] = None
    cron_hour: Optional[str] = None
    cron_min: Optional[str] = None
    cron_sec: Optional[str] = None
    cron_start_date: Optional[datetime.datetime] = None
    cron_end_date: Optional[datetime.datetime] = None

    intv: Optional[int] = None
    intv_type: Optional[str] = None
    intv_value: Optional[int] = None
    intv_start_date: Optional[datetime.datetime] = None
    intv_end_date: Optional[datetime.datetime] = None

    ooff: Optional[int] = None
    ooff_date: Optional[datetime.datetime] = None

    created: Optional[datetime.datetime] = None
    creator_id: Optional[int] = None
    updated: Optional[datetime.datetime] = None
    updater_id: Optional[int] = None

    global_params: Optional[str] = None

    sequence_tasks: Optional[int] = None

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(120), nullable=True)
    description = db.Column(db.String(8000), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=True, index=True)

    cron = db.Column(db.Integer, nullable=True)
    cron_year = db.Column(db.String(120), nullable=True)
    cron_month = db.Column(db.String(120), nullable=True)
    cron_week = db.Column(db.String(120), nullable=True)
    cron_day = db.Column(db.String(120), nullable=True)
    cron_week_day = db.Column(db.String(120), nullable=True)
    cron_hour = db.Column(db.String(120), nullable=True)
    cron_min = db.Column(db.String(120), nullable=True)
    cron_sec = db.Column(db.String(120), nullable=True)
    cron_start_date = db.Column(db.DateTime, nullable=True)
    cron_end_date = db.Column(db.DateTime, nullable=True)

    intv = db.Column(db.Integer, nullable=True)
    intv_type = db.Column(db.String(5), nullable=True)
    intv_value = db.Column(db.Integer, nullable=True)
    intv_start_date = db.Column(db.DateTime, nullable=True)
    intv_end_date = db.Column(db.DateTime, nullable=True)

    ooff = db.Column(db.Integer, nullable=True)
    ooff_date = db.Column(db.DateTime, nullable=True)

    global_params = db.Column(db.String(8000), nullable=True)

    sequence_tasks = db.Column(db.Integer, nullable=True)

    task = db.relationship(
        "Task",
        backref="project",
        lazy="dynamic",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )

    # projectparams link
    params = db.relationship(
        "ProjectParam",
        backref="project",
        lazy=True,
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )

    created = db.Column(db.DateTime, server_default=functions.now())
    creator_id = db.Column(
        db.Integer, db.ForeignKey(User.id), nullable=True, index=True
    )
    updated = db.Column(db.DateTime, onupdate=functions.now())
    updater_id = db.Column(
        db.Integer, db.ForeignKey(User.id), nullable=True, index=True
    )

    def __str__(self) -> str:
        """Return default string."""
        return str(self.name)


@dataclass
class TaskSourceType(db.Model):
    """Lookup table of task source types."""

    __tablename__ = "task_source_type"
    id: Optional[int] = None
    name: Optional[str] = None

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=True)
    task = db.relationship("Task", backref="source_type", lazy=True)


@dataclass
class TaskSourceQueryType(db.Model):
    """Lookup table of task query source types."""

    __tablename__ = "task_source_query_type"
    id: Optional[int] = None
    name: Optional[str] = None

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=True)
    task = db.relationship("Task", backref="query_type", lazy=True)


@dataclass
class TaskProcessingType(db.Model):
    """Lookup table of task query source types."""

    __tablename__ = "task_processing_type"
    id: Optional[int] = None
    name: Optional[str] = None

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=True)
    task = db.relationship("Task", backref="processing_type", lazy=True)


@dataclass
class TaskStatus(db.Model):
    """Lookup table of task status types.

    This table can link back to a task status, or a task log status.
    """

    __tablename__ = "task_status"
    id: Optional[int] = None
    name: Optional[str] = None

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), nullable=True)
    task = db.relationship(
        "Task",
        backref="status",
        lazy="dynamic",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )
    task_log = db.relationship(
        "TaskLog",
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
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    primary_contact: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(120), nullable=True)
    description = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(120), nullable=True)
    primary_contact = db.Column(db.String(400), nullable=True)
    primary_contact_email = db.Column(db.String(120), nullable=True)
    primary_contact_phone = db.Column(db.String(120), nullable=True)
    ssh = db.relationship(
        "ConnectionSsh",
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionSsh.connection_id",
    )
    sftp = db.relationship(
        "ConnectionSftp",
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionSftp.connection_id",
    )
    ftp = db.relationship(
        "ConnectionFtp",
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionFtp.connection_id",
    )
    smb = db.relationship(
        "ConnectionSmb",
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionSmb.connection_id",
    )
    database = db.relationship(
        "ConnectionDatabase",
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionDatabase.connection_id",
    )
    gpg = db.relationship(
        "ConnectionGpg",
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
    id: Optional[int] = None
    connection_id: Optional[int] = None
    name: Optional[str] = None
    address: Optional[str] = None
    port: Optional[int] = None
    path: Optional[str] = None
    username: Optional[str] = None
    key: Optional[str] = None
    password: Optional[str] = None

    id = db.Column(db.Integer, primary_key=True, index=True)
    connection_id = db.Column(
        db.Integer, db.ForeignKey(Connection.id), nullable=True, index=True
    )
    name = db.Column(db.String(500), nullable=True)
    address = db.Column(db.String(500), nullable=True)
    port = db.Column(db.Integer, nullable=True)
    path = db.Column(db.String(500), nullable=True)
    username = db.Column(db.String(120), nullable=True)
    key = db.Column(db.String(8000), nullable=True)
    password = db.Column(db.Text, nullable=True)
    key_password = db.Column(db.Text, nullable=True)
    task = db.relationship(
        "Task",
        backref="destination_sftp_conn",
        lazy=True,
        foreign_keys="Task.destination_sftp_id",
    )
    task_source = db.relationship(
        "Task",
        backref="source_sftp_conn",
        lazy=True,
        foreign_keys="Task.source_sftp_id",
    )
    query_source = db.relationship(
        "Task", backref="query_sftp_conn", lazy=True, foreign_keys="Task.query_sftp_id"
    )
    processing_source = db.relationship(
        "Task",
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
    id: Optional[int] = None
    connection_id: Optional[int] = None
    name: Optional[str] = None
    address: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None

    id = db.Column(db.Integer, primary_key=True, index=True)
    connection_id = db.Column(
        db.Integer, db.ForeignKey(Connection.id), nullable=True, index=True
    )
    name = db.Column(db.String(500), nullable=True)
    address = db.Column(db.String(500), nullable=True)
    port = db.Column(db.Integer, nullable=True)
    username = db.Column(db.String(120), nullable=True)
    password = db.Column(db.Text, nullable=True)
    task_source = db.relationship(
        "Task",
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
    id: Optional[int] = None
    connection_id: Optional[int] = None
    name: Optional[str] = None
    key: Optional[str] = None

    id = db.Column(db.Integer, primary_key=True, index=True)
    connection_id = db.Column(
        db.Integer, db.ForeignKey(Connection.id), nullable=True, index=True
    )
    name = db.Column(db.String(500), nullable=True)
    key = db.Column(db.String(8000), nullable=True)
    task_source = db.relationship(
        "Task",
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
    id: Optional[int] = None
    connection_id: Optional[int] = None
    name: Optional[str] = None
    address: Optional[str] = None
    path: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

    id = db.Column(db.Integer, primary_key=True, index=True)
    connection_id = db.Column(
        db.Integer, db.ForeignKey(Connection.id), nullable=True, index=True
    )
    name = db.Column(db.String(500), nullable=True)
    address = db.Column(db.String(500), nullable=True)
    path = db.Column(db.String(500), nullable=True)
    username = db.Column(db.String(500), nullable=True)
    password = db.Column(db.Text, nullable=True)
    task = db.relationship(
        "Task",
        backref="destination_ftp_conn",
        lazy=True,
        foreign_keys="Task.destination_ftp_id",
    )
    task_source = db.relationship(
        "Task", backref="source_ftp_conn", lazy=True, foreign_keys="Task.source_ftp_id"
    )
    query_source = db.relationship(
        "Task", backref="query_ftp_conn", lazy=True, foreign_keys="Task.query_ftp_id"
    )
    processing_source = db.relationship(
        "Task",
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
    id: Optional[int] = None
    connection_id: Optional[int] = None
    name: Optional[str] = None
    share_name: Optional[str] = None
    path: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    server_ip: Optional[str] = None
    server_name: Optional[str] = None

    id = db.Column(db.Integer, primary_key=True, index=True)
    connection_id = db.Column(
        db.Integer, db.ForeignKey(Connection.id), nullable=True, index=True
    )
    name = db.Column(db.String(120), nullable=True)
    share_name = db.Column(db.String(500), nullable=True)
    path = db.Column(db.String(1000), nullable=True)
    username = db.Column(db.String(500), nullable=True)
    password = db.Column(db.Text, nullable=True)
    server_ip = db.Column(db.String(500), nullable=True)
    server_name = db.Column(db.String(500), nullable=True)
    task = db.relationship(
        "Task",
        backref="destination_smb_conn",
        lazy=True,
        foreign_keys="Task.destination_smb_id",
    )
    task_source = db.relationship(
        "Task", backref="source_smb_conn", lazy=True, foreign_keys="Task.source_smb_id"
    )
    query_source = db.relationship(
        "Task", backref="query_smb_conn", lazy=True, foreign_keys="Task.query_smb_id"
    )
    processing_source = db.relationship(
        "Task",
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
    id: Optional[int] = None
    name: Optional[str] = None

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=True)
    database = db.relationship("ConnectionDatabase", backref="database_type", lazy=True)


@dataclass
class ConnectionDatabase(db.Model):
    """List of task source databases and connection strings."""

    __tablename__ = "connection_database"
    id: Optional[int] = None
    type_id: Optional[int] = None
    name: Optional[str] = None
    connection_string: Optional[str] = None
    connection_id: Optional[int] = None
    timeout: Optional[int] = None

    id = db.Column(db.Integer, primary_key=True, index=True)
    type_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionDatabaseType.id), nullable=True, index=True
    )
    connection_id = db.Column(
        db.Integer, db.ForeignKey(Connection.id), nullable=True, index=True
    )
    name = db.Column(db.String(500), nullable=True)
    connection_string = db.Column(db.Text, nullable=True)
    timeout = db.Column(db.Integer, nullable=True)
    task_source = db.relationship(
        "Task",
        backref="source_database_conn",
        lazy=True,
        foreign_keys="Task.source_database_id",
    )

    def __str__(self) -> str:
        """Get string of name."""
        return str(self.name)


@dataclass
class TaskDestinationFileType(db.Model):
    """Lookup table of task destination file types."""

    __tablename__ = "task_destination_file_type"
    id: Optional[int] = None
    name: Optional[str] = None
    ext: Optional[str] = None

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=True)
    ext = db.Column(db.String(120), nullable=False)
    task = db.relationship("Task", backref="file_type", lazy=True)


@dataclass
class QuoteLevel(db.Model):
    """Lookup table for python quote levels."""

    __tablename__ = "quote_level"
    id: Optional[int] = None
    name: Optional[str] = None

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(120), nullable=True)
    task = db.relationship("Task", backref="destination_file_quote_level", lazy=True)


@dataclass
class ProjectParam(db.Model):
    """Task parameters."""

    __tablename__ = "project_param"
    id: Optional[int] = None
    key: Optional[str] = None
    value: Optional[str] = None
    sensitive: Optional[int] = None
    project_id: Optional[int] = None

    id = db.Column(db.Integer, primary_key=True, index=True)
    key = db.Column(db.String(500), nullable=True)
    value = db.Column(db.String(8000), nullable=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey(Project.id), nullable=True, index=True
    )
    sensitive = db.Column(db.Integer, nullable=True, index=True)


@dataclass
class Task(db.Model):
    """Table containing task details."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "task"
    # general information
    id: Optional[int] = None
    name: Optional[str] = None
    project_id: Optional[int] = None
    status_id: Optional[int] = None
    enabled: Optional[int] = None
    order: Optional[int] = None
    last_run: Optional[datetime.datetime] = None
    next_run: Optional[datetime.datetime] = None
    last_run_job_id: Optional[str] = None
    created: Optional[datetime.datetime] = None
    creator_id: Optional[int] = None
    updated: Optional[datetime.datetime] = None
    updater_id: Optional[int] = None

    # data source
    source_type_id: Optional[int] = None
    source_database_id: Optional[int] = None

    source_query_type_id: Optional[int] = None
    source_query_include_header: Optional[int] = None
    source_git: Optional[str] = None
    source_devops: Optional[str] = None
    source_url: Optional[str] = None
    source_code: Optional[str] = None

    source_require_sql_output: Optional[int] = None

    query_smb_id: Optional[int] = None
    query_smb_file: Optional[str] = None
    query_sftp_id: Optional[int] = None
    query_sftp_file: Optional[str] = None
    query_ftp_id: Optional[int] = None
    query_ftp_file: Optional[str] = None
    query_params: Optional[str] = None

    source_smb_delimiter: Optional[str] = None
    source_smb_ignore_delimiter: Optional[int] = None
    source_smb_file: Optional[str] = None
    source_smb_id: Optional[int] = None

    source_ftp_file: Optional[str] = None
    source_ftp_delimiter: Optional[str] = None
    source_ftp_ignore_delimiter: Optional[int] = None
    source_ftp_id: Optional[int] = None

    source_sftp_file: Optional[str] = None
    source_sftp_delimiter: Optional[str] = None
    source_sftp_ignore_delimiter: Optional[int] = None
    source_sftp_id: Optional[int] = None

    source_ssh_id: Optional[int] = None

    # caching
    source_cache: Optional[str] = None
    enable_source_cache: Optional[int] = None

    # processing
    processing_type_id: Optional[int] = None
    processing_smb_id: Optional[int] = None
    processing_smb_file: Optional[str] = None
    processing_sftp_id: Optional[int] = None
    processing_sftp_file: Optional[str] = None
    processing_ftp_id: Optional[int] = None
    processing_ftp_file: Optional[str] = None
    processing_code: Optional[str] = None
    processing_url: Optional[str] = None
    processing_git: Optional[str] = None
    processing_devops: Optional[str] = None
    processing_command: Optional[str] = None

    # destination
    destination_file_delimiter: Optional[str] = None
    destination_file_name: Optional[str] = None
    destination_ignore_delimiter: Optional[int] = None
    destination_file_line_terminator: Optional[str] = None
    destination_quote_level_id: Optional[int] = None

    destination_create_zip: Optional[int] = None
    destination_zip_name: Optional[str] = None

    destination_file_type_id: Optional[int] = None

    destination_sftp: Optional[int] = None
    destination_sftp_overwrite: Optional[int] = None
    destination_sftp_id: Optional[int] = None
    destination_sftp_dont_send_empty_file: Optional[int] = None

    destination_ftp: Optional[int] = None
    destination_ftp_overwrite: Optional[int] = None
    destination_ftp_id: Optional[int] = None
    destination_ftp_dont_send_empty_file: Optional[int] = None

    destination_smb: Optional[int] = None
    destination_smb_overwrite: Optional[int] = None
    destination_smb_id: Optional[int] = None
    destination_smb_dont_send_empty_file: Optional[int] = None

    file_gpg: Optional[int] = None
    file_gpg_id: Optional[int] = None

    email_completion: Optional[int] = None
    email_completion_log: Optional[int] = None
    email_completion_file: Optional[int] = None
    email_completion_file_embed: Optional[int] = None
    email_completion_dont_send_empty_file: Optional[int] = None
    email_completion_recipients: Optional[str] = None
    email_completion_message: Optional[str] = None

    email_error: Optional[int] = None
    email_error_recipients: Optional[str] = None
    email_error_message: Optional[str] = None

    max_retries: Optional[int] = None

    est_duration: Optional[int] = None

    # general information
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(1000), nullable=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey(Project.id), nullable=True, index=True
    )
    status_id = db.Column(
        db.Integer, db.ForeignKey(TaskStatus.id), nullable=True, index=True
    )
    enabled = db.Column(db.Integer, nullable=True, index=True)
    order = db.Column(db.Integer, nullable=True, index=True)
    last_run = db.Column(db.DateTime, nullable=True)
    last_run_job_id = db.Column(db.String(30), nullable=True, index=True)
    next_run = db.Column(db.DateTime, nullable=True, index=True)
    created = db.Column(db.DateTime, server_default=functions.now(), index=True)
    creator_id = db.Column(
        db.Integer, db.ForeignKey(User.id), nullable=True, index=True
    )
    updated = db.Column(db.DateTime, onupdate=functions.now(), index=True)
    updater_id = db.Column(
        db.Integer, db.ForeignKey(User.id), nullable=True, index=True
    )

    """ data source """
    # db/sftp/smb/ftp
    source_type_id = db.Column(
        db.Integer, db.ForeignKey(TaskSourceType.id), nullable=True, index=True
    )

    # source locations

    # git/url/code/sftp/ftp/smb/devops
    source_query_type_id = db.Column(
        db.Integer, db.ForeignKey(TaskSourceQueryType.id), nullable=True, index=True
    )
    source_query_include_header = db.Column(db.Integer, nullable=True)

    source_require_sql_output = db.Column(db.Integer, nullable=True)
    # source git
    source_git = db.Column(db.String(1000), nullable=True)

    # source devops
    source_devops = db.Column(db.String(1000), nullable=True)

    # source web url
    source_url = db.Column(db.String(1000), nullable=True)

    # source typed code
    source_code = db.Column(db.Text, nullable=True)

    # cached source query
    source_cache = db.Column(db.Text, nullable=True)
    enable_source_cache = db.Column(db.Integer, nullable=True, index=True)

    query_smb_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSmb.id), nullable=True, index=True
    )
    query_smb_file = db.Column(db.String(1000), nullable=True)

    query_sftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSftp.id), nullable=True, index=True
    )
    query_sftp_file = db.Column(db.String(1000), nullable=True)

    query_ftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionFtp.id), nullable=True, index=True
    )
    query_ftp_file = db.Column(db.String(1000), nullable=True)

    query_params = db.Column(db.String(8000), nullable=True)

    # source smb sql file
    source_smb_file = db.Column(db.String(1000), nullable=True)
    source_smb_delimiter = db.Column(db.String(10), nullable=True)
    source_smb_ignore_delimiter = db.Column(db.Integer, nullable=True)
    source_smb_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSmb.id), nullable=True, index=True
    )

    # source ftp sql file
    source_ftp_file = db.Column(db.String(1000), nullable=True)
    source_ftp_delimiter = db.Column(db.String(10), nullable=True)
    source_ftp_ignore_delimiter = db.Column(db.Integer, nullable=True)
    source_ftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionFtp.id), nullable=True, index=True
    )

    # source sftp sql file
    source_sftp_file = db.Column(db.String(1000), nullable=True)
    source_sftp_delimiter = db.Column(db.String(10), nullable=True)
    source_sftp_ignore_delimiter = db.Column(db.Integer, nullable=True)
    source_sftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSftp.id), nullable=True, index=True
    )

    # source database
    source_database_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionDatabase.id), nullable=True, index=True
    )

    source_ssh_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSsh.id), nullable=True, index=True
    )

    """ processing script source """

    processing_type_id = db.Column(
        db.Integer, db.ForeignKey(TaskProcessingType.id), nullable=True, index=True
    )

    processing_smb_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSmb.id), nullable=True, index=True
    )
    processing_smb_file = db.Column(db.String(1000), nullable=True)

    processing_sftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSftp.id), nullable=True, index=True
    )
    processing_sftp_file = db.Column(db.String(1000), nullable=True)

    processing_ftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionFtp.id), nullable=True, index=True
    )
    processing_ftp_file = db.Column(db.String(1000), nullable=True)

    processing_code = db.Column(db.String(8000), nullable=True)
    processing_url = db.Column(db.String(1000), nullable=True)
    processing_git = db.Column(db.String(1000), nullable=True)
    processing_devops = db.Column(db.String(1000), nullable=True)
    processing_command = db.Column(db.String(1000), nullable=True)

    """ destination """

    # destination file
    destination_file_name = db.Column(db.String(1000), nullable=True)
    destination_file_delimiter = db.Column(db.String(10), nullable=True)
    destination_ignore_delimiter = db.Column(db.Integer, nullable=True)
    destination_file_line_terminator = db.Column(db.String(10), nullable=True)

    # destination zip archive
    destination_create_zip = db.Column(db.Integer, nullable=True)
    destination_zip_name = db.Column(db.String(1000), nullable=True)

    # csv/txt/other
    destination_file_type_id = db.Column(
        db.Integer, db.ForeignKey(TaskDestinationFileType.id), nullable=True, index=True
    )

    # save to sftp server
    destination_sftp = db.Column(db.Integer, nullable=True, index=True)
    destination_sftp_overwrite = db.Column(db.Integer, nullable=True)
    destination_sftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSftp.id), nullable=True, index=True
    )
    destination_sftp_dont_send_empty_file = db.Column(db.Integer, nullable=True)

    # save to ftp server
    destination_ftp = db.Column(db.Integer, nullable=True, index=True)
    destination_ftp_overwrite = db.Column(db.Integer, nullable=True)
    destination_ftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionFtp.id), nullable=True, index=True
    )
    destination_ftp_dont_send_empty_file = db.Column(db.Integer, nullable=True)

    # save to smb server
    destination_smb = db.Column(db.Integer, nullable=True, index=True)
    destination_smb_overwrite = db.Column(db.Integer, nullable=True)
    destination_smb_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSmb.id), nullable=True, index=True
    )
    destination_smb_dont_send_empty_file = db.Column(db.Integer, nullable=True)

    file_gpg = db.Column(db.Integer, nullable=True, index=True)
    file_gpg_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionGpg.id), nullable=True, index=True
    )

    destination_quote_level_id = db.Column(
        db.Integer, db.ForeignKey(QuoteLevel.id), nullable=True, index=True
    )

    """ email """
    # completion email
    email_completion = db.Column(db.Integer, nullable=True, index=True)
    email_completion_log = db.Column(db.Integer, nullable=True)
    email_completion_file = db.Column(db.Integer, nullable=True)
    email_completion_file_embed = db.Column(db.Integer, nullable=True)
    email_completion_recipients = db.Column(db.String(1000), nullable=True)
    email_completion_subject = db.Column(db.String(8000), nullable=True)
    email_completion_message = db.Column(db.String(8000), nullable=True)
    email_completion_dont_send_empty_file = db.Column(db.Integer, nullable=True)

    # error email
    email_error = db.Column(db.Integer, nullable=True, index=True)
    email_error_recipients = db.Column(db.String(1000), nullable=True)
    email_error_subject = db.Column(db.String(8000), nullable=True)
    email_error_message = db.Column(db.String(8000), nullable=True)

    # rerun on fail
    max_retries = db.Column(db.Integer, nullable=True, index=True)

    est_duration = db.Column(db.Integer, nullable=True, index=True)

    # tasklog link
    task = db.relationship(
        "TaskLog",
        backref="task",
        lazy=True,
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )

    # taskparams link
    params = db.relationship(
        "TaskParam",
        backref="task",
        lazy=True,
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )

    # taskfiles link
    files = db.relationship(
        "TaskFile",
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
    id: Optional[int] = None
    task_id: Optional[int] = None
    status_id: Optional[int] = None
    job_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[int] = 0
    status_date: Optional[datetime.datetime] = None

    job_id = db.Column(db.String(1000), nullable=True, index=True)
    id = db.Column(db.Integer, primary_key=True, index=True)
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id), nullable=True, index=True)
    status_id = db.Column(
        db.Integer, db.ForeignKey(TaskStatus.id), nullable=True, index=True
    )
    message = db.Column(db.Text, nullable=True)
    status_date = db.Column(db.DateTime, default=datetime.datetime.now, index=True)
    error = db.Column(db.Integer, nullable=True, index=True)

    __table_args__ = (
        db.Index("ix_task_log_status_date_error", "status_date", "error"),
    )


@dataclass
class TaskFile(db.Model):
    """Table containing paths to task backup files."""

    __tablename__ = "task_file"
    id: Optional[int] = None
    name: Optional[str] = None
    task_id: Optional[int] = None
    job_id: Optional[str] = None
    size: Optional[str] = None
    file_hash: Optional[str] = None
    path: Optional[str] = None
    created: Optional[datetime.datetime] = None

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(1000), nullable=True, index=True)
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id), nullable=True, index=True)
    job_id = db.Column(db.String(1000), nullable=True, index=True)
    size = db.Column(db.String(200), nullable=True, index=True)
    path = db.Column(db.String(1000), nullable=True, index=True)
    file_hash = db.Column(db.String(1000), nullable=True)
    created = db.Column(db.DateTime, default=datetime.datetime.now, index=True)

    __table_args__ = (
        db.Index("ix_task_file_id_task_id_job_id", "id", "task_id", "job_id"),
    )


@dataclass
class TaskParam(db.Model):
    """Task parameters."""

    __tablename__ = "task_param"
    id: Optional[int] = None
    key: Optional[str] = None
    value: Optional[str] = None
    sensitive: Optional[int] = None
    task_id: Optional[int] = None

    id = db.Column(db.Integer, primary_key=True, index=True)
    key = db.Column(db.String(500), nullable=True)
    value = db.Column(db.String(8000), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id), nullable=True, index=True)
    sensitive = db.Column(db.Integer, nullable=True, index=True)
