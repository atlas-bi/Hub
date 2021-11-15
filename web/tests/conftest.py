import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from typing import Generator, Tuple

import pytest
import requests
from dateutil.tz import tzlocal
from flask import url_for

from web import create_app as web_create_app
from web.model import Project, Task
from web.seed import get_or_create

os.environ["FLASK_ENV"] = "test"
os.environ["FLASK_APP"] = "web"
os.environ["FLASK_DEBUG"] = "False"


@pytest.fixture(scope="module")
def client_fixture() -> Generator:
    app = web_create_app()
    with app.test_client() as client, app.app_context():

        assert app.config["ENV"] == "test"

        from web.extensions import db
        from web.model import User
        from web.seed import get_or_create, seed

        db.drop_all()
        db.session.commit()

        db.create_all()
        db.session.commit()

        seed(db.session)

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

        if sys.platform == "darwin":
            print("killing 5002")
            subprocess.run(
                ["lsof -i :5002 | grep 'python' | awk '{print $2}' | xargs kill -9"],
                shell=True,
            )
            print("killing 5001")
            subprocess.run(
                ["lsof -i :5001 | grep 'python' | awk '{print $2}' | xargs kill -9"],
                shell=True,
            )

        yield client


# scope as function
@pytest.fixture()
def client_fixture_with_scheduler(client_fixture: Generator) -> Generator:

    # start up scheduler if not running
    process = None
    try:
        requests.get(client_fixture.application.config["SCHEDULER_HOST"])  # type: ignore[attr-defined]
    except requests.exceptions.ConnectionError:
        process = subprocess.Popen(
            [
                "FLASK_ENV=test; FLASK_DEBUG=True; FLASK_APP=scheduler; .tox/test/bin/python -m flask run --port 5001"
            ],
            shell=True,
            preexec_fn=os.setsid,
        )
        # give it time to start up
        time.sleep(5)

    assert (
        requests.get(client_fixture.application.config["SCHEDULER_HOST"]).status_code  # type: ignore[attr-defined]
        == 200
    )

    yield client_fixture

    # stop scheduler
    if process:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)


# scope as function
@pytest.fixture()
def client_fixture_with_runner(client_fixture: Generator) -> Generator:

    # start up scheduler if not running
    process = None
    try:
        requests.get(client_fixture.application.config["RUNNER_HOST"])  # type: ignore[attr-defined]
    except requests.exceptions.ConnectionError:
        process = subprocess.Popen(
            [
                "FLASK_ENV=test; FLASK_DEBUG=False; FLASK_APP=runner; flask run --port 5002"
            ],
            shell=True,
            preexec_fn=os.setsid,
        )
        # give it time to start up
        time.sleep(5)

    assert (  # type: ignore[attr-defined]
        requests.get(client_fixture.application.config["RUNNER_HOST"]).status_code  # type: ignore[attr-defined]
        == 200
    )

    yield client_fixture

    # stop runner
    if process:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)


def check_url(client, url: str, flash: bool = False) -> str:  # type: ignore[no-untyped-def]
    page = client.get(url, follow_redirects=True)
    assert page.status_code == 200
    if flash:
        assert "flashes" in page.get_data(as_text=True)
        return page.get_data(as_text=True)
    return ""


def create_demo_task(year: int = 2025, sequence: int = 0) -> Tuple[int, int]:
    from scheduler.extensions import db

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
        owner_id=1,
    )
    # create a task
    task = get_or_create(
        db.session,
        Task,
        name="Task 1" + str(project.id),
        source_type_id=6,
        source_code="""select getdate()""",
        project_id=project.id,
        source_query_type_id=4,
        enabled=0,
    )
    return project.id, task.id
