"""Tests for cronwrap.lock module."""

import os
import threading
import time
from pathlib import Path

import pytest

from cronwrap.lock import LockConfig, LockError, acquire_lock, is_locked


@pytest.fixture()
def lock_cfg(tmp_path: Path) -> LockConfig:
    return LockConfig(lock_dir=str(tmp_path), timeout=0.0)


# ---------------------------------------------------------------------------
# Basic acquire / release
# ---------------------------------------------------------------------------


def test_lock_file_created_inside_context(lock_cfg, tmp_path):
    with acquire_lock("myjob", lock_cfg) as lock_path:
        assert lock_path.exists()


def test_lock_file_removed_after_context(lock_cfg, tmp_path):
    with acquire_lock("myjob", lock_cfg) as lock_path:
        pass
    assert not lock_path.exists()


def test_lock_file_contains_pid(lock_cfg, tmp_path):
    with acquire_lock("myjob", lock_cfg) as lock_path:
        content = lock_path.read_text()
    assert str(os.getpid()) in content


def test_lock_dir_created_automatically(tmp_path):
    nested = tmp_path / "a" / "b" / "c"
    cfg = LockConfig(lock_dir=str(nested))
    with acquire_lock("myjob", cfg):
        assert nested.is_dir()


def test_safe_name_with_slashes(lock_cfg, tmp_path):
    with acquire_lock("/etc/cron.d/myjob", lock_cfg) as lock_path:
        assert "_" in lock_path.name
        assert "/" not in lock_path.name


# ---------------------------------------------------------------------------
# Contention
# ---------------------------------------------------------------------------


def test_second_acquire_raises_lock_error(lock_cfg):
    with acquire_lock("contended", lock_cfg):
        with pytest.raises(LockError, match="contended"):
            with acquire_lock("contended", lock_cfg):
                pass  # pragma: no cover


def test_is_locked_returns_false_when_free(lock_cfg):
    assert is_locked("free_job", lock_cfg) is False


def test_is_locked_returns_true_when_held(lock_cfg):
    ready = threading.Event()
    done = threading.Event()

    def holder():
        with acquire_lock("held_job", lock_cfg):
            ready.set()
            done.wait(timeout=5)

    t = threading.Thread(target=holder, daemon=True)
    t.start()
    ready.wait(timeout=5)

    assert is_locked("held_job", lock_cfg) is True

    done.set()
    t.join(timeout=5)


def test_lock_released_after_exception(lock_cfg):
    with pytest.raises(RuntimeError):
        with acquire_lock("exc_job", lock_cfg):
            raise RuntimeError("boom")

    # Should be acquirable again
    with acquire_lock("exc_job", lock_cfg):
        pass


# ---------------------------------------------------------------------------
# Timeout
# ---------------------------------------------------------------------------


def test_acquire_with_timeout_eventually_raises(lock_cfg):
    cfg = LockConfig(lock_dir=lock_cfg.lock_dir, timeout=0.2, poll_interval=0.05)
    ready = threading.Event()
    done = threading.Event()

    def holder():
        with acquire_lock("timeout_job", lock_cfg):
            ready.set()
            done.wait(timeout=5)

    t = threading.Thread(target=holder, daemon=True)
    t.start()
    ready.wait(timeout=5)

    with pytest.raises(LockError):
        with acquire_lock("timeout_job", cfg):
            pass  # pragma: no cover

    done.set()
    t.join(timeout=5)
