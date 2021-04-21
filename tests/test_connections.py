# flake8: noqa,
# pylint: skip-file
import json
import re

import pytest
from bs4 import BeautifulSoup


def test_connections_home(em_web_authed):
    assert em_web_authed.get("/connection").status_code == 200


def test_new_connection_get(em_web_authed):
    response = em_web_authed.get("/connection/new")
    assert response.status_code == 302


def test_new_connection_post(em_web_authed):
    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    response = em_web_authed.post(
        "/connection/new",
        data={
            "name": "Test Connection",
            "desc": "description",
            "addr": "outer space",
            "contact": "joe",
            "email": "no@thin.g",
            "phone": "411",
            "sftp1-name": "test sftp",
            "sftp1-addr": "outerspace",
            "sftp1-port": 99,
            "sftp1-path": "/home/ward/bound",
            "sftp1-user": "me",
            "sftp1-key": "long key value?",
            "sftp1-pass": "coolpass",
            "ssh1-name": "test ssh",
            "ssh1-addr": "outerspace",
            "ssh1-port": 99,
            "ssh1-user": "me",
            "ssh1-pass": "coolpass",
            "ftp1-name": "test ftp",
            "ftp1-addr": "outerspace",
            "ftp1-port": 99,
            "ftp1-path": "/home/ward/bound",
            "ftp1-user": "me",
            "ftp1-key": "long key value?",
            "ftp1-pass": "coolpass",
            "smb1-name": "test sftp",
            "smb1-servername": "test smb",
            "smb1-serverip": "10.0.0.0",
            "smb1-sharename": "shared stuff",
            "smb1-path": "/home/ward/bound",
            "smb1-user": "me",
            "smb1-pass": "coolpass",
            "gpg1-name": "test gpg",
            "gpg1-key": "long key!",
            "database1-name": "test sftp",
            "database1-type": "1",
            "database1-conn": "long connection string should be valid",
        },
        headers=headers,
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_get_connection(em_web_authed):
    # get a connection
    response = em_web_authed.get("/connection")
    soup = BeautifulSoup(response.data)
    url = soup.find("a", attrs={"title": "Edit Connection"})["href"]

    response = em_web_authed.get(url)
    assert response.status_code == 200


def test_edit_connection(em_web_authed):
    # get a connection
    response = em_web_authed.get("/connection")
    soup = BeautifulSoup(response.data)
    url = soup.find("a", attrs={"title": "Edit Connection"})["href"]

    # <a title="Edit Connection" href="/connection/2"></a>

    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    response = em_web_authed.post(
        url,
        data={
            "name": "Test Connection",
            "desc": "description",
            "addr": "outer space",
            "contact": "joe",
            "email": "no@thin.g",
            "phone": "411",
            "sftp1-name": "test sftp",
            "sftp1-addr": "outerspace",
            "sftp1-port": 99,
            "sftp1-path": "/home/ward/bound",
            "sftp1-user": "me",
            "sftp1-key": "long key value?",
            "sftp1-pass": "coolpass",
            "ssh1-name": "test ssh",
            "ssh1-addr": "outerspace",
            "ssh1-port": 99,
            "ssh1-user": "me",
            "ssh1-pass": "coolpass",
            "ftp1-name": "test ftp",
            "ftp1-addr": "outerspace",
            "ftp1-port": 99,
            "ftp1-path": "/home/ward/bound",
            "ftp1-user": "me",
            "ftp1-key": "long key value?",
            "ftp1-pass": "coolpass",
            "smb1-name": "test sftp",
            "smb1-servername": "test smb",
            "smb1-serverip": "10.0.0.0",
            "smb1-sharename": "shared stuff",
            "smb1-path": "/home/ward/bound",
            "smb1-user": "me",
            "smb1-pass": "coolpass",
            "gpg1-name": "test gpg",
            "gpg1-key": "long key!",
            "database1-name": "test sftp",
            "database1-type": "1",
            "database1-conn": "long connection string should be valid",
        },
        headers=headers,
    )

    assert response.status_code == 200


def test_sftp_connection(em_web_authed):
    response = em_web_authed.get("/connection/sftp")
    assert response.status_code == 200


def test_gpg_connection(em_web_authed):
    response = em_web_authed.get("/connection/gpg")
    assert response.status_code == 200


def test_smb_connection(em_web_authed):
    response = em_web_authed.get("/connection/smb")
    assert response.status_code == 200


def test_database_connection(em_web_authed):
    response = em_web_authed.get("/connection/database")
    assert response.status_code == 200


def test_ftp_connection(em_web_authed):
    response = em_web_authed.get("/connection/ftp")
    assert response.status_code == 200


def test_remove_sftp_connection(em_web_authed):
    # get connection and db id
    response = em_web_authed.get("/connection")
    # open first connection editor
    soup = BeautifulSoup(response.data)
    url = soup.find("a", attrs={"title": "Edit Connection"})["href"]
    connection_id = re.findall(r"\d+", url)[0]

    response = em_web_authed.get(url)

    # get el id
    soup = BeautifulSoup(response.data)
    el_id = soup.select("div.em-drop[data-sftp]")[0]["data-sftp"]

    response = em_web_authed.get(
        "/connection/" + connection_id + "/removeSftp/" + el_id, follow_redirects=True
    )
    assert response.status_code == 200


def test_remove_gpg_connection(em_web_authed):
    # get connection and db id
    response = em_web_authed.get("/connection")
    # open first connection editor
    soup = BeautifulSoup(response.data)
    url = soup.find("a", attrs={"title": "Edit Connection"})["href"]
    connection_id = re.findall(r"\d+", url)[0]
    response = em_web_authed.get(url)

    # get el id
    soup = BeautifulSoup(response.data)
    el_id = soup.select("div.em-drop[data-gpg]")[0]["data-gpg"]

    response = em_web_authed.get(
        "/connection/" + connection_id + "/removeGpg/" + el_id, follow_redirects=True
    )
    assert response.status_code == 200


def test_remove_smb_connection(em_web_authed):
    # get connection and db id
    response = em_web_authed.get("/connection")
    # open first connection editor
    soup = BeautifulSoup(response.data)
    url = soup.find("a", attrs={"title": "Edit Connection"})["href"]
    connection_id = re.findall(r"\d+", url)[0]
    response = em_web_authed.get(url)

    # get el id
    soup = BeautifulSoup(response.data)
    el_id = soup.select("div.em-drop[data-smb]")[0]["data-smb"]

    response = em_web_authed.get(
        "/connection/" + connection_id + "/removeSmb/" + el_id, follow_redirects=True
    )
    assert response.status_code == 200


def test_remove_database_connection(em_web_authed):
    # get connection and db id
    response = em_web_authed.get("/connection")
    # open first connection editor
    soup = BeautifulSoup(response.data)
    url = soup.find("a", attrs={"title": "Edit Connection"})["href"]
    connection_id = re.findall(r"\d+", url)[0]
    response = em_web_authed.get(url)

    # get el id
    soup = BeautifulSoup(response.data)
    el_id = soup.select("div.em-drop[data-database]")[0]["data-database"]

    response = em_web_authed.get(
        "/connection/" + connection_id + "/removeDatabase/" + el_id,
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_remove_ftp_connection(em_web_authed):
    # get connection and db id
    response = em_web_authed.get("/connection")
    # open first connection editor
    soup = BeautifulSoup(response.data)
    url = soup.find("a", attrs={"title": "Edit Connection"})["href"]
    connection_id = re.findall(r"\d+", url)[0]
    response = em_web_authed.get(url)

    # get el id
    soup = BeautifulSoup(response.data)
    el_id = soup.select("div.em-drop[data-ftp]")[0]["data-ftp"]

    response = em_web_authed.get(
        "/connection/" + connection_id + "/removeFtp/" + el_id, follow_redirects=True
    )
    assert response.status_code == 200


def test_remove_connection(em_web_authed):
    # get connection and db id
    response = em_web_authed.get("/connection")
    # open first connection editor
    soup = BeautifulSoup(response.data)
    url = soup.find("a", attrs={"title": "Edit Connection"})["href"]
    connection_id = re.findall(r"\d+", url)[0]

    response = em_web_authed.get(
        "/connection/remove/" + connection_id, follow_redirects=True
    )
    assert response.status_code == 200
