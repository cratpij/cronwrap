"""Optional random delay (jitter) before a job runs to avoid thundering-herd."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JitterConfig:
    """Configuration for pre-job random delay."""

    max_seconds: int = 0
    """Upper bound (inclusive) for the random sleep, in seconds.
    A value of 0 disables jitter entirely."""

    seed: Optional[int] = field(default=None, repr=False)
    """Optional RNG seed – useful for deterministic tests."""

    def is_enabled(self) -> bool:
        """Return True when jitter is active."""
        return self.max_seconds > 0


def sample_delay(cfg: JitterConfig) -> float:
    """Return a random delay in seconds sampled from [0, cfg.max_seconds].

    Returns 0.0 when jitter is disabled.
    """
    if not cfg.is_enabled():
        return 0.0
    rng = random.Random(cfg.seed)
    return rng.uniform(0, cfg.max_seconds)


def apply_jitter(cfg: JitterConfig, *, _sleep=time.sleep) -> float:
    """Sleep for a random duration and return the actual delay applied.

    Parameters
    ----------
    cfg:
        Jitter configuration.
    _sleep:
        Callable used to sleep; injectable for testing.

    Returns
    -------
    float
        Number of seconds slept (0.0 when jitter is disabled).
    """
    delay = sample_delay(cfg)
    if delay > 0:
        _sleep(delay)
    return delay
