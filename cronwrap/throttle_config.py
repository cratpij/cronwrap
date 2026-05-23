"""Build ThrottleConfig from environment variables.

Environment variables:
  CRONWRAP_THROTTLE_SECONDS  - minimum seconds between runs (default: 0 = disabled)
  CRONWRAP_THROTTLE_DIR      - directory to store throttle state (default: /var/lib/cronwrap/throttle)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from cronwrap.throttle import ThrottleConfig

_DEFAULT_DIR = Path("/var/lib/cronwrap/throttle")
_DEFAULT_SECONDS = 0


def from_env(job_name: str) -> Optional[ThrottleConfig]:
    """Return a ThrottleConfig built from environment variables.

    Returns None when throttling is disabled (interval == 0).
    """
    raw_seconds = os.environ.get("CRONWRAP_THROTTLE_SECONDS", "").strip()
    try:
        interval = int(raw_seconds)
    except ValueError:
        interval = _DEFAULT_SECONDS

    if interval < 0:
        interval = 0

    raw_dir = os.environ.get("CRONWRAP_THROTTLE_DIR", "").strip()
    state_dir = Path(raw_dir) if raw_dir else _DEFAULT_DIR

    cfg = ThrottleConfig(
        job_name=job_name,
        min_interval_seconds=interval,
        state_dir=state_dir,
    )
    return cfg if cfg.is_enabled else None
