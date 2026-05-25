"""Build a :class:`DeadlineConfig` from environment variables.

Environment variables
---------------------
CRONWRAP_DEADLINE_SECONDS
    Maximum number of seconds a job may be delayed past its scheduled time
    before it is skipped.  Defaults to ``0`` (disabled).
CRONWRAP_SCHEDULED_AT
    Unix timestamp (float) of the intended scheduled time.  Required when
    ``CRONWRAP_DEADLINE_SECONDS`` is set.
"""
from __future__ import annotations

import os
from typing import Optional

from cronwrap.deadline import DeadlineConfig

_DEFAULT_MAX_DELAY = 0


def _parse_int(value: str, default: int) -> int:
    try:
        parsed = int(value)
        return max(0, parsed)
    except (ValueError, TypeError):
        return default


def _parse_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def from_env(env: Optional[dict] = None) -> Optional[DeadlineConfig]:
    """Return a :class:`DeadlineConfig` built from *env* (or ``os.environ``).

    Returns ``None`` when ``CRONWRAP_DEADLINE_SECONDS`` is absent or zero.
    """
    source = env if env is not None else os.environ

    raw_delay = source.get("CRONWRAP_DEADLINE_SECONDS", "")
    max_delay = _parse_int(raw_delay, _DEFAULT_MAX_DELAY)
    if max_delay <= 0:
        return None

    raw_scheduled = source.get("CRONWRAP_SCHEDULED_AT", "")
    scheduled_at = _parse_float(raw_scheduled) if raw_scheduled else None

    return DeadlineConfig(max_delay_seconds=max_delay, scheduled_at=scheduled_at)
