"""Database-free tests for database adapter connection retries."""

import time
from unittest.mock import Mock

import pytest

from runner.scripts import em_jdbc, em_postgres, em_sqlserver

ADAPTERS = [
    pytest.param(
        em_jdbc.connect,
        em_jdbc.jaydebeapi,
        em_jdbc.jaydebeapi.Error,
        ("jclassname=Example,url=jdbc:example,jars=example.jar,libs=libs",),
        id="jdbc",
    ),
    pytest.param(
        em_postgres.connect,
        em_postgres.psycopg2,
        em_postgres.psycopg2.Error,
        ("postgresql://db.example.test/app", 1),
        id="postgres",
    ),
    pytest.param(
        em_sqlserver.connect,
        em_sqlserver.pyodbc,
        em_sqlserver.pyodbc.Error,
        ("SERVER=db.example.test", 1),
        id="sqlserver",
    ),
]


@pytest.mark.parametrize(("connect", "driver", "error_type", "args"), ADAPTERS)
def test_adapter_retries_driver_errors_then_connects(
    monkeypatch: pytest.MonkeyPatch,
    connect,
    driver,
    error_type,
    args,
) -> None:
    """Each adapter retries one driver error and returns its connection pair."""
    connection = Mock()
    cursor = Mock()
    connection.cursor.return_value = cursor
    driver_connect = Mock(side_effect=[error_type("temporary"), connection])
    monkeypatch.setattr(driver, "connect", driver_connect)
    sleeps = []
    monkeypatch.setattr(time, "sleep", sleeps.append)

    assert connect(*args) == (connection, cursor)
    assert driver_connect.call_count == 2
    assert sleeps == [5]


@pytest.mark.parametrize(("connect", "driver", "_error_type", "args"), ADAPTERS)
def test_adapter_does_not_retry_unrelated_errors(
    monkeypatch: pytest.MonkeyPatch,
    connect,
    driver,
    _error_type,
    args,
) -> None:
    """Each adapter lets non-driver configuration errors pass through once."""
    driver_connect = Mock(side_effect=ValueError("bad configuration"))
    monkeypatch.setattr(driver, "connect", driver_connect)
    sleeps = []
    monkeypatch.setattr(time, "sleep", sleeps.append)

    with pytest.raises(ValueError, match="bad configuration"):
        connect(*args)

    assert driver_connect.call_count == 1
    assert sleeps == []
