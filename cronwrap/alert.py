"""Alert throttling: suppress repeated failure notifications within a cooldown window."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class AlertState:
    job_name: str
    last_alerted_at: float  # unix timestamp
    alert_count: int = 0

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "last_alerted_at": self.last_alerted_at,
            "alert_count": self.alert_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AlertState":
        return cls(
            job_name=data["job_name"],
            last_alerted_at=float(data["last_alerted_at"]),
            alert_count=int(data.get("alert_count", 0)),
        )


@dataclass
class AlertConfig:
    state_dir: Path
    cooldown_seconds: int = 3600  # 1 hour default


def _state_path(cfg: AlertConfig, job_name: str) -> Path:
    safe = job_name.replace(os.sep, "_").replace(" ", "_")
    return cfg.state_dir / f"{safe}.alert.json"


def load_state(cfg: AlertConfig, job_name: str) -> Optional[AlertState]:
    path = _state_path(cfg, job_name)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return AlertState.from_dict(data)
    except (json.JSONDecodeError, KeyError):
        return None


def save_state(cfg: AlertConfig, state: AlertState) -> None:
    cfg.state_dir.mkdir(parents=True, exist_ok=True)
    path = _state_path(cfg, state.job_name)
    path.write_text(json.dumps(state.to_dict(), indent=2))


def should_alert(cfg: AlertConfig, job_name: str, now: Optional[float] = None) -> bool:
    """Return True if an alert should be sent (outside the cooldown window)."""
    if now is None:
        now = time.time()
    state = load_state(cfg, job_name)
    if state is None:
        return True
    return (now - state.last_alerted_at) >= cfg.cooldown_seconds


def record_alert(cfg: AlertConfig, job_name: str, now: Optional[float] = None) -> AlertState:
    """Persist that an alert was sent right now; return updated state."""
    if now is None:
        now = time.time()
    existing = load_state(cfg, job_name)
    count = (existing.alert_count + 1) if existing else 1
    state = AlertState(job_name=job_name, last_alerted_at=now, alert_count=count)
    save_state(cfg, state)
    return state
