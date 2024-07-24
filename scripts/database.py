"""Initial creation and seed of the database."""

from typing import Any

from sqlalchemy.orm import Session as SqlSession


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
    get_or_create(session, model.ConnectionDatabaseType, name="Jdbc")

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
    get_or_create(session, model.TaskStatus, name="Jdbc")
