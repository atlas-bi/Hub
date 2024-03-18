"""Setyp pytest."""

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy_utils import create_database, database_exists, drop_database

from scheduler import create_app as scheduler_create_app
from scheduler.model import Project, Task

from . import get_or_create, seed

os.environ["FLASK_ENV"] = "test"
os.environ["FLASK_APP"] = "scheduler"
os.environ["FLASK_DEBUG"] = "False"

import subprocess
from datetime import datetime, timezone
from typing import Any, Generator, Tuple

from dateutil.tz import tzlocal

from scheduler import model


# default scope is function.
@pytest.fixture(scope="function")
def client_fixture() -> Generator:
    """Scheduler client."""

    app = scheduler_create_app()
    with app.test_client() as client, app.app_context():
        assert app.config["ENV"] == "test"  # noqa: S101

        from scheduler.extensions import atlas_scheduler, db

        # from web.seed import seed

        if database_exists(db.engine.url):
            drop_database(db.engine.url)

        create_database(db.engine.url)

        assert database_exists(db.engine.url)

        db.create_all()
        db.session.commit()

        seed(db.session, model)

        atlas_scheduler.remove_all_jobs()

        assert atlas_scheduler.running  # noqa: S101

        yield client

        if atlas_scheduler.running:
            print("shutting down scheduler")
            atlas_scheduler.shutdown(wait=False)

    with app.app_context():
        db.session.remove()
        db.drop_all()
        drop_database(db.engine.url)


@pytest.fixture(scope="module")
def api_fixture() -> Generator:
    """Scheduler client."""

    app = scheduler_create_app()
    with app.test_client() as client, app.app_context():
        assert app.config["ENV"] == "test"  # noqa: S101

        from scheduler.extensions import atlas_scheduler, db

        # from web.seed import seed

        if database_exists(db.engine.url):
            drop_database(db.engine.url)

        create_database(db.engine.url)

        assert database_exists(db.engine.url)

        db.create_all()
        db.session.commit()

        seed(db.session, model)

        atlas_scheduler.remove_all_jobs()

        assert atlas_scheduler.running  # noqa: S101

        yield client

        if atlas_scheduler.running:
            print("shutting down scheduler")
            atlas_scheduler.shutdown(wait=False)

    with app.app_context():
        db.session.remove()
        db.drop_all()
        drop_database(db.engine.url)


# pylint: disable=W0613
def demo_task(*kwards: Any, **args: Any) -> int:
    """Demo function with no errors.

    Used to test the scheduler.
    """
    return 1 + 1


# pylint: disable=W0613
def bad_demo_task(*kwards: Any, **args: Any) -> int:
    """Demo function that will result in error.

    Used to test the scheduler.
    """
    # pylint: disable=W0104,E0602
    asdf  # type: ignore[name-defined]  # noqa: F821
    return 1 + 1


def create_demo_task(session, year: int = 2025, sequence: int = 0) -> Tuple[int, int]:
    """Create demo project and task."""
    # create a project
    project = get_or_create(
        session,
        Project,
        name="Project 1 " + str(datetime.now()),
        cron=1,
        cron_min="1",
        cron_start_date=datetime(year, 1, 1, tzinfo=timezone.utc),
        sequence_tasks=sequence,
        intv=1,
        intv_type="w",
        intv_start_date=datetime(9999, 1, 1, tzinfo=timezone.utc),
        ooff=1,
        ooff_date=datetime(9999, 1, 1, tzinfo=timezone.utc),
    )
    # create a task
    task = get_or_create(
        session,
        Task,
        name="Task 1 " + str(project.id),
        source_type_id=6,
        source_code="""select getdate()""",
        project_id=project.id,
        source_query_type_id=4,
        enabled=0,
    )
    return project.id, task.id
