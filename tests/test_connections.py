# flake8: noqa,
# pylint: skip-file
import pytest


def test_connections_home(em_web_authed):
    assert em_web_authed.get("/connection").status_code == 200
