"""Database utility regression tests."""

import os
from contextlib import suppress
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy_utils import create_database, database_exists

from scripts.database import force_drop_database


def test_force_drop_postgres_database_with_active_connection() -> None:
    """Database reset terminates sessions that would block PostgreSQL DROP DATABASE."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for the PostgreSQL integration test")

    url = make_url(database_url).set(database=f"atlas_force_drop_{uuid4().hex}")
    create_database(url)
    engine = sa.create_engine(url)
    connection = engine.connect()
    connection.execute(sa.text("SELECT 1"))

    try:
        force_drop_database(url, engine)
        assert not database_exists(url)
    finally:
        with suppress(SQLAlchemyError):
            connection.close()
