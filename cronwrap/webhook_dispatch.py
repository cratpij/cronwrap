"""High-level helper that fires a webhook when a job fails, respecting config."""

from __future__ import annotations

import logging
import urllib.error
from typing import Optional

from cronwrap.webhook import WebhookConfig, send_webhook

log = logging.getLogger(__name__)


def maybe_send_webhook(
    config: Optional[WebhookConfig],
    exit_code: int,
    stdout: str,
    stderr: str,
    *,
    only_on_failure: bool = True,
) -> bool:
    """Send a webhook notification if config is provided and conditions are met.

    Args:
        config: WebhookConfig or None (disabled).
        exit_code: The job's exit code.
        stdout: Captured standard output.
        stderr: Captured standard error.
        only_on_failure: When True (default), skip sending on exit_code == 0.

    Returns:
        True if a webhook was sent successfully, False otherwise.
    """
    if config is None:
        log.debug("webhook: no config, skipping")
        return False

    if only_on_failure and exit_code == 0:
        log.debug("webhook: job succeeded, skipping")
        return False

    try:
        ok = send_webhook(config, exit_code=exit_code, stdout=stdout, stderr=stderr)
        if ok:
            log.info("webhook: notification sent to %s", config.url)
        else:
            log.warning("webhook: server returned non-2xx for %s", config.url)
        return ok
    except urllib.error.URLError as exc:
        log.error("webhook: network error sending to %s: %s", config.url, exc)
        return False
    except Exception as exc:  # pragma: no cover
        log.error("webhook: unexpected error: %s", exc)
        return False
