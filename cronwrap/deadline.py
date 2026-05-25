"""Deadline enforcement: skip a job run if it starts too late."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DeadlineConfig:
    """Configuration for deadline enforcement.

    If ``max_delay_seconds`` is positive, a job invocation that starts more
    than that many seconds after its scheduled time will be skipped.
    """

    max_delay_seconds: int = 0
    # Unix timestamp representing the intended scheduled time.
    scheduled_at: Optional[float] = field(default=None, repr=False)

    def is_enabled(self) -> bool:
        """Return True when deadline enforcement is active."""
        return self.max_delay_seconds > 0 and self.scheduled_at is not None


class DeadlineMissed(Exception):
    """Raised when a job is started after its deadline."""

    def __init__(self, delay: float, max_delay: int) -> None:
        self.delay = delay
        self.max_delay = max_delay
        super().__init__(
            f"Job started {delay:.1f}s after scheduled time "
            f"(max allowed: {max_delay}s)"
        )


def check_deadline(cfg: DeadlineConfig, now: Optional[float] = None) -> None:
    """Raise :class:`DeadlineMissed` if the deadline has been exceeded.

    Parameters
    ----------
    cfg:
        Deadline configuration.
    now:
        Current Unix timestamp; defaults to ``time.time()``.
    """
    if not cfg.is_enabled():
        return

    current = now if now is not None else time.time()
    assert cfg.scheduled_at is not None  # guarded by is_enabled()
    delay = current - cfg.scheduled_at
    if delay > cfg.max_delay_seconds:
        raise DeadlineMissed(delay=delay, max_delay=cfg.max_delay_seconds)
