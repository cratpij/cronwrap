"""Tests for cronwrap.audit and cronwrap.audit_config."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from cronwrap.audit import (
    AuditEntry,
    append_entry,
    make_entry,
    read_entries,
    _audit_path,
)
from cronwrap.audit_config import from_env


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def audit_dir(tmp_path: Path) -> str:
    return str(tmp_path / "audit")


def _entry(**kwargs) -> AuditEntry:
    defaults = dict(
        job_name="backup",
        started_at="2024-01-01T00:00:00+00:00",
        exit_code=0,
        duration_seconds=1.5,
    )
    defaults.update(kwargs)
    return AuditEntry(**defaults)


# ---------------------------------------------------------------------------
# AuditEntry serialisation
# ---------------------------------------------------------------------------


def test_entry_to_dict_roundtrip():
    e = _entry(tags=["prod"], labels={"env": "prod"}, retries=2, timed_out=False)
    assert AuditEntry.from_dict(e.to_dict()) == e


def test_entry_from_dict_defaults():
    minimal = {
        "job_name": "x",
        "started_at": "2024-01-01T00:00:00+00:00",
        "exit_code": 1,
        "duration_seconds": 0.1,
    }
    e = AuditEntry.from_dict(minimal)
    assert e.tags == []
    assert e.labels == {}
    assert e.retries == 0
    assert e.timed_out is False
    assert e.throttled is False
    assert e.note is None


# ---------------------------------------------------------------------------
# make_entry helper
# ---------------------------------------------------------------------------


def test_make_entry_fills_started_at():
    e = make_entry("myjob", exit_code=0, duration_seconds=2.0)
    assert e.started_at  # not empty
    assert "T" in e.started_at  # ISO-8601 shape


def test_make_entry_accepts_explicit_started_at():
    ts = "2024-06-15T12:00:00+00:00"
    e = make_entry("myjob", exit_code=0, duration_seconds=0.5, started_at=ts)
    assert e.started_at == ts


# ---------------------------------------------------------------------------
# append_entry / read_entries
# ---------------------------------------------------------------------------


def test_append_creates_file(audit_dir):
    e = _entry()
    path = append_entry(audit_dir, e)
    assert path.exists()


def test_append_creates_parent_dirs(tmp_path):
    deep_dir = str(tmp_path / "a" / "b" / "c")
    append_entry(deep_dir, _entry())
    assert Path(deep_dir).exists()


def test_read_entries_empty_when_no_file(audit_dir):
    assert read_entries(audit_dir, "nonexistent") == []


def test_read_entries_returns_appended(audit_dir):
    e1 = _entry(exit_code=0, duration_seconds=1.0)
    e2 = _entry(exit_code=1, duration_seconds=2.0, retries=1)
    append_entry(audit_dir, e1)
    append_entry(audit_dir, e2)
    entries = read_entries(audit_dir, "backup")
    assert len(entries) == 2
    assert entries[0].exit_code == 0
    assert entries[1].exit_code == 1
    assert entries[1].retries == 1


def test_audit_file_is_valid_jsonl(audit_dir):
    append_entry(audit_dir, _entry())
    path = _audit_path(audit_dir, "backup")
    lines = path.read_text().splitlines()
    for line in lines:
        json.loads(line)  # must not raise


def test_job_name_with_spaces_safe(audit_dir):
    e = _entry(job_name="my job")
    path = append_entry(audit_dir, e)
    assert " " not in path.name


# ---------------------------------------------------------------------------
# audit_config.from_env
# ---------------------------------------------------------------------------


def test_from_env_defaults(monkeypatch):
    monkeypatch.delenv("CRONWRAP_AUDIT_ENABLED", raising=False)
    monkeypatch.delenv("CRONWRAP_AUDIT_DIR", raising=False)
    cfg = from_env()
    assert cfg is not None
    assert cfg.enabled is True
    assert cfg.audit_dir == "/var/lib/cronwrap/audit"


def test_from_env_custom_dir(monkeypatch):
    monkeypatch.setenv("CRONWRAP_AUDIT_DIR", "/tmp/myaudit")
    monkeypatch.delenv("CRONWRAP_AUDIT_ENABLED", raising=False)
    cfg = from_env()
    assert cfg is not None
    assert cfg.audit_dir == "/tmp/myaudit"


def test_from_env_disabled(monkeypatch):
    monkeypatch.setenv("CRONWRAP_AUDIT_ENABLED", "false")
    assert from_env() is None


def test_from_env_disabled_zero(monkeypatch):
    monkeypatch.setenv("CRONWRAP_AUDIT_ENABLED", "0")
    assert from_env() is None
