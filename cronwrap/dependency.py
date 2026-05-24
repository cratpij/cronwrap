"""Job dependency checking — skip execution if upstream jobs have not succeeded recently."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class DependencyConfig:
    """Configuration for job dependency checks."""

    job_names: List[str] = field(default_factory=list)
    """Names of upstream jobs that must have succeeded."""

    max_age_seconds: int = 86400
    """How recent the upstream success must be (default: 24 h)."""

    history_dir: str = "/var/lib/cronwrap/history"
    """Directory where history JSON files are stored."""

    def is_enabled(self) -> bool:
        return bool(self.job_names)


@dataclass
class DependencyResult:
    """Outcome of a dependency check."""

    satisfied: bool
    unsatisfied: List[str] = field(default_factory=list)
    """Names of jobs whose dependency was not met."""


def _last_success_age(job_name: str, history_dir: str) -> Optional[float]:
    """Return seconds since the most recent successful run, or None if not found."""
    history_file = Path(history_dir) / f"{job_name}.json"
    if not history_file.exists():
        return None

    try:
        records = json.loads(history_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    now = datetime.now(tz=timezone.utc).timestamp()
    for record in reversed(records):
        if record.get("exit_code", 1) == 0:
            started_at = record.get("started_at")
            if started_at:
                try:
                    ts = datetime.fromisoformat(started_at).timestamp()
                    return now - ts
                except ValueError:
                    continue
    return None


def check_dependencies(config: DependencyConfig) -> DependencyResult:
    """Check whether all upstream jobs satisfy the dependency requirements."""
    if not config.is_enabled():
        return DependencyResult(satisfied=True)

    unsatisfied: List[str] = []
    for job_name in config.job_names:
        age = _last_success_age(job_name, config.history_dir)
        if age is None or age > config.max_age_seconds:
            unsatisfied.append(job_name)

    return DependencyResult(satisfied=not unsatisfied, unsatisfied=unsatisfied)
