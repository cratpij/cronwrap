"""Heartbeat / ping-URL support for cron jobs.

After a successful job run the wrapper can send an HTTP GET request to a
configured URL (e.g. a dead-man's-switch service such as Healthchecks.io or
Cronitor).  A ping is only sent when the job exits with code 0.
"""

from __future__ import annotations

import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HeartbeatConfig:
    """Configuration for the heartbeat ping."""

    url: Optional[str] = None
    # seconds to wait for the remote server
    timeout: int = 10
    # append ?status=fail when the job failed (supported by some services)
    ping_on_failure: bool = False
    failure_suffix: str = "/fail"


def is_enabled(cfg: HeartbeatConfig) -> bool:
    """Return True when a ping URL has been configured."""
    return bool(cfg.url and cfg.url.strip())


def build_url(cfg: HeartbeatConfig, *, success: bool) -> str:
    """Return the URL to ping for the given outcome.

    If *ping_on_failure* is enabled and the job failed the *failure_suffix* is
    appended to the base URL so that services like Healthchecks.io can record
    the failure without marking the check as "down".
    """
    base = (cfg.url or "").rstrip("/")
    if not success and cfg.ping_on_failure:
        return base + cfg.failure_suffix
    return base


def send_heartbeat(cfg: HeartbeatConfig, *, success: bool) -> bool:
    """Send the heartbeat ping and return True on HTTP 2xx, False otherwise.

    Failures are swallowed so that a dead ping endpoint never prevents the
    cron wrapper from finishing normally.
    """
    if not is_enabled(cfg):
        return False
    if not success and not cfg.ping_on_failure:
        return False

    url = build_url(cfg, success=success)
    try:
        with urllib.request.urlopen(url, timeout=cfg.timeout) as resp:  # noqa: S310
            return 200 <= resp.status < 300
    except (urllib.error.URLError, OSError):
        return False
