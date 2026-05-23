"""Timeout enforcement for cron job subprocesses."""

from __future__ import annotations

import signal
import subprocess
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TimeoutConfig:
    """Configuration for job timeout behaviour."""

    seconds: Optional[int] = None  # None means no timeout
    kill_after: int = 5  # seconds to wait after SIGTERM before sending SIGKILL

    def is_enabled(self) -> bool:
        return self.seconds is not None and self.seconds > 0


class TimeoutExpired(Exception):
    """Raised when a job exceeds its allowed runtime."""

    def __init__(self, job_name: str, seconds: int) -> None:
        self.job_name = job_name
        self.seconds = seconds
        super().__init__(
            f"Job '{job_name}' timed out after {seconds} second(s)."
        )


def wait_with_timeout(
    proc: subprocess.Popen,
    cfg: TimeoutConfig,
    job_name: str = "<unknown>",
) -> tuple[int, str, str]:
    """Wait for *proc* to finish, enforcing *cfg* timeout.

    Returns (returncode, stdout, stderr).
    Raises :class:`TimeoutExpired` if the process exceeds the allowed time.
    """
    timeout = cfg.seconds if cfg.is_enabled() else None

    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # Graceful shutdown first, then hard kill.
        proc.terminate()
        try:
            stdout, stderr = proc.communicate(timeout=cfg.kill_after)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
        raise TimeoutExpired(job_name, cfg.seconds)  # type: ignore[arg-type]

    return proc.returncode, stdout or "", stderr or ""
