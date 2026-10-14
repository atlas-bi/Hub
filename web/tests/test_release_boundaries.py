"""Regression tests for runtime boundaries introduced in a52d6ca."""

import logging.config
import runpy
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock

import alembic.context
from flask import Flask
from sqlalchemy.pool import NullPool

from config import Config
from web.extensions import csrf
from web.web import saml_auth


def test_saml_acs_accepts_identity_provider_post_without_csrf(monkeypatch) -> None:
    """The identity provider cannot send a Flask-WTF CSRF token."""

    class AuthnResponse:
        @staticmethod
        def get_identity() -> dict[str, list[str]]:
            return {"groups": []}

    parse_response = MagicMock(return_value=AuthnResponse())
    saml_client = SimpleNamespace(parse_authn_request_response=parse_response)
    monkeypatch.setattr(saml_auth.SAML, "saml_client_for", lambda _self: saml_client)

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="test",
        TESTING=True,
        WTF_CSRF_ENABLED=True,
        SAML_ATTR_MAP={"groups": "groups"},
        REQUIRED_GROUPS=["hospital-users"],
        NOT_AUTHORIZED_URL="not_authorized",
    )

    @app.get("/not-authorized")
    def not_authorized() -> str:
        return "not authorized"

    app.register_blueprint(saml_auth.login_bp)
    csrf.init_app(app)

    response = app.test_client().post("/saml2/acs/", data={"SAMLResponse": "signed-idp-response"})

    assert response.status_code == 302
    assert response.location.endswith("/not-authorized")
    parse_response.assert_called_once()


def test_production_database_pool_stays_bounded() -> None:
    """Each gunicorn worker must not reserve a large connection pool."""
    assert Config.SQLALCHEMY_ENGINE_OPTIONS == {
        "pool_recycle": 1800,
        "pool_pre_ping": True,
        "pool_size": 2,
        "max_overflow": 5,
    }


def test_online_migrations_use_and_dispose_a_null_pool_engine(monkeypatch) -> None:
    """Alembic must use one temporary connection instead of the app pool."""
    migration_url = MagicMock()
    migration_url.render_as_string.return_value = "postgresql://test"
    app_engine = SimpleNamespace(url=migration_url)
    target_db = SimpleNamespace(
        get_engine=lambda: app_engine,
        metadata=object(),
        engine=app_engine,
    )
    app = Flask(__name__)
    app.extensions["migrate"] = SimpleNamespace(
        db=target_db,
        configure_args={},
    )

    alembic_config = SimpleNamespace(
        config_file_name="alembic.ini",
        cmd_opts=SimpleNamespace(autogenerate=False),
        set_main_option=MagicMock(),
        get_main_option=MagicMock(return_value="postgresql://test"),
    )
    migration_engine = MagicMock()
    migration_engine.connect.return_value = nullcontext(MagicMock())
    create_engine = MagicMock(return_value=migration_engine)

    monkeypatch.setattr(alembic.context, "config", alembic_config, raising=False)
    monkeypatch.setattr(alembic.context, "is_offline_mode", lambda: False)
    monkeypatch.setattr(alembic.context, "configure", MagicMock())
    monkeypatch.setattr(alembic.context, "begin_transaction", nullcontext)
    run_migrations = MagicMock()
    monkeypatch.setattr(alembic.context, "run_migrations", run_migrations)
    monkeypatch.setattr(logging.config, "fileConfig", lambda _path: None)
    monkeypatch.setattr("sqlalchemy.create_engine", create_engine)

    with app.app_context():
        runpy.run_path("migrations/env.py")

    create_engine.assert_called_once_with(migration_url, poolclass=NullPool)
    run_migrations.assert_called_once_with()
    migration_engine.dispose.assert_called_once_with()
