"""Webhook notification support for cronwrap job failures."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WebhookConfig:
    url: str
    job_name: str
    timeout_seconds: int = 10
    extra_headers: dict = field(default_factory=dict)


def build_payload(config: WebhookConfig, exit_code: int, stdout: str, stderr: str) -> dict:
    """Build the JSON payload sent to the webhook endpoint."""
    return {
        "job": config.job_name,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "status": "failure" if exit_code != 0 else "success",
    }


def send_webhook(
    config: WebhookConfig,
    exit_code: int,
    stdout: str,
    stderr: str,
) -> bool:
    """POST a JSON payload to the configured webhook URL.

    Returns True on HTTP 2xx, False otherwise.
    Raises urllib.error.URLError on network-level errors.
    """
    payload = build_payload(config, exit_code, stdout, stderr)
    data = json.dumps(payload).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    headers.update(config.extra_headers)

    req = urllib.request.Request(config.url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=config.timeout_seconds) as resp:
            return 200 <= resp.status < 300
    except urllib.error.HTTPError as exc:
        return False
