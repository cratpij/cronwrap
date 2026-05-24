"""Build a DependencyConfig from environment variables."""

from __future__ import annotations

import os
from typing import Optional

from cronwrap.dependency import DependencyConfig

_DEFAULT_MAX_AGE = 86400
_DEFAULT_HISTORY_DIR = "/var/lib/cronwrap/history"


def from_env() -> Optional[DependencyConfig]:
    """Return a DependencyConfig populated from environment variables, or None.

    Environment variables
    ---------------------
    CRONWRAP_DEPENDS_ON
        Comma-separated list of upstream job names.
    CRONWRAP_DEPENDS_MAX_AGE
        Maximum age (in seconds) of the upstream success. Defaults to 86400.
    CRONWRAP_HISTORY_DIR
        Directory that holds per-job history files.
    """
    raw = os.environ.get("CRONWRAP_DEPENDS_ON", "").strip()
    if not raw:
        return None

    job_names = [name.strip() for name in raw.split(",") if name.strip()]
    if not job_names:
        return None

    max_age = _DEFAULT_MAX_AGE
    raw_age = os.environ.get("CRONWRAP_DEPENDS_MAX_AGE", "").strip()
    if raw_age:
        try:
            parsed = int(raw_age)
            max_age = max(0, parsed)
        except ValueError:
            pass

    history_dir = os.environ.get("CRONWRAP_HISTORY_DIR", _DEFAULT_HISTORY_DIR).strip()
    if not history_dir:
        history_dir = _DEFAULT_HISTORY_DIR

    return DependencyConfig(
        job_names=job_names,
        max_age_seconds=max_age,
        history_dir=history_dir,
    )
