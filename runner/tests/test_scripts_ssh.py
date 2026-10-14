"""SSH connection tests."""

from types import SimpleNamespace
from unittest.mock import Mock

import paramiko

from runner.scripts.em_ssh import connect


def test_connect_retries_transient_errors_with_timeouts(monkeypatch) -> None:
    """SSH retries a transient failure, with bounded connection timeouts."""
    session = Mock()
    session.connect.side_effect = [paramiko.SSHException("temporary"), None]
    monkeypatch.setattr("runner.scripts.em_ssh.paramiko.SSHClient", Mock(return_value=session))
    monkeypatch.setattr("runner.scripts.em_ssh.em_decrypt", lambda value, key: "password")
    monkeypatch.setattr(
        "runner.scripts.em_ssh.app",
        SimpleNamespace(config={"PASS_KEY": "test-key"}),
    )
    sleep = Mock()
    monkeypatch.setattr("runner.scripts.em_ssh.time.sleep", sleep)
    connection = SimpleNamespace(address="server", port=2222, username="user", password="secret")

    assert connect(connection) is session

    assert session.connect.call_count == 2
    session.connect.assert_called_with(
        hostname="server",
        port=2222,
        username="user",
        password="password",
        timeout=5,
        banner_timeout=10,
        auth_timeout=10,
        allow_agent=False,
        look_for_keys=False,
    )
    session.close.assert_called_once_with()
    sleep.assert_called_once_with(1)
