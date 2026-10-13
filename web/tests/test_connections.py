"""Test connection.py.

run with::

   poetry run pytest tests/test_connections.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest tests/test_connections.py::test_new_sftp \
       --cov --cov-branch  --cov-report=term-missing --disable-warnings

"""

from pathlib import Path
from unittest.mock import Mock

import pytest
from bs4 import BeautifulSoup
from pytest import fixture

from web import db
from web.model import (
    Connection,
    ConnectionDatabase,
    ConnectionFtp,
    ConnectionGpg,
    ConnectionSftp,
    ConnectionSmb,
    ConnectionSsh,
    Task,
)

from .conftest import create_demo_task


def test_connections_home(client_fixture: fixture) -> None:
    assert client_fixture.get("/connection").status_code == 200


def test_new_connection(client_fixture: fixture) -> None:
    response = client_fixture.get("/connection/new")
    assert response.status_code == 200

    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    data = {
        "name": "Test Connection",
        "description": "description",
        "address": "outer space",
        "contact": "joe",
        "email": "no@thin.g",
        "phone": "411",
    }
    response = client_fixture.post(
        "/connection/new",
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["description"] in response.get_data(as_text=True)
    assert data["address"] in response.get_data(as_text=True)
    assert data["contact"] in response.get_data(as_text=True)
    assert data["email"] in response.get_data(as_text=True)
    assert data["phone"] in response.get_data(as_text=True)

    # edit
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "Edit Connection"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )

    data = {
        "name": "Test Connection edited",
        "description": "description edited",
        "address": "outer space edited",
        "contact": "joe edited",
        "email": "no@thin.g edited",
        "phone": "411 edited",
    }
    response = client_fixture.post(
        url,
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["description"] in response.get_data(as_text=True)
    assert data["address"] in response.get_data(as_text=True)
    assert data["contact"] in response.get_data(as_text=True)
    assert data["email"] in response.get_data(as_text=True)
    assert data["phone"] in response.get_data(as_text=True)

    # delete
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "Delete Connection"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )

    assert b"Connection deleted." in response.data


def test_new_database(client_fixture: fixture) -> None:
    # add a connection
    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    data = {
        "name": "Test Connection",
        "description": "description",
        "address": "outer space",
        "contact": "joe",
        "email": "no@thin.g",
        "phone": "411",
    }
    response = client_fixture.post(
        "/connection/new",
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["description"] in response.get_data(as_text=True)
    assert data["address"] in response.get_data(as_text=True)
    assert data["contact"] in response.get_data(as_text=True)
    assert data["email"] in response.get_data(as_text=True)
    assert data["phone"] in response.get_data(as_text=True)

    # new editor
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "New Database"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )

    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("form", attrs={"method": "post"})["action"]

    data = {
        "name": "Test Database",
        "database_type": "1",
        "connection_string": "outer space",
    }

    response = client_fixture.post(
        url,
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["connection_string"] in response.get_data(as_text=True)

    # edit
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "Edit Database Connection"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )

    data = {
        "name": "Test Database edited",
        "database_type": "2",
        "connection_string": "outer space edited",
    }

    response = client_fixture.post(
        url,
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["connection_string"] in response.get_data(as_text=True)

    # delete
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "Delete Database Connection"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )


def test_delete_database_disables_referencing_tasks(client_fixture: fixture, monkeypatch) -> None:
    """Deleting a database disables its task and requests scheduler removal."""
    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    response = client_fixture.post(
        "/connection/new",
        data={
            "name": "Test Connection",
            "description": "description",
            "address": "outer space",
            "contact": "joe",
            "email": "no@thin.g",
            "phone": "411",
        },
        headers=headers,
        follow_redirects=True,
    )

    soup = BeautifulSoup(response.data, features="lxml")
    new_database_url = soup.find("a", attrs={"title": "New Database"})["href"]
    response = client_fixture.get(new_database_url, follow_redirects=True)

    soup = BeautifulSoup(response.data, features="lxml")
    form_url = soup.find("form", attrs={"method": "post"})["action"]
    client_fixture.post(
        form_url,
        data={
            "name": "Test Database",
            "database_type": "1",
            "connection_string": "outer space",
        },
        headers=headers,
        follow_redirects=True,
    )

    database = ConnectionDatabase.query.filter_by(name="Test Database").first()
    _, task_id = create_demo_task(db.session)
    task = Task.query.filter_by(id=task_id).first()
    task.source_database_id = database.id
    task.source_type_id = 1
    task.enabled = 1
    db.session.commit()

    scheduler_get = Mock()
    monkeypatch.setattr("web.web.connection.requests.get", scheduler_get)

    client_fixture.get(
        f"/connection/{database.connection_id}/database/{database.id}/delete",
        follow_redirects=True,
    )

    db.session.expire_all()
    task = Task.query.filter_by(id=task_id).first()
    assert task.source_database_id is None
    assert task.source_type_id is None
    assert task.enabled == 0
    scheduler_get.assert_called_once_with(
        f"{client_fixture.application.config['SCHEDULER_HOST']}/delete/{task_id}", timeout=10
    )


def test_connection_forms_include_csrf_tokens(client_fixture: fixture) -> None:
    """Connection forms expose tokens and CSRF rejects a tokenless POST."""
    client_fixture.application.config["WTF_CSRF_ENABLED"] = True
    response = client_fixture.get("/connection/new")
    soup = BeautifulSoup(response.data, features="lxml")
    assert soup.find("input", attrs={"name": "csrf_token", "value": True})
    assert (
        client_fixture.post("/connection/new", data={"name": "Missing token"}).status_code == 400
    )

    templates = Path(__file__).parents[1] / "templates" / "pages" / "connection"
    for name in (
        "new.html.j2",
        "database_edit.html.j2",
        "sftp_edit.html.j2",
        "ftp_edit.html.j2",
        "smb_edit.html.j2",
        "ssh_edit.html.j2",
        "gpg_edit.html.j2",
    ):
        assert 'name="csrf_token"' in (templates / name).read_text()


@pytest.mark.parametrize(
    ("connector_model", "endpoint", "cleared_fields"),
    [
        (
            ConnectionSftp,
            "sftp",
            {
                "source_sftp_id": None,
                "source_sftp_file": None,
                "source_sftp_delimiter": None,
                "source_sftp_ignore_delimiter": None,
                "source_type_id": None,
                "query_sftp_id": None,
                "query_sftp_file": None,
                "source_query_type_id": None,
                "processing_sftp_id": None,
                "processing_sftp_file": None,
                "processing_type_id": None,
                "destination_sftp_id": None,
                "destination_sftp": 0,
                "destination_sftp_overwrite": None,
                "destination_sftp_dont_send_empty_file": None,
            },
        ),
        (
            ConnectionSsh,
            "ssh",
            {"source_ssh_id": None, "source_type_id": None},
        ),
        (
            ConnectionSmb,
            "smb",
            {
                "source_smb_id": None,
                "source_smb_file": None,
                "source_smb_delimiter": None,
                "source_smb_ignore_delimiter": None,
                "source_type_id": None,
                "query_smb_id": None,
                "query_smb_file": None,
                "source_query_type_id": None,
                "processing_smb_id": None,
                "processing_smb_file": None,
                "processing_type_id": None,
                "destination_smb_id": None,
                "destination_smb": 0,
                "destination_smb_overwrite": None,
                "destination_smb_dont_send_empty_file": None,
            },
        ),
        (
            ConnectionFtp,
            "ftp",
            {
                "source_ftp_id": None,
                "source_ftp_file": None,
                "source_ftp_delimiter": None,
                "source_ftp_ignore_delimiter": None,
                "source_type_id": None,
                "query_ftp_id": None,
                "query_ftp_file": None,
                "source_query_type_id": None,
                "processing_ftp_id": None,
                "processing_ftp_file": None,
                "processing_type_id": None,
                "destination_ftp_id": None,
                "destination_ftp": 0,
                "destination_ftp_overwrite": None,
                "destination_ftp_dont_send_empty_file": None,
            },
        ),
        (
            ConnectionGpg,
            "gpg",
            {"file_gpg_id": None, "file_gpg": 0},
        ),
    ],
)
def test_delete_connection_cleans_referencing_tasks(
    client_fixture: fixture, monkeypatch, connector_model, endpoint, cleared_fields
) -> None:
    """Deleting each connector clears its task roles and unschedules the task."""
    connection = Connection(
        name="Test Connection",
        description="description",
        address="outer space",
        primary_contact="joe",
        primary_contact_email="joe@example.net",
        primary_contact_phone="411",
    )
    db.session.add(connection)
    db.session.commit()

    connector = connector_model(connection_id=connection.id, name="Test Connector")
    db.session.add(connector)
    db.session.commit()

    _, task_id = create_demo_task(db.session)
    task = Task.query.filter_by(id=task_id).first()
    task.enabled = 1
    for field, cleared_value in cleared_fields.items():
        if cleared_value == 0:
            value = 1
        elif field.endswith("_id") and not field.endswith("_type_id"):
            value = connector.id
        elif (
            field.endswith("_id")
            or "ignore_delimiter" in field
            or field.endswith(("overwrite", "dont_send_empty_file"))
            or field == "file_gpg"
        ):
            value = 1
        elif field.endswith("_file"):
            value = "previous.csv"
        elif field.endswith("_delimiter"):
            value = "|"
        else:
            raise AssertionError(f"No seed value defined for {field}.")
        setattr(task, field, value)
    db.session.commit()

    scheduler_delete = Mock()
    monkeypatch.setattr("web.web.connection.requests.get", scheduler_delete)
    response = client_fixture.get(
        f"/connection/{connection.id}/{endpoint}/{connector.id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    db.session.expire_all()
    task = Task.query.filter_by(id=task_id).first()
    assert task.enabled == 0
    for field, cleared_value in cleared_fields.items():
        assert getattr(task, field) == cleared_value
    scheduler_delete.assert_called_once_with(
        f"{client_fixture.application.config['SCHEDULER_HOST']}/delete/{task_id}",
        timeout=10,
    )


def test_new_sftp(client_fixture: fixture) -> None:
    # add a connection
    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    data = {
        "name": "Test Connection",
        "description": "description",
        "address": "outer space",
        "contact": "joe",
        "email": "no@thin.g",
        "phone": "411",
    }
    response = client_fixture.post(
        "/connection/new",
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["description"] in response.get_data(as_text=True)
    assert data["address"] in response.get_data(as_text=True)
    assert data["contact"] in response.get_data(as_text=True)
    assert data["email"] in response.get_data(as_text=True)
    assert data["phone"] in response.get_data(as_text=True)

    # new editor
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "New SFTP"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )

    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("form", attrs={"method": "post"})["action"]

    data = {
        "name": "Test SFTP",
        "address": "SFTP address",
        "port": "99",
        "path": "nowhere/around/here",
        "username": "albany",
        "password": "new york",
        "ssh_key": "cool key",
    }

    response = client_fixture.post(
        url,
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["address"] in response.get_data(as_text=True)
    assert data["port"] in response.get_data(as_text=True)
    assert data["path"] in response.get_data(as_text=True)
    assert data["username"] in response.get_data(as_text=True)
    assert data["password"] in response.get_data(as_text=True)
    assert data["ssh_key"] in response.get_data(as_text=True)

    # edit
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "Edit SFTP Connection"})["href"]
    response = client_fixture.get(
        url,
        follow_redirects=True,
    )

    data = {
        "name": "Test SFTP edited",
        "address": "SFTP address edited",
        "port": "101",
        "path": "nowhere/around/here/ edited",
        "username": "albany edited",
        "password": "new york edited",
        "ssh_key": "cool key edited",
    }

    response = client_fixture.post(
        url,
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["address"] in response.get_data(as_text=True)
    assert data["port"] in response.get_data(as_text=True)
    assert data["path"] in response.get_data(as_text=True)
    assert data["username"] in response.get_data(as_text=True)
    assert data["password"] in response.get_data(as_text=True)
    assert data["ssh_key"] in response.get_data(as_text=True)

    # delete
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "Delete SFTP Connection"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )


def test_new_ftp(client_fixture: fixture) -> None:
    # add a connection
    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    data = {
        "name": "Test Connection",
        "description": "description",
        "address": "outer space",
        "contact": "joe",
        "email": "no@thin.g",
        "phone": "411",
    }
    response = client_fixture.post(
        "/connection/new",
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["description"] in response.get_data(as_text=True)
    assert data["address"] in response.get_data(as_text=True)
    assert data["contact"] in response.get_data(as_text=True)
    assert data["email"] in response.get_data(as_text=True)
    assert data["phone"] in response.get_data(as_text=True)

    # new editor
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "New FTP"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )

    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("form", attrs={"method": "post"})["action"]

    data = {
        "name": "Test FTP",
        "address": "FTP address",
        "path": "nowhere/around/here",
        "username": "albany",
        "password": "new york",
    }

    response = client_fixture.post(
        url,
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["address"] in response.get_data(as_text=True)
    assert data["path"] in response.get_data(as_text=True)
    assert data["username"] in response.get_data(as_text=True)
    assert data["password"] in response.get_data(as_text=True)

    # edit
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "Edit FTP Connection"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )

    data = {
        "name": "Test FTP edited",
        "address": "FTP address edited",
        "path": "nowhere/around/here/ edited",
        "username": "albany edited",
        "password": "new york edited",
    }

    response = client_fixture.post(
        url,
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["address"] in response.get_data(as_text=True)
    assert data["path"] in response.get_data(as_text=True)
    assert data["username"] in response.get_data(as_text=True)
    assert data["password"] in response.get_data(as_text=True)

    # delete
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "Delete FTP Connection"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )


def test_new_smb(client_fixture: fixture) -> None:
    # add a connection
    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    data = {
        "name": "Test Connection",
        "description": "description",
        "address": "outer space",
        "contact": "joe",
        "email": "no@thin.g",
        "phone": "411",
    }
    response = client_fixture.post(
        "/connection/new",
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["description"] in response.get_data(as_text=True)
    assert data["address"] in response.get_data(as_text=True)
    assert data["contact"] in response.get_data(as_text=True)
    assert data["email"] in response.get_data(as_text=True)
    assert data["phone"] in response.get_data(as_text=True)

    # new editor
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "New SMB"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )

    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("form", attrs={"method": "post"})["action"]

    data = {
        "name": "Test SMB",
        "server_name": "smbserver",
        "server_ip": "1.2.3.4",
        "share_name": "myshare",
        "path": "nowhere/around/here",
        "username": "albany",
        "password": "new york",
    }

    response = client_fixture.post(
        url,
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["server_name"] in response.get_data(as_text=True)
    assert data["server_ip"] in response.get_data(as_text=True)
    assert data["share_name"] in response.get_data(as_text=True)
    assert data["path"] in response.get_data(as_text=True)
    assert data["username"] in response.get_data(as_text=True)
    assert data["password"] in response.get_data(as_text=True)

    # edit
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "Edit SMB Connection"})["href"]
    response = client_fixture.get(
        url,
        follow_redirects=True,
    )

    data = {
        "name": "Test SMB edited",
        "server_name": "smbserver edited",
        "server_ip": "1.2.3.5",
        "share_name": "myshareedited",
        "path": "nowhere/around/here/edited",
        "username": "albany edited",
        "password": "new york edited",
    }

    response = client_fixture.post(
        url,
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["server_name"] in response.get_data(as_text=True)
    assert data["server_ip"] in response.get_data(as_text=True)
    assert data["share_name"] in response.get_data(as_text=True)
    assert data["path"] in response.get_data(as_text=True)
    assert data["username"] in response.get_data(as_text=True)
    assert data["password"] in response.get_data(as_text=True)

    # delete
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "Delete SMB Connection"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )


def test_new_ssh(client_fixture: fixture) -> None:
    # add a connection
    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    data = {
        "name": "Test Connection",
        "description": "description",
        "address": "outer space",
        "contact": "joe",
        "email": "no@thin.g",
        "phone": "411",
    }
    response = client_fixture.post(
        "/connection/new",
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["description"] in response.get_data(as_text=True)
    assert data["address"] in response.get_data(as_text=True)
    assert data["contact"] in response.get_data(as_text=True)
    assert data["email"] in response.get_data(as_text=True)
    assert data["phone"] in response.get_data(as_text=True)

    # new editor
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "New SSH"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )

    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("form", attrs={"method": "post"})["action"]

    data = {
        "name": "Test SSH",
        "address": "SSH address",
        "port": "99",
        "username": "albany",
        "password": "new york",
    }

    response = client_fixture.post(
        url,
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["address"] in response.get_data(as_text=True)
    assert data["port"] in response.get_data(as_text=True)
    assert data["username"] in response.get_data(as_text=True)
    assert data["password"] in response.get_data(as_text=True)

    # edit
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "Edit SSH Connection"})["href"]
    response = client_fixture.get(
        url,
        follow_redirects=True,
    )

    data = {
        "name": "Test SSH edited",
        "address": "SSH address edited",
        "port": "101",
        "username": "albany edited",
        "password": "new york edited",
    }

    response = client_fixture.post(
        url,
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["address"] in response.get_data(as_text=True)
    assert data["port"] in response.get_data(as_text=True)
    assert data["username"] in response.get_data(as_text=True)
    assert data["password"] in response.get_data(as_text=True)

    # delete
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "Delete SSH Connection"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )


def test_new_gpg(client_fixture: fixture) -> None:
    # add a connection
    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    data = {
        "name": "Test Connection",
        "description": "description",
        "address": "outer space",
        "contact": "joe",
        "email": "no@thin.g",
        "phone": "411",
    }
    response = client_fixture.post(
        "/connection/new",
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["description"] in response.get_data(as_text=True)
    assert data["address"] in response.get_data(as_text=True)
    assert data["contact"] in response.get_data(as_text=True)
    assert data["email"] in response.get_data(as_text=True)
    assert data["phone"] in response.get_data(as_text=True)

    # new editor
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "New GPG"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )

    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("form", attrs={"method": "post"})["action"]

    data = {"name": "Test GPG", "key": "cool key"}

    response = client_fixture.post(
        url,
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["key"] in response.get_data(as_text=True)

    # edit
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "Edit GPG Connection"})["href"]
    response = client_fixture.get(
        url,
        follow_redirects=True,
    )

    data = {"name": "Test GPG edited", "key": "cool key edited"}

    response = client_fixture.post(
        url,
        data=data,
        headers=headers,
        follow_redirects=True,
    )

    assert data["name"] in response.get_data(as_text=True)
    assert data["key"] in response.get_data(as_text=True)

    # delete
    soup = BeautifulSoup(response.data, features="lxml")
    url = soup.find("a", attrs={"title": "Delete GPG Connection"})["href"]

    response = client_fixture.get(
        url,
        follow_redirects=True,
    )
