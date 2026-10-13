"""Bounded SSH/SFTP connection retry tests."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from runner.scripts import em_sftp, em_ssh


@pytest.mark.parametrize(
    "error_type",
    [EOFError, OSError, em_ssh.paramiko.SSHException],
)
def test_ssh_connection_stops_after_three_failures_and_closes_sessions(monkeypatch, error_type):
    """SSH bounds retries and closes every failed session."""
    sessions = [Mock() for _ in range(3)]
    for session in sessions:
        session.connect.side_effect = error_type("temporary")
    session_factory = Mock(side_effect=sessions)
    monkeypatch.setattr(em_ssh.paramiko, "SSHClient", session_factory)
    monkeypatch.setattr(em_ssh, "em_decrypt", lambda value, key: "password")
    monkeypatch.setattr(
        em_ssh,
        "app",
        SimpleNamespace(config={"PASS_KEY": "test-key"}),
    )
    sleep = Mock()
    monkeypatch.setattr(em_ssh.time, "sleep", sleep)
    connection = SimpleNamespace(address="server", port=2222, username="user", password="secret")

    with pytest.raises(ValueError, match="temporary"):
        em_ssh.connect(connection)

    assert session_factory.call_count == 3
    for session in sessions:
        session.close.assert_called_once_with()
    sleep.assert_any_call(1)


@pytest.mark.parametrize(
    "error_type",
    [
        EOFError,
        OSError,
        em_sftp.paramiko.ssh_exception.AuthenticationException,
        em_sftp.paramiko.SSHException,
    ],
)
def test_sftp_connection_stops_after_three_failures_and_closes_transports(monkeypatch, error_type):
    """SFTP bounds retries and closes every failed transport."""
    transports = [Mock() for _ in range(3)]
    for transport in transports:
        transport.connect.side_effect = error_type("temporary")
    transport_factory = Mock(side_effect=transports)
    monkeypatch.setattr(em_sftp.paramiko, "Transport", transport_factory)
    monkeypatch.setattr(em_sftp, "connection_key", lambda connection: None)
    monkeypatch.setattr(em_sftp, "em_decrypt", lambda value, key: "password")
    monkeypatch.setattr(
        em_sftp,
        "app",
        SimpleNamespace(config={"PASS_KEY": "test-key"}),
    )
    sleep = Mock()
    monkeypatch.setattr(em_sftp.time, "sleep", sleep)
    connection = SimpleNamespace(
        address="server",
        port=2222,
        username="user",
        password="secret",
        key=None,
        key_password=None,
    )

    with pytest.raises(ValueError, match="temporary"):
        em_sftp.connect(connection)

    assert transport_factory.call_count == 3
    for transport in transports:
        transport.close.assert_called_once_with()
    sleep.assert_any_call(1)
