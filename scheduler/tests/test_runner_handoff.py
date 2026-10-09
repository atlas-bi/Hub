"""Tests for scheduler-to-runner response handling."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scheduler.functions import _raise_for_runner_error


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (
            SimpleNamespace(ok=False, status_code=503, text="unavailable"),
            "Runner returned HTTP 503: unavailable",
        ),
        (
            SimpleNamespace(
                ok=True,
                status_code=200,
                text="",
                json=lambda: {"error": "runner rejected task"},
            ),
            "Runner returned error: runner rejected task",
        ),
    ],
)
def test_runner_error_responses_raise(response, message) -> None:
    """HTTP failures and runner JSON errors both fail scheduler handoff."""
    with pytest.raises(RuntimeError, match=message):
        _raise_for_runner_error(response)


@pytest.mark.parametrize(
    "response",
    [
        SimpleNamespace(ok=True, status_code=200, json=lambda: {"message": "queued"}),
        SimpleNamespace(ok=True, status_code=200, json=Mock(side_effect=ValueError)),
    ],
)
def test_runner_success_responses_do_not_raise(response) -> None:
    """Successful and non-JSON runner responses do not fail handoff."""
    _raise_for_runner_error(response)
