"""Environment variable filtering for cron job execution context."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Variables that are always stripped from the sanitized environment
_SENSITIVE_PATTERNS: List[str] = [
    r".*PASSWORD.*",
    r".*SECRET.*",
    r".*TOKEN.*",
    r".*PRIVATE.*",
    r".*CREDENTIAL.*",
]

_COMPILED: List[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in _SENSITIVE_PATTERNS
]


@dataclass
class EnvFilterConfig:
    """Configuration for environment variable filtering."""

    # Additional variable names to always strip (exact match, case-insensitive)
    strip_vars: List[str] = field(default_factory=list)
    # If set, only these variables are passed through (allowlist mode)
    allowlist: Optional[List[str]] = None
    # Whether to redact sensitive values instead of removing them
    redact: bool = False
    redact_placeholder: str = "***REDACTED***"


def is_sensitive(name: str, extra_strip: List[str]) -> bool:
    """Return True if *name* matches any sensitive pattern or extra strip list."""
    upper = name.upper()
    for pattern in _COMPILED:
        if pattern.fullmatch(upper):
            return True
    return upper in {v.upper() for v in extra_strip}


def filter_env(
    env: Dict[str, str],
    config: EnvFilterConfig,
) -> Dict[str, str]:
    """Return a filtered copy of *env* according to *config*."""
    result: Dict[str, str] = {}

    for key, value in env.items():
        # Allowlist mode: only pass through explicitly listed vars
        if config.allowlist is not None:
            if key not in config.allowlist:
                continue

        if is_sensitive(key, config.strip_vars):
            if config.redact:
                result[key] = config.redact_placeholder
            # else: omit entirely
        else:
            result[key] = value

    return result


def safe_env(config: Optional[EnvFilterConfig] = None) -> Dict[str, str]:
    """Return a filtered snapshot of the current process environment."""
    if config is None:
        config = EnvFilterConfig()
    return filter_env(dict(os.environ), config)
