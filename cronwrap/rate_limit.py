"""Rate limiting support: skip job execution if it has run too many times in a window."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class RateLimitConfig:
    max_runs: int          # maximum number of runs allowed in the window
    window_seconds: int    # rolling window size in seconds
    state_dir: Path
    job_name: str

    def is_enabled(self) -> bool:
        return self.max_runs > 0 and self.window_seconds > 0


@dataclass
class RateLimitState:
    run_timestamps: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"run_timestamps": self.run_timestamps}

    @classmethod
    def from_dict(cls, data: dict) -> "RateLimitState":
        return cls(run_timestamps=list(data.get("run_timestamps", [])))


def _state_path(cfg: RateLimitConfig) -> Path:
    safe_name = cfg.job_name.replace("/", "_").replace(" ", "_")
    return cfg.state_dir / f"{safe_name}.ratelimit.json"


def load_state(cfg: RateLimitConfig) -> RateLimitState:
    path = _state_path(cfg)
    if not path.exists():
        return RateLimitState()
    try:
        return RateLimitState.from_dict(json.loads(path.read_text()))
    except (json.JSONDecodeError, OSError):
        return RateLimitState()


def save_state(cfg: RateLimitConfig, state: RateLimitState) -> None:
    path = _state_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict()))


def check_rate_limit(cfg: RateLimitConfig, now: Optional[float] = None) -> bool:
    """Return True if the job is allowed to run, False if it is rate-limited."""
    if not cfg.is_enabled():
        return True

    now = now if now is not None else time.time()
    state = load_state(cfg)

    cutoff = now - cfg.window_seconds
    recent = [ts for ts in state.run_timestamps if ts >= cutoff]

    if len(recent) >= cfg.max_runs:
        return False

    recent.append(now)
    save_state(cfg, RateLimitState(run_timestamps=recent))
    return True
