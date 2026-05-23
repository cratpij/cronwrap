"""Environment-based configuration loader for job tags."""

from __future__ import annotations

import os

from cronwrap.tag import TagConfig, build_tag_config

_ENV_VAR = "CRONWRAP_TAGS"


def from_env(environ: dict[str, str] | None = None) -> TagConfig:
    """Build a :class:`~cronwrap.tag.TagConfig` from environment variables.

    Reads ``CRONWRAP_TAGS`` — a comma-separated list of tags to attach to
    every job run executed in this environment.

    Args:
        environ: Mapping to read from.  Defaults to :data:`os.environ`.

    Returns:
        A :class:`~cronwrap.tag.TagConfig` instance.

    Example::

        CRONWRAP_TAGS=deploy,prod python -m cronwrap ...
    """
    if environ is None:
        environ = dict(os.environ)

    raw = environ.get(_ENV_VAR, "")
    return build_tag_config(raw)
