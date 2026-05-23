"""Persistent run-history log for cron jobs (JSON Lines format)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


_DEFAULT_HISTORY_FILE = Path.home() / ".cronwrap" / "history.jsonl"


@dataclass
class RunRecord:
    """A single job execution record."""

    job_name: str
    command: str
    started_at: str  # ISO-8601
    finished_at: str  # ISO-8601
    exit_code: int
    attempts: int
    stdout: str = ""
    stderr: str = ""

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_dict(cls, data: dict) -> "RunRecord":
        return cls(**{k: data[k] for k in cls.__dataclass_fields__})


def append_record(
    record: RunRecord,
    history_file: Optional[Path] = None,
) -> None:
    """Append *record* to the history file (one JSON object per line)."""
    path = history_file or _DEFAULT_HISTORY_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(record.to_json() + "\n")


def load_records(
    history_file: Optional[Path] = None,
    job_name: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[RunRecord]:
    """Load run records from *history_file*.

    Optionally filter by *job_name* and cap results at *limit*.
    Returns an empty list if the file does not exist.
    """
    path = history_file or _DEFAULT_HISTORY_FILE
    if not path.exists():
        return []

    records: List[RunRecord] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                record = RunRecord.from_dict(data)
            except (json.JSONDecodeError, TypeError, KeyError):
                continue
            if job_name is None or record.job_name == job_name:
                records.append(record)

    if limit is not None:
        records = records[-limit:]
    return records


def last_record(
    job_name: str,
    history_file: Optional[Path] = None,
) -> Optional[RunRecord]:
    """Return the most recent record for *job_name*, or None."""
    records = load_records(history_file=history_file, job_name=job_name)
    return records[-1] if records else None


def make_record(
    job_name: str,
    command: str,
    started_at: datetime,
    finished_at: datetime,
    exit_code: int,
    attempts: int,
    stdout: str = "",
    stderr: str = "",
) -> RunRecord:
    """Convenience constructor that converts datetimes to ISO-8601 strings."""
    return RunRecord(
        job_name=job_name,
        command=command,
        started_at=started_at.isoformat(),
        finished_at=finished_at.isoformat(),
        exit_code=exit_code,
        attempts=attempts,
        stdout=stdout,
        stderr=stderr,
    )
