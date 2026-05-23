"""Rate-limiting / throttle support for cron jobs.

Prevents a job from running more frequently than a configured minimum
interval, regardless of how often the cron expression fires.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ThrottleConfig:
    """Configuration for job throttling."""

    job_name: str
    min_interval_seconds: int  # 0 means disabled
    state_dir: Path = field(default_factory=lambda: Path("/var/lib/cronwrap/throttle"))

    @property
    def is_enabled(self) -> bool:
        return self.min_interval_seconds > 0


@dataclass
class ThrottleState:
    """Persisted state for a throttled job."""

    last_run_at: float  # Unix timestamp; 0.0 means never run

    def to_dict(self) -> dict:
        return {"last_run_at": self.last_run_at}

    @classmethod
    def from_dict(cls, data: dict) -> "ThrottleState":
        return cls(last_run_at=float(data.get("last_run_at", 0.0)))


class ThrottleBlocked(Exception):
    """Raised when a job is blocked by the throttle."""

    def __init__(self, job_name: str, seconds_remaining: float) -> None:
        self.job_name = job_name
        self.seconds_remaining = seconds_remaining
        super().__init__(
            f"Job '{job_name}' throttled; {seconds_remaining:.0f}s remaining before next allowed run."
        )


def _state_path(cfg: ThrottleConfig) -> Path:
    return cfg.state_dir / f"{cfg.job_name}.throttle.json"


def load_state(cfg: ThrottleConfig) -> Optional[ThrottleState]:
    path = _state_path(cfg)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return ThrottleState.from_dict(data)
    except (json.JSONDecodeError, OSError):
        return None


def save_state(cfg: ThrottleConfig, state: ThrottleState) -> None:
    path = _state_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict()))


def check_throttle(cfg: ThrottleConfig, now: Optional[float] = None) -> None:
    """Raise ThrottleBlocked if the job should not run yet."""
    if not cfg.is_enabled:
        return
    now = now if now is not None else time.time()
    state = load_state(cfg)
    if state is None or state.last_run_at == 0.0:
        return
    elapsed = now - state.last_run_at
    remaining = cfg.min_interval_seconds - elapsed
    if remaining > 0:
        raise ThrottleBlocked(cfg.job_name, remaining)


def record_run(cfg: ThrottleConfig, now: Optional[float] = None) -> None:
    """Persist the current timestamp as the last run time."""
    if not cfg.is_enabled:
        return
    now = now if now is not None else time.time()
    save_state(cfg, ThrottleState(last_run_at=now))
