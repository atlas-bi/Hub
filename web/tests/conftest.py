import os
from datetime import datetime
from typing import Generator, Tuple

import pytest
from dateutil.tz import tzlocal
from flask import url_for
from sqlalchemy_utils import create_database, database_exists, drop_database

from web import create_app as web_create_app
from web import model
from web.model import Project, Task

from . import get_or_create, seed

os.environ["FLASK_ENV"] = "test"
os.environ["FLASK_APP"] = "web"
os.environ["FLASK_DEBUG"] = "False"


@pytest.fixture(scope="function")
def client_fixture() -> Generator:
    app = web_create_app()
    with app.test_client() as client, app.app_context():
        assert app.config["ENV"] == "test"

        from web.extensions import db
        from web.model import User

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

        # tests auto login and redirect
        assert client.get("/login").status_code == 302

        client.post(
            url_for("auth_bp.login"),
            data=dict(
                user="mr-cool",
                password="",
            ),
            follow_redirects=True,
        )

        yield client

    with app.app_context():
        db.session.remove()
        db.drop_all()
        drop_database(db.engine.url)


def check_url(client, url: str, flash: bool = False) -> str:  # type: ignore[no-untyped-def]
    page = client.get(url, follow_redirects=True)
    assert page.status_code == 200
    if flash:
        # print(page.get_data(as_text=True))
        # assert "flashes" in page.get_data(as_text=True)
        return page.get_data(as_text=True)
    return ""


def create_demo_task(session, year: int = 2025, sequence: int = 0) -> Tuple[int, int]:
    # create a project
    project = get_or_create(
        session,
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
        owner_id=1,
    )
    # create a task
    task = get_or_create(
        session,
        Task,
        name="Task 1" + str(project.id),
        source_type_id=6,
        source_code="""select getdate()""",
        project_id=project.id,
        source_query_type_id=4,
        enabled=0,
    )
    return project.id, task.id
