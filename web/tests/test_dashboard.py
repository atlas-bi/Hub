"""Test web/admin.

run with::

   poetry run pytest web/tests/test_dashboard.py \
       --cov --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest web/tests/test_dashboard.py::test_search \
       --cov --cov-branch --cov-append --cov-report=term-missing --disable-warnings


"""

from pytest import fixture

from web.extensions import db
from web.model import (
    Connection,
    ConnectionDatabase,
    ConnectionFtp,
    ConnectionGpg,
    ConnectionSftp,
    ConnectionSmb,
    ConnectionSsh,
)

from .conftest import create_demo_task


def test_search(client_fixture: fixture) -> None:
    # add a task and project
    create_demo_task(db.session, 2025)

    # add a connection
    conn = Connection(
        name="Test Connection",
        description="description",
        address="outer space",
        primary_contact="joe",
        primary_contact_email="no@thin.g",
        primary_contact_phone="411",
    )
    db.session.add(conn)
    db.session.commit()

    # sftp
    conn_sftp = ConnectionSftp(
        name="Test SFTP",
        connection_id=conn.id,
        address="SFTP address",
        port=99,
        path="nowhere/around/here",
        username="albany",
        password="new york",
        key="cool key",
    )
    db.session.add(conn_sftp)
    db.session.commit()
    # database
    conn_database = ConnectionDatabase(
        connection_id=conn.id, name="test db", type_id=1, connection_string="joseph"
    )
    db.session.add(conn_database)
    db.session.commit()
    # ftp
    conn_ftp = ConnectionFtp(
        name="Test FTP",
        connection_id=conn.id,
        address="FTP address",
        path="nowhere/around/here",
        username="albany",
        password="new york",
    )
    db.session.add(conn_ftp)
    db.session.commit()
    # smb
    conn_smb = ConnectionSmb(
        name="Test SMB",
        connection_id=conn.id,
        server_name="smbserver",
        server_ip="1.2.3.4",
        share_name="myshare",
        path="nowhere/around/here",
        username="albany",
        password="new york",
    )
    db.session.add(conn_smb)
    db.session.commit()
    # gpg
    conn_gpg = ConnectionGpg(name="Test GPG", key="cool key", connection_id=conn.id)
    db.session.add(conn_gpg)
    db.session.commit()
    # ssh
    conn_ssh = ConnectionSsh(
        name="Test SSH",
        connection_id=conn.id,
        address="SSH address",
        port=99,
        username="albany",
        password="new york",
    )
    db.session.add(conn_ssh)
    db.session.commit()

    response = client_fixture.get("/search")
    assert response.status_code == 200

    # verify search data
    assert response.get_json()["task"]["/task/1"] is not None
    assert response.get_json()["project"]["/project/1"] is not None


def test_home_with_project(client_fixture: fixture) -> None:
    # add a task and project
    create_demo_task(db.session, 2025)

    response = client_fixture.get("/", follow_redirects=True)
    assert response.status_code == 200
    # verify we are on the user project page
    assert response.request.path == "/"


def test_schedule(client_fixture: fixture) -> None:
    # offline scheduler should return nothing
    response = client_fixture.get("/schedule")
    assert response.status_code == 200

    assert response.get_data(as_text=True) == ""


def test_errored_schedule_now(client_fixture: fixture) -> None:
    response = client_fixture.get("/dash/errored/schedule", follow_redirects=True)
    assert response.status_code == 200


def test_scheduled_schedule_now(client_fixture: fixture) -> None:
    response = client_fixture.get("/dash/scheduled/reschedule", follow_redirects=True)
    assert response.status_code == 200


def test_orphaned_delete(client_fixture: fixture) -> None:
    response = client_fixture.get("/dash/orphans/delete", follow_redirects=True)
    assert response.status_code == 200

    assert "Failed to delete orphans. Scheduler offline." in response.get_data(as_text=True)


def test_errored_run(client_fixture: fixture) -> None:
    response = client_fixture.get("/dash/errored/run", follow_redirects=True)
    assert response.status_code == 200


def test_active_run(client_fixture: fixture) -> None:
    response = client_fixture.get("/dash/active/run", follow_redirects=True)
    assert response.status_code == 200


def test_scheduled_run(client_fixture: fixture) -> None:
    response = client_fixture.get("/dash/scheduled/run", follow_redirects=True)
    assert response.status_code == 200


def test_scheduled_disable(client_fixture: fixture) -> None:
    response = client_fixture.get("/dash/scheduled/disable", follow_redirects=True)
    assert response.status_code == 200
