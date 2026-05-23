"""Job tagging support — attach arbitrary string tags to job runs for filtering and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class TagConfig:
    """Configuration for job tags parsed from CLI or environment."""

    tags: List[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.tags) == 0

    def as_csv(self) -> str:
        """Return tags as a comma-separated string."""
        return ",".join(self.tags)


def parse_tags(raw: str) -> List[str]:
    """Parse a comma-separated tag string into a deduplicated, sorted list.

    Leading/trailing whitespace is stripped from each tag.  Empty tokens
    (e.g. from trailing commas) are silently dropped.

    Args:
        raw: Raw comma-separated tag string, e.g. ``"deploy,prod,v2"``.

    Returns:
        Sorted list of unique, non-empty tag strings.
    """
    seen: dict[str, None] = {}
    for token in raw.split(","):
        tag = token.strip()
        if tag:
            seen[tag] = None
    return sorted(seen.keys())


def validate_tag(tag: str) -> bool:
    """Return True if *tag* contains only alphanumerics, hyphens, and underscores."""
    return bool(tag) and all(c.isalnum() or c in ("-", "_") for c in tag)


def build_tag_config(raw: str | None) -> TagConfig:
    """Build a :class:`TagConfig` from an optional raw string.

    Invalid tags (containing disallowed characters) are silently ignored.

    Args:
        raw: Comma-separated tag string or ``None``.

    Returns:
        A :class:`TagConfig` instance (possibly with an empty tag list).
    """
    if not raw:
        return TagConfig()
    tags = [t for t in parse_tags(raw) if validate_tag(t)]
    return TagConfig(tags=tags)
