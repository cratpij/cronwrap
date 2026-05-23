"""Job label support — attach arbitrary key=value metadata to a run."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_LABEL_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_.-]*$')
_MAX_VALUE_LEN = 256


@dataclass
class LabelConfig:
    labels: Dict[str, str] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return len(self.labels) == 0

    def as_dict(self) -> Dict[str, str]:
        return dict(self.labels)


def validate_label_key(key: str) -> bool:
    """Return True if *key* is a valid label key."""
    return bool(_LABEL_RE.match(key))


def validate_label_value(value: str) -> bool:
    """Return True if *value* is within the allowed length."""
    return len(value) <= _MAX_VALUE_LEN


def parse_labels(raw: str) -> LabelConfig:
    """Parse a comma-separated list of ``key=value`` pairs.

    Silently drops malformed or invalid entries.

    >>> parse_labels("env=prod,team=sre").labels
    {'env': 'prod', 'team': 'sre'}
    """
    labels: Dict[str, str] = {}
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if "=" not in token:
            continue
        key, _, value = token.partition("=")
        key = key.strip()
        value = value.strip()
        if not validate_label_key(key):
            continue
        if not validate_label_value(value):
            continue
        labels[key] = value
    return LabelConfig(labels=labels)


def merge_labels(*configs: LabelConfig) -> LabelConfig:
    """Merge multiple :class:`LabelConfig` objects; later configs win."""
    merged: Dict[str, str] = {}
    for cfg in configs:
        merged.update(cfg.labels)
    return LabelConfig(labels=merged)


def labels_from_env(env: Optional[Dict[str, str]] = None) -> Optional[LabelConfig]:
    """Build a :class:`LabelConfig` from the ``CRONWRAP_LABELS`` env var."""
    import os
    source = env if env is not None else os.environ
    raw = source.get("CRONWRAP_LABELS", "").strip()
    if not raw:
        return None
    return parse_labels(raw)
