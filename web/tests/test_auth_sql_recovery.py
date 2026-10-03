"""Regression tests for transient SQLAlchemy failures in authentication."""

from unittest.mock import Mock

import pytest
from sqlalchemy.exc import OperationalError, PendingRollbackError

from web import create_app
from web.web import auth


def _operational_error() -> OperationalError:
    return OperationalError("SELECT 1", {}, Exception("connection lost"))


def _pending_rollback_error() -> PendingRollbackError:
    return PendingRollbackError("transaction is inactive")


ERROR_FACTORIES = [
    pytest.param(_operational_error, id="operational"),
    pytest.param(_pending_rollback_error, id="pending"),
]


@pytest.mark.parametrize("error_factory", ERROR_FACTORIES)
def test_load_user_rolls_back_and_retries_lookup(monkeypatch, error_factory) -> None:
    """A transient user lookup failure is rolled back and retried once."""
    user = object()
    app = create_app()

    class RetryQuery:
        calls = 0

        def filter_by(self, **_kwargs):
            return self

        def first(self):
            self.calls += 1
            if self.calls == 1:
                raise error_factory()
            return user

    with app.app_context():
        query = RetryQuery()
        rollback = Mock()
        monkeypatch.setattr(auth.User, "query", query, raising=False)
        monkeypatch.setattr(auth.db.session, "rollback", rollback)

        assert auth.load_user("7") is user
        assert query.calls == 2
        rollback.assert_called_once_with()


@pytest.mark.parametrize("error_factory", ERROR_FACTORIES)
def test_log_login_rolls_back_and_retries_commit(monkeypatch, error_factory) -> None:
    """A transient login insert failure is rolled back and retried once."""
    app = create_app()
    with app.app_context():
        add = Mock()
        commit = Mock(side_effect=[error_factory(), None])
        rollback = Mock()
        monkeypatch.setattr(auth.db.session, "add", add)
        monkeypatch.setattr(auth.db.session, "commit", commit)
        monkeypatch.setattr(auth.db.session, "rollback", rollback)

        auth.log_login("clinician", 1)

        assert add.call_count == 2
        assert commit.call_count == 2
        rollback.assert_called_once_with()
