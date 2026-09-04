from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session as SqlSession
from sqlalchemy_utils import drop_database


def force_drop_database(url: Any, engine: Optional[Any] = None) -> None:
    """Drop a database, terminating Postgres sessions first.

    sqlalchemy-utils >= 0.42 removed the ``pg_terminate_backend`` step that used
    to run before ``DROP DATABASE``. Flask-SQLAlchemy (and other) connection pools
    still hold sessions to the target DB during test teardown, which then fails
    with ``ObjectInUse``. See https://github.com/kvesteri/sqlalchemy-utils/issues/791
    """
    if engine is not None:
        engine.dispose()

    url_obj = make_url(url)
    if url_obj.get_dialect().name != "postgresql":
        drop_database(url)
        return

    database = url_obj.database
    dialect_driver = url_obj.get_dialect().driver
    admin_url = url_obj.set(database="postgres")

    if dialect_driver in {"asyncpg", "pg8000", "psycopg", "psycopg2", "psycopg2cffi"}:
        admin_engine = sa.create_engine(admin_url, isolation_level="AUTOCOMMIT")
    else:
        admin_engine = sa.create_engine(admin_url)

    try:
        with admin_engine.begin() as conn:
            version = conn.dialect.server_version_info
            pid_column = "pid" if version >= (9, 2) else "procpid"
            conn.execute(
                sa.text(
                    f"""
                    SELECT pg_terminate_backend(pg_stat_activity.{pid_column})
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = :database
                      AND {pid_column} <> pg_backend_pid()
                    """
                ),
                {"database": database},
            )
            quoted = conn.dialect.identifier_preparer.quote(database)
            conn.execute(sa.text(f"DROP DATABASE {quoted}"))
    finally:
        admin_engine.dispose()


def get_or_create(session: SqlSession, model: Any, **kwargs: Any) -> Any:
    """Create model if not existing."""
    instance = model.query.filter_by(**kwargs).first()

    if instance:
        return instance

    instance = model(**kwargs)

    session.add(instance)
    session.commit()

    return instance


def seed(session: SqlSession, model: Any) -> None:
    """Insert seed records to database."""
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    # login types
    get_or_create(session, model.User, account_name="admin", full_name="admin")
    get_or_create(session, model.LoginType, name="login")
    get_or_create(session, model.LoginType, name="logout")
    get_or_create(session, model.LoginType, name="bad login")

    # quote level
    get_or_create(session, model.QuoteLevel, name="Quote None")
    get_or_create(session, model.QuoteLevel, name="Quote All")
    get_or_create(session, model.QuoteLevel, name="Quote Minimal (default)")
    get_or_create(session, model.QuoteLevel, name="Quote Non-numeric")

    # task source type
    get_or_create(session, model.TaskSourceType, name="Database")
    get_or_create(session, model.TaskSourceType, name="Network File (SMB Connection)")
    get_or_create(session, model.TaskSourceType, name="File (SFTP Connection)")
    get_or_create(session, model.TaskSourceType, name="File (FTP Connection)")
    get_or_create(session, model.TaskSourceType, name="Python Script")
    get_or_create(session, model.TaskSourceType, name="SSH Command")

    # task processing type
    get_or_create(session, model.TaskProcessingType, name="Network File (SMB Connection)")
    get_or_create(session, model.TaskProcessingType, name="File (SFTP Connection)")
    get_or_create(session, model.TaskProcessingType, name="File (FTP Connection)")
    get_or_create(session, model.TaskProcessingType, name="Git URL")
    get_or_create(session, model.TaskProcessingType, name="Other URL (no auth)")
    get_or_create(session, model.TaskProcessingType, name="Source Code")
    get_or_create(session, model.TaskProcessingType, name="Devops")

    # task source query type
    get_or_create(session, model.TaskSourceQueryType, name="Git URL")
    get_or_create(session, model.TaskSourceQueryType, name="File Path (SMB Connection)")
    get_or_create(session, model.TaskSourceQueryType, name="Other URL (no auth)")
    get_or_create(session, model.TaskSourceQueryType, name="Source Code")
    get_or_create(session, model.TaskSourceQueryType, name="File Path (SFTP Connection)")
    get_or_create(session, model.TaskSourceQueryType, name="File Path (FTP Connection)")
    get_or_create(session, model.TaskSourceQueryType, name="Devops")

    # database type
    get_or_create(session, model.ConnectionDatabaseType, name="Postgres")
    get_or_create(session, model.ConnectionDatabaseType, name="SQL Sever")

    # file types
    get_or_create(session, model.TaskDestinationFileType, name="CSV (.csv)", ext="csv")
    get_or_create(session, model.TaskDestinationFileType, name="Text (.txt)", ext="txt")
    get_or_create(session, model.TaskDestinationFileType, name="Excel (.csv)", ext="csv")
    get_or_create(
        session,
        model.TaskDestinationFileType,
        name="Other (specify in filename)",
        ext="",
    )

    # task status
    get_or_create(session, model.TaskStatus, name="Running")
    get_or_create(session, model.TaskStatus, name="Errored")
    get_or_create(session, model.TaskStatus, name="Stopped")
    get_or_create(session, model.TaskStatus, name="Completed")
    get_or_create(session, model.TaskStatus, name="Starting")
    get_or_create(session, model.TaskStatus, name="Scheduler")
    get_or_create(session, model.TaskStatus, name="User")
    get_or_create(session, model.TaskStatus, name="Runner")
    get_or_create(session, model.TaskStatus, name="SFTP")
    get_or_create(session, model.TaskStatus, name="SMB")
    get_or_create(session, model.TaskStatus, name="File")
    get_or_create(session, model.TaskStatus, name="Email")
    get_or_create(session, model.TaskStatus, name="FTP")
    get_or_create(session, model.TaskStatus, name="Py Processer")
    get_or_create(session, model.TaskStatus, name="Git/Web Code")
    get_or_create(session, model.TaskStatus, name="Date Parser")
    get_or_create(session, model.TaskStatus, name="Cmd Runner")
    get_or_create(session, model.TaskStatus, name="System")
    get_or_create(session, model.TaskStatus, name="SSH")
    get_or_create(session, model.TaskStatus, name="SQL Server")
    get_or_create(session, model.TaskStatus, name="Postgres")
