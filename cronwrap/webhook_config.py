"""Environment-based configuration loader for webhook notifications."""

from __future__ import annotations

import os
from typing import Optional

from cronwrap.webhook import WebhookConfig

_DEFAULT_TIMEOUT = 10
_MIN_TIMEOUT = 1


def from_env(job_name: str) -> Optional[WebhookConfig]:
    """Build a WebhookConfig from environment variables, or return None.

    Environment variables:
        CRONWRAP_WEBHOOK_URL      — required; if absent, webhooks are disabled.
        CRONWRAP_WEBHOOK_TIMEOUT  — optional integer seconds (default 10).
        CRONWRAP_WEBHOOK_TOKEN    — optional Bearer token added as Authorization header.
    """
    url = os.environ.get("CRONWRAP_WEBHOOK_URL", "").strip()
    if not url:
        return None

    timeout = _DEFAULT_TIMEOUT
    raw_timeout = os.environ.get("CRONWRAP_WEBHOOK_TIMEOUT", "").strip()
    if raw_timeout:
        try:
            parsed = int(raw_timeout)
            timeout = max(_MIN_TIMEOUT, parsed)
        except ValueError:
            pass

    extra_headers: dict = {}
    token = os.environ.get("CRONWRAP_WEBHOOK_TOKEN", "").strip()
    if token:
        extra_headers["Authorization"] = f"Bearer {token}"

    return WebhookConfig(
        url=url,
        job_name=job_name,
        timeout_seconds=timeout,
        extra_headers=extra_headers,
    )
