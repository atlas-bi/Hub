"""Tests for database connection retry helper."""

from typing import List

import pytest

from runner.scripts.em_connect_retry import with_connect_retry


def test_with_connect_retry_succeeds_without_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return immediately when the first connect attempt succeeds."""
    sleeps: List[float] = []
    monkeypatch.setattr("runner.scripts.em_connect_retry.time.sleep", sleeps.append)

    assert with_connect_retry(lambda: "ok") == "ok"
    assert sleeps == []


def test_with_connect_retry_retries_once_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sleep once and retry when the first connect attempt fails."""
    sleeps: List[float] = []
    monkeypatch.setattr("runner.scripts.em_connect_retry.time.sleep", sleeps.append)

    attempts = {"count": 0}

    def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise ConnectionError("temporary")
        return "recovered"

    assert with_connect_retry(flaky, retry_on=(ConnectionError,), delay_seconds=5) == "recovered"
    assert attempts["count"] == 2
    assert sleeps == [5]


def test_with_connect_retry_raises_after_exhausted_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise the last error after the retry budget is exhausted."""
    sleeps: List[float] = []
    monkeypatch.setattr("runner.scripts.em_connect_retry.time.sleep", sleeps.append)

    def always_fail() -> str:
        raise ConnectionError("down")

    with pytest.raises(ConnectionError, match="down"):
        with_connect_retry(always_fail, retry_on=(ConnectionError,), attempts=2, delay_seconds=5)

    assert sleeps == [5]
