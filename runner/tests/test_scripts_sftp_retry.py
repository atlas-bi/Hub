"""SFTP retry tests."""

from types import SimpleNamespace
from unittest.mock import Mock

from runner.scripts import em_sftp


def test_connect_retries_transient_errors_with_timeouts(monkeypatch) -> None:
    """SFTP retries a transient failure and applies protocol timeouts."""
    first_transport = Mock()
    first_transport.connect.side_effect = em_sftp.paramiko.SSHException("temporary")
    second_transport = Mock()
    transports = iter((first_transport, second_transport))
    monkeypatch.setattr(
        em_sftp.paramiko,
        "Transport",
        lambda *args, **kwargs: next(transports),
    )
    sftp_client = Mock()
    monkeypatch.setattr(
        em_sftp.paramiko.SFTPClient,
        "from_transport",
        lambda transport: sftp_client,
    )
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

    assert em_sftp.connect(connection) == (second_transport, sftp_client)

    first_transport.close.assert_called_once_with()
    sleep.assert_called_once_with(1)
    assert second_transport.banner_timeout == 10
    assert second_transport.auth_timeout == 10
