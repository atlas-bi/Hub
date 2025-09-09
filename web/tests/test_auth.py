"""Test auth.

run with::

   poetry run pytest web/tests/test_auth.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest web/tests/test_auth.py::test_next \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings

"""

from flask import url_for
from flask.wrappers import Response
from flask_login import current_user
from pytest import fixture


def test_index(client_fixture: fixture) -> None:
    """Verify that redirection to login page works.

    Parameters:
        client_fixture: client fixture
    """
    res = client_fixture.get("/")
    # should redirect to login page
    if not client_fixture.application.config.get("TEST"):
        assert res.status_code == 302
        assert "/login" in res.get_data(as_text=True)


def login(client_fixture: fixture, username: str, password: str) -> Response:
    # 302 becuase tests autologin.
    assert client_fixture.get("/login").status_code == 302

    return client_fixture.post(
        url_for("auth_bp.login"),
        data=dict(user=username, password=password),
        follow_redirects=True,
    )


def logout(client_fixture: fixture) -> Response:
    return client_fixture.get("/logout", follow_redirects=True)


def test_login_logout(client_fixture: fixture) -> None:
    """Make sure login and logout works."""

    logout(client_fixture)
    username = "mr-cool"
    password = ""

    page = login(client_fixture, username, password)
    assert page.status_code == 200
    assert b"Dashboard" in page.data

    assert current_user.get_id()

    # verify we stay logged in
    page = client_fixture.get("/login", follow_redirects=True)
    assert page.status_code == 200
    assert b"Dashboard" in page.data

    page = logout(client_fixture)
    assert page.status_code == 200
    assert b"Bye." in page.data

    # test doesn't work with auto login.
    # page = login(client_fixture, username + "x", password)
    # assert b"Invalid login, please try again!" in page.data


def test_not_authorized(client_fixture: fixture) -> None:
    page = client_fixture.get("/not_authorized", follow_redirects=True)
    assert page.status_code == 200


def test_next(client_fixture: fixture) -> None:
    username = "mr-cool"
    password = ""

    page = client_fixture.post(
        "/login?next=https://nothing?asdf=asdf",
        data={"user": username, "password": password},
    )

    assert page.status_code == 400

    # check a valid next
    page = client_fixture.post(
        "/login?next=https://localhost/", data={"user": username, "password": password}
    )

    assert page.status_code == 302

    # check an invalid next
    page = client_fixture.post(
        "/login?next=https://google.com/", data={"user": username, "password": password}
    )
    assert page.status_code == 400
