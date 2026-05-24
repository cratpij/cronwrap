"""Retry policy configuration and delay computation for failed jobs."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BASE_DELAY = 5.0
_DEFAULT_MAX_DELAY = 60.0


@dataclass
class RetryPolicy:
    """Encapsulates retry behaviour for a cron job."""

    max_retries: int = _DEFAULT_MAX_RETRIES
    base_delay: float = _DEFAULT_BASE_DELAY
    max_delay: float = _DEFAULT_MAX_DELAY
    exponential: bool = True
    jitter: bool = False

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if self.base_delay < 0:
            raise ValueError("base_delay must be >= 0")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")

    def is_enabled(self) -> bool:
        """Return True when at least one retry is allowed."""
        return self.max_retries > 0

    def compute_delay(self, attempt: int) -> float:
        """Return the delay in seconds before *attempt* (1-based).

        *attempt* == 1 means the first retry after the initial failure.
        """
        if attempt < 1:
            return 0.0
        if not self.exponential:
            delay = self.base_delay
        else:
            delay = self.base_delay * (2 ** (attempt - 1))
        return min(delay, self.max_delay)

    def should_retry(self, attempt: int) -> bool:
        """Return True when *attempt* (1-based) is within the allowed limit."""
        return attempt <= self.max_retries


def from_env() -> Optional[RetryPolicy]:
    """Build a :class:`RetryPolicy` from environment variables.

    Returns ``None`` when ``CRONWRAP_MAX_RETRIES`` is not set.
    """
    raw_retries = os.environ.get("CRONWRAP_MAX_RETRIES")
    if raw_retries is None:
        return None

    try:
        max_retries = int(raw_retries)
    except ValueError:
        max_retries = _DEFAULT_MAX_RETRIES

    try:
        base_delay = float(os.environ.get("CRONWRAP_RETRY_BASE_DELAY", _DEFAULT_BASE_DELAY))
    except ValueError:
        base_delay = _DEFAULT_BASE_DELAY

    try:
        max_delay = float(os.environ.get("CRONWRAP_RETRY_MAX_DELAY", _DEFAULT_MAX_DELAY))
    except ValueError:
        max_delay = _DEFAULT_MAX_DELAY

    exponential = os.environ.get("CRONWRAP_RETRY_EXPONENTIAL", "true").lower() != "false"
    jitter = os.environ.get("CRONWRAP_RETRY_JITTER", "false").lower() == "true"

    return RetryPolicy(
        max_retries=max(0, max_retries),
        base_delay=max(0.0, base_delay),
        max_delay=max(0.0, max_delay),
        exponential=exponential,
        jitter=jitter,
    )
