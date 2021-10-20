"""Test connection.py.

run with::

   poetry run pytest tests/test_connections.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest tests/test_connections.py::test_new_database \
       --cov --cov-branch  --cov-report=term-missing --disable-warnings

"""

from bs4 import BeautifulSoup
from pytest import fixture


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
    url = soup.find("form", attrs={"method": "POST"})["action"]

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
    url = soup.find("form", attrs={"method": "POST"})["action"]

    data = {
        "name": "Test SFTP",
        "address": "SFTP address",
        "port": "99",
        "path": "nowhere/around/here",
        "username": "albany",
        "password": "new york",
        "key": "cool key",
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
    assert data["key"] in response.get_data(as_text=True)

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
        "key": "cool key edited",
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
    assert data["key"] in response.get_data(as_text=True)

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
    url = soup.find("form", attrs={"method": "POST"})["action"]

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
    url = soup.find("form", attrs={"method": "POST"})["action"]

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
    url = soup.find("form", attrs={"method": "POST"})["action"]

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
    url = soup.find("form", attrs={"method": "POST"})["action"]

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
