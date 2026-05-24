"""Load AuditConfig from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

_DEFAULT_AUDIT_DIR = "/var/lib/cronwrap/audit"
_DEFAULT_ENABLED = True


@dataclass
class AuditConfig:
    enabled: bool
    audit_dir: str


def from_env() -> Optional["AuditConfig"]:
    """Return an AuditConfig built from environment variables.

    Returns ``None`` when auditing is explicitly disabled via
    ``CRONWRAP_AUDIT_ENABLED=false``.
    """
    raw_enabled = os.environ.get("CRONWRAP_AUDIT_ENABLED", "").strip().lower()
    if raw_enabled in ("0", "false", "no"):
        return None

    audit_dir = os.environ.get("CRONWRAP_AUDIT_DIR", "").strip() or _DEFAULT_AUDIT_DIR

    return AuditConfig(enabled=True, audit_dir=audit_dir)
