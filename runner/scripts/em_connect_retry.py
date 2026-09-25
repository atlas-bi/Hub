"""Retry helper for flaky database service connections."""

from __future__ import annotations

import time
from typing import Callable, Tuple, Type, TypeVar

T = TypeVar("T")

DEFAULT_ATTEMPTS = 2
DEFAULT_DELAY_SECONDS = 5


def with_connect_retry(
    connect_once: Callable[[], T],
    *,
    retry_on: Tuple[Type[BaseException], ...] = (Exception,),
    attempts: int = DEFAULT_ATTEMPTS,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
) -> T:
    """Run a connect callable, retrying after a short delay on failure.

    Matches the behavior requested for intermittent SQL Server / service
    connectivity: try again after about five seconds before giving up.
    """
    last_error: BaseException | None = None
    for attempt in range(attempts):
        try:
            return connect_once()
        except retry_on as exc:
            last_error = exc
            if attempt + 1 >= attempts:
                break
            time.sleep(delay_seconds)
    assert last_error is not None
    raise last_error
