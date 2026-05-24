"""Audit log: append structured run events to a newline-delimited JSON file."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditEntry:
    job_name: str
    started_at: str
    exit_code: int
    duration_seconds: float
    tags: List[str] = field(default_factory=list)
    labels: dict = field(default_factory=dict)
    retries: int = 0
    timed_out: bool = False
    throttled: bool = False
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "started_at": self.started_at,
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "tags": self.tags,
            "labels": self.labels,
            "retries": self.retries,
            "timed_out": self.timed_out,
            "throttled": self.throttled,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            job_name=data["job_name"],
            started_at=data["started_at"],
            exit_code=data["exit_code"],
            duration_seconds=data["duration_seconds"],
            tags=data.get("tags", []),
            labels=data.get("labels", {}),
            retries=data.get("retries", 0),
            timed_out=data.get("timed_out", False),
            throttled=data.get("throttled", False),
            note=data.get("note"),
        )


def _audit_path(audit_dir: str, job_name: str) -> Path:
    safe = job_name.replace(os.sep, "_").replace(" ", "_")
    return Path(audit_dir) / f"{safe}.audit.jsonl"


def append_entry(audit_dir: str, entry: AuditEntry) -> Path:
    """Append *entry* to the job's audit log, creating the file if needed."""
    path = _audit_path(audit_dir, entry.job_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.to_dict()) + "\n")
    return path


def read_entries(audit_dir: str, job_name: str) -> List[AuditEntry]:
    """Return all audit entries for *job_name*, oldest first."""
    path = _audit_path(audit_dir, job_name)
    if not path.exists():
        return []
    entries: List[AuditEntry] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(AuditEntry.from_dict(json.loads(line)))
    return entries


def make_entry(
    job_name: str,
    exit_code: int,
    duration_seconds: float,
    *,
    started_at: Optional[str] = None,
    **kwargs,
) -> AuditEntry:
    """Convenience constructor; *started_at* defaults to now (UTC ISO-8601)."""
    if started_at is None:
        started_at = datetime.now(timezone.utc).isoformat()
    return AuditEntry(
        job_name=job_name,
        started_at=started_at,
        exit_code=exit_code,
        duration_seconds=duration_seconds,
        **kwargs,
    )
