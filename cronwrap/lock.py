"""File-based locking to prevent overlapping cron job executions."""

from __future__ import annotations

import fcntl
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, Optional


@dataclass
class LockConfig:
    """Configuration for job locking."""

    lock_dir: str = "/tmp/cronwrap"
    timeout: float = 0.0  # seconds to wait; 0 = non-blocking
    poll_interval: float = 0.1


class LockError(Exception):
    """Raised when a lock cannot be acquired."""


def _lock_path(job_name: str, lock_dir: str) -> Path:
    safe_name = job_name.replace("/", "_").replace(" ", "_")
    return Path(lock_dir) / f"{safe_name}.lock"


@contextmanager
def acquire_lock(
    job_name: str,
    config: Optional[LockConfig] = None,
) -> Generator[Path, None, None]:
    """Context manager that holds an exclusive lock for *job_name*.

    Raises LockError immediately (or after *timeout* seconds) if the lock
    is already held by another process.
    """
    cfg = config or LockConfig()
    lock_file = _lock_path(job_name, cfg.lock_dir)
    lock_file.parent.mkdir(parents=True, exist_ok=True)

    fd = os.open(str(lock_file), os.O_CREAT | os.O_WRONLY)
    deadline = time.monotonic() + cfg.timeout
    acquired = False

    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise LockError(
                        f"Could not acquire lock for job {job_name!r} "
                        f"(timeout={cfg.timeout}s)"
                    )
                time.sleep(cfg.poll_interval)

        os.write(fd, str(os.getpid()).encode())
        yield lock_file
    finally:
        if acquired:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        try:
            lock_file.unlink(missing_ok=True)
        except OSError:  # pragma: no cover
            pass


def is_locked(job_name: str, config: Optional[LockConfig] = None) -> bool:
    """Return True if *job_name* is currently locked by another process."""
    cfg = config or LockConfig()
    lock_file = _lock_path(job_name, cfg.lock_dir)
    if not lock_file.exists():
        return False
    fd = os.open(str(lock_file), os.O_RDONLY | os.O_CREAT)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    except BlockingIOError:
        return True
    finally:
        os.close(fd)
