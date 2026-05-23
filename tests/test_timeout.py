"""Tests for cronwrap.timeout."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from cronwrap.timeout import TimeoutConfig, TimeoutExpired, wait_with_timeout


# ---------------------------------------------------------------------------
# TimeoutConfig
# ---------------------------------------------------------------------------

def test_timeout_disabled_by_default():
    cfg = TimeoutConfig()
    assert not cfg.is_enabled()


def test_timeout_enabled_with_positive_seconds():
    cfg = TimeoutConfig(seconds=30)
    assert cfg.is_enabled()


def test_timeout_disabled_when_zero():
    cfg = TimeoutConfig(seconds=0)
    assert not cfg.is_enabled()


# ---------------------------------------------------------------------------
# TimeoutExpired
# ---------------------------------------------------------------------------

def test_timeout_expired_message():
    exc = TimeoutExpired("backup", 60)
    assert "backup" in str(exc)
    assert "60" in str(exc)
    assert exc.job_name == "backup"
    assert exc.seconds == 60


# ---------------------------------------------------------------------------
# wait_with_timeout — happy path
# ---------------------------------------------------------------------------

def _make_proc(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    proc = MagicMock(spec=subprocess.Popen)
    proc.returncode = returncode
    proc.communicate.return_value = (stdout, stderr)
    return proc


def test_successful_process_returns_output():
    proc = _make_proc(returncode=0, stdout="hello", stderr="")
    cfg = TimeoutConfig(seconds=10)
    rc, out, err = wait_with_timeout(proc, cfg, job_name="demo")
    assert rc == 0
    assert out == "hello"
    assert err == ""


def test_no_timeout_passes_none_to_communicate():
    proc = _make_proc()
    cfg = TimeoutConfig()  # disabled
    wait_with_timeout(proc, cfg, job_name="demo")
    proc.communicate.assert_called_once_with(timeout=None)


def test_timeout_value_forwarded_to_communicate():
    proc = _make_proc()
    cfg = TimeoutConfig(seconds=45)
    wait_with_timeout(proc, cfg, job_name="demo")
    proc.communicate.assert_called_once_with(timeout=45)


# ---------------------------------------------------------------------------
# wait_with_timeout — timeout path
# ---------------------------------------------------------------------------

def test_raises_timeout_expired_on_slow_process():
    proc = MagicMock(spec=subprocess.Popen)
    proc.communicate.side_effect = [
        subprocess.TimeoutExpired(cmd="sleep", timeout=5),
        ("", ""),  # after terminate()
    ]
    cfg = TimeoutConfig(seconds=5, kill_after=2)

    with pytest.raises(TimeoutExpired) as exc_info:
        wait_with_timeout(proc, cfg, job_name="slow_job")

    assert exc_info.value.job_name == "slow_job"
    proc.terminate.assert_called_once()


def test_sigkill_sent_when_terminate_also_times_out():
    proc = MagicMock(spec=subprocess.Popen)
    proc.communicate.side_effect = [
        subprocess.TimeoutExpired(cmd="sleep", timeout=5),
        subprocess.TimeoutExpired(cmd="sleep", timeout=2),
        ("", ""),  # after kill()
    ]
    cfg = TimeoutConfig(seconds=5, kill_after=2)

    with pytest.raises(TimeoutExpired):
        wait_with_timeout(proc, cfg, job_name="zombie")

    proc.kill.assert_called_once()
