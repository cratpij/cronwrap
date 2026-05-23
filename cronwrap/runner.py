"""Core job runner with retry logic for cronwrap."""

import subprocess
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, List

logger = logging.getLogger(__name__)


@dataclass
class JobResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    attempts: int
    elapsed: float

    @property
    def success(self) -> bool:
        return self.returncode == 0


@dataclass
class RunnerConfig:
    command: str
    retries: int = 0
    retry_delay: float = 5.0
    timeout: Optional[float] = None
    env: Optional[dict] = None


def run_job(config: RunnerConfig) -> JobResult:
    """Execute a shell command with optional retry logic.

    Args:
        config: RunnerConfig describing the job and retry behaviour.

    Returns:
        JobResult with the outcome of the final attempt.
    """
    max_attempts = config.retries + 1
    last_result: Optional[JobResult] = None
    start_time = time.monotonic()

    for attempt in range(1, max_attempts + 1):
        logger.info("Running command (attempt %d/%d): %s", attempt, max_attempts, config.command)

        try:
            proc = subprocess.run(
                config.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=config.timeout,
                env=config.env,
            )
        except subprocess.TimeoutExpired as exc:
            logger.warning("Command timed out on attempt %d", attempt)
            last_result = JobResult(
                command=config.command,
                returncode=-1,
                stdout="",
                stderr=f"TimeoutExpired: {exc}",
                attempts=attempt,
                elapsed=time.monotonic() - start_time,
            )
        else:
            last_result = JobResult(
                command=config.command,
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                attempts=attempt,
                elapsed=time.monotonic() - start_time,
            )

        if last_result.success:
            logger.info("Command succeeded on attempt %d", attempt)
            return last_result

        if attempt < max_attempts:
            logger.warning(
                "Attempt %d failed (exit %d). Retrying in %.1fs…",
                attempt,
                last_result.returncode,
                config.retry_delay,
            )
            time.sleep(config.retry_delay)

    logger.error("Command failed after %d attempt(s)", max_attempts)
    return last_result  # type: ignore[return-value]
