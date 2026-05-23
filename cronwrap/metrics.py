"""Lightweight metrics collection for cron job runs."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional


@dataclass
class JobMetrics:
    job_name: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    total_retries: int = 0
    last_exit_code: Optional[int] = None
    last_duration_seconds: Optional[float] = None
    durations: List[float] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs

    @property
    def average_duration(self) -> Optional[float]:
        if not self.durations:
            return None
        return sum(self.durations) / len(self.durations)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "JobMetrics":
        return cls(**data)


def _metrics_path(metrics_dir: str, job_name: str) -> Path:
    safe_name = job_name.replace(os.sep, "_").replace(" ", "_")
    return Path(metrics_dir) / f"{safe_name}.metrics.json"


def load_metrics(metrics_dir: str, job_name: str) -> JobMetrics:
    path = _metrics_path(metrics_dir, job_name)
    if not path.exists():
        return JobMetrics(job_name=job_name)
    with open(path, "r") as fh:
        return JobMetrics.from_dict(json.load(fh))


def save_metrics(metrics_dir: str, metrics: JobMetrics) -> None:
    path = _metrics_path(metrics_dir, metrics.job_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(metrics.to_dict(), fh, indent=2)


def record_run(
    metrics_dir: str,
    job_name: str,
    exit_code: int,
    duration_seconds: float,
    retries_used: int = 0,
) -> JobMetrics:
    m = load_metrics(metrics_dir, job_name)
    m.total_runs += 1
    m.last_exit_code = exit_code
    m.last_duration_seconds = duration_seconds
    m.total_retries += retries_used
    m.durations.append(duration_seconds)
    if exit_code == 0:
        m.successful_runs += 1
    else:
        m.failed_runs += 1
    save_metrics(metrics_dir, m)
    return m
