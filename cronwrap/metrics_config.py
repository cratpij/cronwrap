"""Configuration helpers for the metrics subsystem."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_DEFAULT_METRICS_DIR = os.path.join(
    os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")),
    "cronwrap",
    "metrics",
)


@dataclass
class MetricsConfig:
    """Settings that control metrics collection behaviour."""

    enabled: bool = True
    metrics_dir: str = field(default_factory=lambda: _DEFAULT_METRICS_DIR)
    max_durations: int = 100  # cap stored duration samples per job

    def resolved_dir(self) -> Path:
        """Return the metrics directory as an absolute Path."""
        return Path(self.metrics_dir).expanduser().resolve()

    @classmethod
    def from_env(cls) -> "MetricsConfig":
        """Build a MetricsConfig from environment variables.

        CRONWRAP_METRICS_ENABLED  – '0' or 'false' to disable (default: enabled)
        CRONWRAP_METRICS_DIR      – override storage directory
        CRONWRAP_METRICS_MAX_DUR  – max duration samples to keep
        """
        enabled_raw = os.environ.get("CRONWRAP_METRICS_ENABLED", "1")
        enabled = enabled_raw.strip().lower() not in ("0", "false", "no")
        metrics_dir = os.environ.get("CRONWRAP_METRICS_DIR", _DEFAULT_METRICS_DIR)
        max_dur_raw = os.environ.get("CRONWRAP_METRICS_MAX_DUR", str(100))
        try:
            max_durations = int(max_dur_raw)
        except ValueError:
            max_durations = 100
        return cls(enabled=enabled, metrics_dir=metrics_dir, max_durations=max_durations)

    def trim_durations(self, durations: list) -> list:
        """Return *durations* trimmed to at most *max_durations* most-recent entries."""
        if len(durations) > self.max_durations:
            return durations[-self.max_durations :]
        return durations
