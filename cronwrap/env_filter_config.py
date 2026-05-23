"""Load EnvFilterConfig from environment variables."""
from __future__ import annotations

import os
from typing import Optional

from cronwrap.env_filter import EnvFilterConfig

_ENV_STRIP_VARS = "CRONWRAP_ENV_STRIP_VARS"
_ENV_ALLOWLIST = "CRONWRAP_ENV_ALLOWLIST"
_ENV_REDACT = "CRONWRAP_ENV_REDACT"
_ENV_REDACT_PLACEHOLDER = "CRONWRAP_ENV_REDACT_PLACEHOLDER"


def from_env() -> Optional[EnvFilterConfig]:
    """Build an EnvFilterConfig from environment variables.

    Returns None if no relevant env vars are set, signalling that
    the caller should use a plain default config.
    """
    strip_raw = os.environ.get(_ENV_STRIP_VARS, "")
    allowlist_raw = os.environ.get(_ENV_ALLOWLIST, "")
    redact_raw = os.environ.get(_ENV_REDACT, "").strip().lower()
    placeholder = os.environ.get(_ENV_REDACT_PLACEHOLDER, "***REDACTED***")

    strip_vars = [v.strip() for v in strip_raw.split(",") if v.strip()]
    allowlist = (
        [v.strip() for v in allowlist_raw.split(",") if v.strip()]
        if allowlist_raw.strip()
        else None
    )
    redact = redact_raw in ("1", "true", "yes")

    if not strip_vars and allowlist is None and not redact:
        return None

    return EnvFilterConfig(
        strip_vars=strip_vars,
        allowlist=allowlist,
        redact=redact,
        redact_placeholder=placeholder,
    )
