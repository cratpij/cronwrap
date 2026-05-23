"""Build :class:`OutputConfig` from environment variables."""

from __future__ import annotations

import os

from cronwrap.output import OutputConfig, DEFAULT_MAX_BYTES

_ENV_MAX_BYTES = "CRONWRAP_OUTPUT_MAX_BYTES"
_ENV_INCLUDE_STDOUT = "CRONWRAP_OUTPUT_STDOUT"
_ENV_INCLUDE_STDERR = "CRONWRAP_OUTPUT_STDERR"


def from_env() -> OutputConfig:
    """Return an :class:`OutputConfig` populated from environment variables.

    Environment variables
    ---------------------
    CRONWRAP_OUTPUT_MAX_BYTES
        Maximum bytes to keep per stream.  Defaults to 65536 (64 KB).
        Values <= 0 are clamped to 0 (discard all output).
    CRONWRAP_OUTPUT_STDOUT
        Set to ``"0"`` or ``"false"`` to suppress stdout capture.
    CRONWRAP_OUTPUT_STDERR
        Set to ``"0"`` or ``"false"`` to suppress stderr capture.
    """
    max_bytes = _parse_int(_ENV_MAX_BYTES, DEFAULT_MAX_BYTES)
    if max_bytes < 0:
        max_bytes = 0

    include_stdout = _parse_bool(_ENV_INCLUDE_STDOUT, default=True)
    include_stderr = _parse_bool(_ENV_INCLUDE_STDERR, default=True)

    return OutputConfig(
        max_bytes=max_bytes,
        include_stdout=include_stdout,
        include_stderr=include_stderr,
    )


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _parse_int(var: str, default: int) -> int:
    raw = os.environ.get(var, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _parse_bool(var: str, default: bool) -> bool:
    raw = os.environ.get(var, "").strip().lower()
    if not raw:
        return default
    return raw not in ("0", "false", "no", "off")
