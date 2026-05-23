"""Generate human-readable summary reports from collected metrics."""
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import List

from cronwrap.metrics import JobMetrics, load_metrics


def list_tracked_jobs(metrics_dir: str) -> List[str]:
    """Return job names that have stored metrics in *metrics_dir*."""
    base = Path(metrics_dir)
    if not base.exists():
        return []
    names = []
    for p in sorted(base.glob("*.metrics.json")):
        with open(p) as fh:
            data = json.load(fh)
        names.append(data.get("job_name", p.stem))
    return names


def format_metrics(m: JobMetrics) -> str:
    """Return a multi-line text summary for a single job."""
    lines = [
        f"Job: {m.job_name}",
        f"  Total runs      : {m.total_runs}",
        f"  Successful      : {m.successful_runs}",
        f"  Failed          : {m.failed_runs}",
        f"  Total retries   : {m.total_retries}",
        f"  Success rate    : {m.success_rate:.1%}",
    ]
    if m.average_duration is not None:
        lines.append(f"  Avg duration    : {m.average_duration:.2f}s")
    if m.last_exit_code is not None:
        lines.append(f"  Last exit code  : {m.last_exit_code}")
    if m.last_duration_seconds is not None:
        lines.append(f"  Last duration   : {m.last_duration_seconds:.2f}s")
    return "\n".join(lines)


def build_report(metrics_dir: str) -> str:
    """Build a full report for all tracked jobs in *metrics_dir*."""
    jobs = list_tracked_jobs(metrics_dir)
    if not jobs:
        return "No metrics recorded yet."
    sections = []
    for job_name in jobs:
        m = load_metrics(metrics_dir, job_name)
        sections.append(format_metrics(m))
    separator = "\n" + "-" * 40 + "\n"
    return separator.join(sections)
