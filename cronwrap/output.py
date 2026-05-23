"""Utilities for capturing, truncating, and formatting job output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

DEFAULT_MAX_BYTES = 64 * 1024  # 64 KB


@dataclass
class OutputConfig:
    """Configuration for output capture behaviour."""

    max_bytes: int = DEFAULT_MAX_BYTES
    include_stdout: bool = True
    include_stderr: bool = True


@dataclass
class CapturedOutput:
    """Holds the raw stdout/stderr strings from a completed job."""

    stdout: str = ""
    stderr: str = ""

    def is_empty(self) -> bool:
        return not self.stdout.strip() and not self.stderr.strip()


def truncate(text: str, max_bytes: int) -> str:
    """Return *text* truncated to at most *max_bytes* bytes (UTF-8).

    If truncation occurs a notice is appended so the reader knows output
    was cut short.
    """
    if max_bytes <= 0:
        return ""
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated + "\n... [output truncated]"


def capture_output(
    stdout_raw: Optional[str],
    stderr_raw: Optional[str],
    config: OutputConfig,
) -> CapturedOutput:
    """Apply include/truncate rules and return a :class:`CapturedOutput`."""
    stdout = ""
    stderr = ""

    if config.include_stdout and stdout_raw:
        stdout = truncate(stdout_raw, config.max_bytes)

    if config.include_stderr and stderr_raw:
        stderr = truncate(stderr_raw, config.max_bytes)

    return CapturedOutput(stdout=stdout, stderr=stderr)


def format_output(captured: CapturedOutput) -> str:
    """Return a human-readable string combining stdout and stderr sections."""
    parts: list[str] = []
    if captured.stdout.strip():
        parts.append("--- stdout ---\n" + captured.stdout.rstrip())
    if captured.stderr.strip():
        parts.append("--- stderr ---\n" + captured.stderr.rstrip())
    return "\n".join(parts) if parts else "(no output)"
