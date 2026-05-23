"""Environment-based configuration for alert throttling."""

from __future__ import annotations

import os
from pathlib import Path

from cronwrap.alert import AlertConfig

_DEFAULT_COOLDOWN = 3600  # seconds
_DEFAULT_STATE_DIR = Path("/var/lib/cronwrap/alerts")


def from_env() -> AlertConfig:
    """Build an AlertConfig from environment variables.

    CRONWRAP_ALERT_DIR   – directory to store alert state files
                           (default: /var/lib/cronwrap/alerts)
    CRONWRAP_ALERT_COOLDOWN – cooldown in seconds between repeated alerts
                           (default: 3600)
    """
    raw_dir = os.environ.get("CRONWRAP_ALERT_DIR", "")
    state_dir = Path(raw_dir) if raw_dir else _DEFAULT_STATE_DIR

    raw_cooldown = os.environ.get("CRONWRAP_ALERT_COOLDOWN", "")
    try:
        cooldown = int(raw_cooldown) if raw_cooldown else _DEFAULT_COOLDOWN
    except ValueError:
        cooldown = _DEFAULT_COOLDOWN

    return AlertConfig(state_dir=state_dir, cooldown_seconds=max(0, cooldown))
