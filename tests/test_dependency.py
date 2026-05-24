"""Tests for cronwrap.dependency and cronwrap.dependency_config."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwrap.dependency import (
    DependencyConfig,
    DependencyResult,
    _last_success_age,
    check_dependencies,
)
from cronwrap.dependency_config import from_env


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_history(directory: Path, job_name: str, records: list) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{job_name}.json").write_text(json.dumps(records))


def _record(exit_code: int, age_seconds: float) -> dict:
    ts = datetime.now(tz=timezone.utc) - timedelta(seconds=age_seconds)
    return {"exit_code": exit_code, "started_at": ts.isoformat()}


# ---------------------------------------------------------------------------
# DependencyConfig
# ---------------------------------------------------------------------------

def test_is_enabled_with_jobs():
    cfg = DependencyConfig(job_names=["upstream"])
    assert cfg.is_enabled() is True


def test_is_disabled_without_jobs():
    cfg = DependencyConfig(job_names=[])
    assert cfg.is_enabled() is False


# ---------------------------------------------------------------------------
# _last_success_age
# ---------------------------------------------------------------------------

def test_last_success_age_returns_none_when_no_file(tmp_path):
    assert _last_success_age("missing", str(tmp_path)) is None


def test_last_success_age_returns_none_when_no_successes(tmp_path):
    _write_history(tmp_path, "job", [_record(1, 100)])
    assert _last_success_age("job", str(tmp_path)) is None


def test_last_success_age_returns_approximate_age(tmp_path):
    _write_history(tmp_path, "job", [_record(0, 300)])
    age = _last_success_age("job", str(tmp_path))
    assert age is not None
    assert 290 <= age <= 310


def test_last_success_age_uses_most_recent_success(tmp_path):
    records = [_record(0, 3600), _record(0, 60)]
    _write_history(tmp_path, "job", records)
    age = _last_success_age("job", str(tmp_path))
    assert age is not None
    assert age < 120  # most recent success was ~60 s ago


# ---------------------------------------------------------------------------
# check_dependencies
# ---------------------------------------------------------------------------

def test_check_dependencies_satisfied_when_disabled():
    cfg = DependencyConfig(job_names=[])
    result = check_dependencies(cfg)
    assert result.satisfied is True
    assert result.unsatisfied == []


def test_check_dependencies_satisfied_recent_success(tmp_path):
    _write_history(tmp_path, "upstream", [_record(0, 100)])
    cfg = DependencyConfig(job_names=["upstream"], max_age_seconds=3600, history_dir=str(tmp_path))
    result = check_dependencies(cfg)
    assert result.satisfied is True


def test_check_dependencies_unsatisfied_stale_success(tmp_path):
    _write_history(tmp_path, "upstream", [_record(0, 7200)])
    cfg = DependencyConfig(job_names=["upstream"], max_age_seconds=3600, history_dir=str(tmp_path))
    result = check_dependencies(cfg)
    assert result.satisfied is False
    assert "upstream" in result.unsatisfied


def test_check_dependencies_unsatisfied_missing_job(tmp_path):
    cfg = DependencyConfig(job_names=["ghost"], max_age_seconds=3600, history_dir=str(tmp_path))
    result = check_dependencies(cfg)
    assert result.satisfied is False
    assert "ghost" in result.unsatisfied


# ---------------------------------------------------------------------------
# from_env
# ---------------------------------------------------------------------------

def test_from_env_returns_none_when_no_env(monkeypatch):
    monkeypatch.delenv("CRONWRAP_DEPENDS_ON", raising=False)
    assert from_env() is None


def test_from_env_parses_job_names(monkeypatch):
    monkeypatch.setenv("CRONWRAP_DEPENDS_ON", "job_a, job_b")
    cfg = from_env()
    assert cfg is not None
    assert cfg.job_names == ["job_a", "job_b"]


def test_from_env_custom_max_age(monkeypatch):
    monkeypatch.setenv("CRONWRAP_DEPENDS_ON", "job_a")
    monkeypatch.setenv("CRONWRAP_DEPENDS_MAX_AGE", "7200")
    cfg = from_env()
    assert cfg is not None
    assert cfg.max_age_seconds == 7200


def test_from_env_invalid_max_age_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("CRONWRAP_DEPENDS_ON", "job_a")
    monkeypatch.setenv("CRONWRAP_DEPENDS_MAX_AGE", "not-a-number")
    cfg = from_env()
    assert cfg is not None
    assert cfg.max_age_seconds == 86400


def test_from_env_custom_history_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRONWRAP_DEPENDS_ON", "job_a")
    monkeypatch.setenv("CRONWRAP_HISTORY_DIR", str(tmp_path))
    cfg = from_env()
    assert cfg is not None
    assert cfg.history_dir == str(tmp_path)
