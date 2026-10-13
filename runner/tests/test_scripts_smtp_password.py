"""SMTP credential regression tests."""

from types import SimpleNamespace
from unittest.mock import Mock

from flask import Flask

from runner.scripts import em_smtp


def test_missing_smtp_password_is_sent_as_empty_string(monkeypatch) -> None:
    """SMTP authentication receives a string when no password is configured."""
    server = Mock()
    monkeypatch.setattr(em_smtp.smtplib, "SMTP", Mock(return_value=server))
    monkeypatch.setattr(em_smtp.db, "session", Mock())

    app = Flask(__name__)
    app.config.update(
        SMTP_SERVER="smtp.hospital.test",
        SMTP_PORT=587,
        SMTP_USE_TLS=True,
        SMTP_USERNAME="hub",
        SMTP_SENDER_NAME="Hospital Hub",
        SMTP_SENDER_EMAIL="hub@hospital.test",
        SMTP_SUBJECT_PREFIX="[Hub] ",
    )
    with app.app_context():
        em_smtp.Smtp(
            task=SimpleNamespace(id=12),
            run_id="run-1",
            recipients="ops@hospital.test",
            subject="Patient export",
            message="<p>Complete</p>",
            short_message="Complete",
            attachments=[],
        )

    server.login.assert_called_once_with("hub", "")
