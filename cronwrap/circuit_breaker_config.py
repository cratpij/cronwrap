"""Load CircuitBreakerConfig from environment variables."""
from __future__ import annotations

import os
from typing import Optional

from cronwrap.circuit_breaker import CircuitBreakerConfig

_DEFAULT_FAILURE_THRESHOLD = 5
_DEFAULT_RECOVERY_TIMEOUT = 300
_DEFAULT_STATE_DIR = "/tmp/cronwrap/circuit"


def _parse_int(value: Optional[str], default: int, minimum: int = 0) -> int:
    if value is None:
        return default
    try:
        parsed = int(value)
        return max(minimum, parsed)
    except ValueError:
        return default


def from_env() -> Optional[CircuitBreakerConfig]:
    """Return a CircuitBreakerConfig populated from environment variables.

    Returns None if CRONWRAP_CB_FAILURE_THRESHOLD is unset, indicating the
    circuit breaker feature is not configured.

    Environment variables:
        CRONWRAP_CB_FAILURE_THRESHOLD  consecutive failures before opening (default 5)
        CRONWRAP_CB_RECOVERY_TIMEOUT   seconds before half-open attempt (default 300)
        CRONWRAP_CB_STATE_DIR          directory for state files
    """
    threshold_raw = os.environ.get("CRONWRAP_CB_FAILURE_THRESHOLD")
    if threshold_raw is None:
        return None

    threshold = _parse_int(threshold_raw, _DEFAULT_FAILURE_THRESHOLD, minimum=0)
    recovery = _parse_int(
        os.environ.get("CRONWRAP_CB_RECOVERY_TIMEOUT"),
        _DEFAULT_RECOVERY_TIMEOUT,
        minimum=0,
    )
    state_dir = os.environ.get("CRONWRAP_CB_STATE_DIR", _DEFAULT_STATE_DIR)

    return CircuitBreakerConfig(
        failure_threshold=threshold,
        recovery_timeout=recovery,
        state_dir=state_dir,
    )
