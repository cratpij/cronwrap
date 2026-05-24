"""Exponential backoff configuration and delay calculation for retry logic."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


@dataclass
class BackoffConfig:
    """Configuration for exponential backoff between retries."""

    base_delay: float = 1.0      # seconds for the first retry
    max_delay: float = 60.0      # upper cap on computed delay
    multiplier: float = 2.0      # growth factor per attempt
    jitter: bool = True          # add random ±25 % jitter to each delay

    def __post_init__(self) -> None:
        if self.base_delay < 0:
            raise ValueError("base_delay must be >= 0")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.multiplier < 1.0:
            raise ValueError("multiplier must be >= 1.0")


def is_enabled(cfg: BackoffConfig) -> bool:
    """Return True when backoff is active (base_delay > 0)."""
    return cfg.base_delay > 0


def compute_delay(cfg: BackoffConfig, attempt: int) -> float:
    """Return the delay in seconds before *attempt* (0-indexed).

    attempt=0 → first retry, attempt=1 → second retry, …
    """
    if not is_enabled(cfg) or attempt < 0:
        return 0.0

    raw = cfg.base_delay * math.pow(cfg.multiplier, attempt)
    capped = min(raw, cfg.max_delay)

    if cfg.jitter:
        # uniform jitter in [-25 %, +25 %] of capped value
        spread = capped * 0.25
        capped = capped + random.uniform(-spread, spread)
        capped = max(0.0, min(capped, cfg.max_delay))

    return capped


def from_env(env: dict[str, str] | None = None) -> BackoffConfig:
    """Build a BackoffConfig from environment variables.

    CRONWRAP_BACKOFF_BASE_DELAY   float, default 1.0
    CRONWRAP_BACKOFF_MAX_DELAY    float, default 60.0
    CRONWRAP_BACKOFF_MULTIPLIER   float, default 2.0
    CRONWRAP_BACKOFF_JITTER       '0'/'false' disables jitter, default True
    """
    import os
    e = env if env is not None else os.environ

    def _float(key: str, default: float) -> float:
        try:
            return float(e[key])
        except (KeyError, ValueError):
            return default

    def _bool(key: str, default: bool) -> bool:
        val = e.get(key, "").strip().lower()
        if val in ("0", "false", "no", "off"):
            return False
        if val in ("1", "true", "yes", "on"):
            return True
        return default

    return BackoffConfig(
        base_delay=_float("CRONWRAP_BACKOFF_BASE_DELAY", 1.0),
        max_delay=_float("CRONWRAP_BACKOFF_MAX_DELAY", 60.0),
        multiplier=_float("CRONWRAP_BACKOFF_MULTIPLIER", 2.0),
        jitter=_bool("CRONWRAP_BACKOFF_JITTER", True),
    )
