"""Environment-based configuration loader for HeartbeatConfig."""

from __future__ import annotations

import os
from typing import Optional

from cronwrap.heartbeat import HeartbeatConfig

_DEFAULT_TIMEOUT = 10
_MIN_TIMEOUT = 1


def from_env(env: Optional[dict] = None) -> Optional[HeartbeatConfig]:
    """Build a :class:`HeartbeatConfig` from environment variables.

    Returns *None* when ``CRONWRAP_HEARTBEAT_URL`` is not set so callers can
    skip heartbeat logic entirely.

    Environment variables
    ---------------------
    CRONWRAP_HEARTBEAT_URL        Base ping URL (required to enable feature)
    CRONWRAP_HEARTBEAT_TIMEOUT    HTTP timeout in seconds (default: 10)
    CRONWRAP_HEARTBEAT_ON_FAILURE Also ping on failure, appending /fail
                                  ("1" / "true" to enable, default: off)
    CRONWRAP_HEARTBEAT_FAIL_SUFFIX  Suffix appended on failure (default: /fail)
    """
    source = env if env is not None else os.environ

    url = source.get("CRONWRAP_HEARTBEAT_URL", "").strip() or None
    if url is None:
        return None

    raw_timeout = source.get("CRONWRAP_HEARTBEAT_TIMEOUT", "")
    try:
        timeout = max(_MIN_TIMEOUT, int(raw_timeout))
    except (ValueError, TypeError):
        timeout = _DEFAULT_TIMEOUT

    raw_on_failure = source.get("CRONWRAP_HEARTBEAT_ON_FAILURE", "").strip().lower()
    ping_on_failure = raw_on_failure in ("1", "true", "yes")

    failure_suffix = source.get("CRONWRAP_HEARTBEAT_FAIL_SUFFIX", "/fail").strip() or "/fail"

    return HeartbeatConfig(
        url=url,
        timeout=timeout,
        ping_on_failure=ping_on_failure,
        failure_suffix=failure_suffix,
    )
