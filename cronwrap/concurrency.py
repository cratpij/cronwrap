"""Concurrency guard: prevent a job from running more than N instances at once."""
from __future__ import annotations

import os
import glob
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ConcurrencyConfig:
    """Configuration for the concurrency limit feature."""

    max_instances: int = 1
    lock_dir: Path = Path("/tmp/cronwrap/concurrency")
    job_name: str = ""

    def is_enabled(self) -> bool:
        return self.max_instances > 0 and bool(self.job_name)


class ConcurrencyLimitExceeded(Exception):
    """Raised when the concurrency limit for a job is already reached."""

    def __init__(self, job_name: str, current: int, limit: int) -> None:
        self.job_name = job_name
        self.current = current
        self.limit = limit
        super().__init__(
            f"Job '{job_name}' already has {current} running instance(s) "
            f"(limit={limit})"
        )


def _slot_pattern(cfg: ConcurrencyConfig) -> str:
    safe = cfg.job_name.replace("/", "_").replace(" ", "_")
    return str(cfg.lock_dir / f"{safe}.*.lock")


def _slot_path(cfg: ConcurrencyConfig, pid: int) -> Path:
    safe = cfg.job_name.replace("/", "_").replace(" ", "_")
    return cfg.lock_dir / f"{safe}.{pid}.lock"


def _live_slots(cfg: ConcurrencyConfig) -> list[Path]:
    """Return lock files whose recorded PID is still alive."""
    live: list[Path] = []
    for p in glob.glob(_slot_pattern(cfg)):
        path = Path(p)
        try:
            pid = int(path.read_text().strip())
            os.kill(pid, 0)  # signal 0 checks existence
            live.append(path)
        except (ValueError, OSError):
            # stale lock — remove it
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
    return live


def acquire_slot(cfg: ConcurrencyConfig) -> Path:
    """Acquire a concurrency slot or raise ConcurrencyLimitExceeded.

    Returns the path of the created lock file so the caller can release it.
    """
    if not cfg.is_enabled():
        return Path(os.devnull)

    cfg.lock_dir.mkdir(parents=True, exist_ok=True)
    live = _live_slots(cfg)
    if len(live) >= cfg.max_instances:
        raise ConcurrencyLimitExceeded(cfg.job_name, len(live), cfg.max_instances)

    slot = _slot_path(cfg, os.getpid())
    slot.write_text(str(os.getpid()))
    return slot


def release_slot(slot: Path) -> None:
    """Release a previously acquired concurrency slot."""
    try:
        slot.unlink(missing_ok=True)
    except OSError:
        pass


def running_count(cfg: ConcurrencyConfig) -> int:
    """Return the number of currently live instances for the job."""
    if not cfg.is_enabled():
        return 0
    return len(_live_slots(cfg))
