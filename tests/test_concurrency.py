"""Tests for cronwrap.concurrency."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwrap.concurrency import (
    ConcurrencyConfig,
    ConcurrencyLimitExceeded,
    acquire_slot,
    release_slot,
    running_count,
    _live_slots,
)


@pytest.fixture()
def cfg(tmp_path: Path) -> ConcurrencyConfig:
    return ConcurrencyConfig(max_instances=2, lock_dir=tmp_path, job_name="backup")


def test_is_enabled_with_job_name(cfg: ConcurrencyConfig) -> None:
    assert cfg.is_enabled() is True


def test_is_disabled_without_job_name(tmp_path: Path) -> None:
    c = ConcurrencyConfig(max_instances=1, lock_dir=tmp_path, job_name="")
    assert c.is_enabled() is False


def test_is_disabled_when_max_zero(tmp_path: Path) -> None:
    c = ConcurrencyConfig(max_instances=0, lock_dir=tmp_path, job_name="backup")
    assert c.is_enabled() is False


def test_acquire_creates_lock_file(cfg: ConcurrencyConfig) -> None:
    slot = acquire_slot(cfg)
    try:
        assert slot.exists()
        assert slot.read_text().strip() == str(os.getpid())
    finally:
        release_slot(slot)


def test_release_removes_lock_file(cfg: ConcurrencyConfig) -> None:
    slot = acquire_slot(cfg)
    release_slot(slot)
    assert not slot.exists()


def test_running_count_reflects_live_slots(cfg: ConcurrencyConfig) -> None:
    assert running_count(cfg) == 0
    slot = acquire_slot(cfg)
    try:
        assert running_count(cfg) == 1
    finally:
        release_slot(slot)
    assert running_count(cfg) == 0


def test_exceeds_limit_raises(cfg: ConcurrencyConfig) -> None:
    """With max_instances=2, a third acquire should raise."""
    # Simulate two existing live slots by writing lock files with the current PID.
    pid = os.getpid()
    slot1 = cfg.lock_dir / f"backup.{pid}.lock"
    slot2 = cfg.lock_dir / f"backup.{pid + 1}.lock"
    slot1.write_text(str(pid))
    # Make slot2 appear alive by pointing it to our own PID as well
    slot2.write_text(str(pid))
    try:
        with pytest.raises(ConcurrencyLimitExceeded) as exc_info:
            acquire_slot(cfg)
        assert exc_info.value.limit == 2
        assert exc_info.value.job_name == "backup"
    finally:
        slot1.unlink(missing_ok=True)
        slot2.unlink(missing_ok=True)


def test_stale_locks_cleaned_up(cfg: ConcurrencyConfig) -> None:
    """Lock files referencing dead PIDs are removed and not counted."""
    stale = cfg.lock_dir / "backup.99999999.lock"
    cfg.lock_dir.mkdir(parents=True, exist_ok=True)
    stale.write_text("99999999")
    live = _live_slots(cfg)
    assert len(live) == 0
    assert not stale.exists()


def test_acquire_disabled_returns_devnull(tmp_path: Path) -> None:
    c = ConcurrencyConfig(max_instances=0, lock_dir=tmp_path, job_name="")
    slot = acquire_slot(c)
    assert str(slot) == os.devnull


def test_concurrency_limit_exceeded_message(cfg: ConcurrencyConfig) -> None:
    err = ConcurrencyLimitExceeded("myjob", 3, 2)
    assert "myjob" in str(err)
    assert "3" in str(err)
    assert "2" in str(err)
