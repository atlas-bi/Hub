"""SMTP delivery regression tests."""

from types import SimpleNamespace
from unittest.mock import Mock

from flask import Flask

from runner.scripts import em_smtp


def test_email_and_sms_use_tls_and_authentication(monkeypatch) -> None:
    """Both SMTP delivery paths negotiate TLS before authentication."""
    servers = [Mock(), Mock()]
    smtp = Mock(side_effect=servers)
    monkeypatch.setattr(em_smtp.smtplib, "SMTP", smtp)
    monkeypatch.setattr(em_smtp.db, "session", Mock())

    app = Flask(__name__)
    app.config.update(
        SMTP_SERVER="smtp.hospital.test",
        SMTP_PORT=587,
        SMTP_USE_TLS=True,
        SMTP_USERNAME="hub",
        SMTP_PASSWORD="secret",
        SMTP_SENDER_NAME="Hospital Hub",
        SMTP_SENDER_EMAIL="hub@hospital.test",
        SMTP_SUBJECT_PREFIX="[Hub] ",
    )
    task = SimpleNamespace(id=12)

    with app.app_context():
        em_smtp.Smtp(
            task=task,
            run_id="run-1",
            recipients="ops@hospital.test;15551234567@sms.test",
            subject="Patient export",
            message="<p>Complete</p>",
            short_message="Patient export complete",
            attachments=[],
        )

    assert smtp.call_count == 2
    for server in servers:
        server.starttls.assert_called_once_with()
        server.login.assert_called_once_with("hub", "secret")
        server.sendmail.assert_called_once()
        server.quit.assert_called_once_with()
