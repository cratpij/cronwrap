"""Circuit breaker: pause job execution after repeated failures."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CircuitBreakerConfig:
    """Configuration for the circuit breaker."""
    failure_threshold: int = 5   # open after this many consecutive failures
    recovery_timeout: int = 300  # seconds before moving to half-open
    state_dir: str = "/tmp/cronwrap/circuit"

    def is_enabled(self) -> bool:
        return self.failure_threshold > 0 and self.recovery_timeout > 0


@dataclass
class CircuitState:
    """Persisted state for a single job's circuit breaker."""
    consecutive_failures: int = 0
    opened_at: Optional[float] = None  # epoch seconds when circuit opened
    state: str = "closed"  # closed | open | half-open

    def to_dict(self) -> dict:
        return {
            "consecutive_failures": self.consecutive_failures,
            "opened_at": self.opened_at,
            "state": self.state,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CircuitState":
        return cls(
            consecutive_failures=d.get("consecutive_failures", 0),
            opened_at=d.get("opened_at"),
            state=d.get("state", "closed"),
        )


class CircuitOpenError(Exception):
    """Raised when a job is blocked by an open circuit breaker."""


def _state_path(job_name: str, state_dir: str) -> Path:
    safe = job_name.replace(os.sep, "_").replace(" ", "_")
    return Path(state_dir) / f"{safe}.json"


def load_state(job_name: str, cfg: CircuitBreakerConfig) -> CircuitState:
    path = _state_path(job_name, cfg.state_dir)
    if not path.exists():
        return CircuitState()
    try:
        return CircuitState.from_dict(json.loads(path.read_text()))
    except Exception:
        return CircuitState()


def save_state(job_name: str, cfg: CircuitBreakerConfig, state: CircuitState) -> None:
    path = _state_path(job_name, cfg.state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict()))


def record_success(job_name: str, cfg: CircuitBreakerConfig) -> CircuitState:
    """Reset circuit on success."""
    state = CircuitState(consecutive_failures=0, opened_at=None, state="closed")
    save_state(job_name, cfg, state)
    return state


def record_failure(job_name: str, cfg: CircuitBreakerConfig) -> CircuitState:
    """Increment failure count; open circuit if threshold reached."""
    state = load_state(job_name, cfg)
    state.consecutive_failures += 1
    if state.consecutive_failures >= cfg.failure_threshold and state.state == "closed":
        state.state = "open"
        state.opened_at = time.time()
    save_state(job_name, cfg, state)
    return state


def check_circuit(job_name: str, cfg: CircuitBreakerConfig) -> CircuitState:
    """Return current state, transitioning open->half-open if timeout elapsed.

    Raises CircuitOpenError if the circuit is open and recovery timeout has
    not yet elapsed.
    """
    if not cfg.is_enabled():
        return CircuitState()
    state = load_state(job_name, cfg)
    if state.state == "open":
        elapsed = time.time() - (state.opened_at or 0)
        if elapsed >= cfg.recovery_timeout:
            state.state = "half-open"
            save_state(job_name, cfg, state)
        else:
            raise CircuitOpenError(
                f"Circuit open for '{job_name}': "
                f"{int(cfg.recovery_timeout - elapsed)}s remaining"
            )
    return state
