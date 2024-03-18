"""Setyp pytest."""

import os

import pytest
from sqlalchemy_utils import create_database, database_exists, drop_database

from runner import create_app as runner_create_app
from runner.model import Project, Task

from . import get_or_create, seed

os.environ["FLASK_ENV"] = "test"
os.environ["FLASK_APP"] = "runner"
os.environ["FLASK_DEBUG"] = "False"

from datetime import datetime
from typing import Any, Generator, Tuple

from dateutil.tz import tzlocal

from runner import model


@pytest.fixture(scope="module")
def client_fixture() -> Generator:
    app = runner_create_app()
    with app.test_client() as client, app.app_context():
        assert app.config["ENV"] == "test"

        from runner.extensions import db
        from runner.model import User

        if database_exists(db.engine.url):
            drop_database(db.engine.url)

        create_database(db.engine.url)

        assert database_exists(db.engine.url)

        db.create_all()
        db.session.commit()

        seed(db.session, model)

        get_or_create(
            db.session,
            User,
            full_name="Mr Cool",
            first_name="Mr",
            account_name="mr-cool",
            email="mr@co.ol",
        )

        yield client


# pylint: disable=W0613
def demo_task(*kwards: Any, **args: Any) -> int:
    """Demo function with no errors."""
    return 1 + 1


# pylint: disable=W0613
def bad_demo_task(*kwards: Any, **args: Any) -> int:
    """Demo function that will result in error."""
    # pylint: disable=W0104,E0602
    asdf  # type: ignore[name-defined]  # noqa: F821
    return 1 + 1


def create_demo_task(year: int = 2025, sequence: int = 0) -> Tuple[int, int]:
    """Create demo project and task."""
    from runner.extensions import db

    # create a project
    project = get_or_create(
        db.session,
        Project,
        name="Project 1 " + str(datetime.now()),
        cron=1,
        cron_min="1",
        cron_start_date=datetime(year, 1, 1, tzinfo=tzlocal()),
        sequence_tasks=sequence,
        intv=1,
        intv_type="w",
        intv_start_date=datetime(9999, 1, 1, tzinfo=tzlocal()),
        ooff=1,
        ooff_date=datetime(9999, 1, 1, tzinfo=tzlocal()),
    )
    # create a task
    task = get_or_create(
        db.session,
        Task,
        name="Task 1 " + str(project.id),
        source_type_id=6,
        source_code="""select getdate()""",
        project_id=project.id,
        source_query_type_id=4,
        enabled=0,
    )
    return project.id, task.id
