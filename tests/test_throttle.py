"""Tests for cronwrap.throttle and cronwrap.throttle_config."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from cronwrap.throttle import (
    ThrottleBlocked,
    ThrottleConfig,
    ThrottleState,
    check_throttle,
    load_state,
    record_run,
    save_state,
    _state_path,
)


@pytest.fixture()
def cfg(tmp_path: Path) -> ThrottleConfig:
    return ThrottleConfig(job_name="test_job", min_interval_seconds=300, state_dir=tmp_path)


# --- ThrottleConfig ---

def test_throttle_disabled_when_zero(tmp_path):
    cfg = ThrottleConfig(job_name="j", min_interval_seconds=0, state_dir=tmp_path)
    assert not cfg.is_enabled


def test_throttle_enabled_with_positive_seconds(cfg):
    assert cfg.is_enabled


# --- ThrottleState ---

def test_state_roundtrip():
    state = ThrottleState(last_run_at=1_700_000_000.0)
    assert ThrottleState.from_dict(state.to_dict()).last_run_at == 1_700_000_000.0


def test_state_from_dict_defaults_last_run_at():
    state = ThrottleState.from_dict({})
    assert state.last_run_at == 0.0


# --- save_state / load_state ---

def test_save_creates_file(cfg, tmp_path):
    save_state(cfg, ThrottleState(last_run_at=12345.0))
    assert _state_path(cfg).exists()


def test_load_returns_none_when_missing(cfg):
    assert load_state(cfg) is None


def test_save_and_load_roundtrip(cfg):
    save_state(cfg, ThrottleState(last_run_at=9999.5))
    loaded = load_state(cfg)
    assert loaded is not None
    assert loaded.last_run_at == 9999.5


def test_load_returns_none_on_corrupt_file(cfg, tmp_path):
    _state_path(cfg).write_text("not json")
    assert load_state(cfg) is None


# --- check_throttle ---

def test_check_throttle_passes_when_disabled(tmp_path):
    cfg = ThrottleConfig(job_name="j", min_interval_seconds=0, state_dir=tmp_path)
    check_throttle(cfg)  # should not raise


def test_check_throttle_passes_when_no_state(cfg):
    check_throttle(cfg)  # no state file -> first run allowed


def test_check_throttle_passes_after_interval(cfg):
    past = time.time() - 400  # 400s ago, interval is 300s
    save_state(cfg, ThrottleState(last_run_at=past))
    check_throttle(cfg)  # should not raise


def test_check_throttle_blocks_within_interval(cfg):
    recent = time.time() - 60  # only 60s ago, interval is 300s
    save_state(cfg, ThrottleState(last_run_at=recent))
    with pytest.raises(ThrottleBlocked) as exc_info:
        check_throttle(cfg)
    assert exc_info.value.seconds_remaining > 0
    assert "test_job" in str(exc_info.value)


# --- record_run ---

def test_record_run_saves_state(cfg):
    now = time.time()
    record_run(cfg, now=now)
    state = load_state(cfg)
    assert state is not None
    assert state.last_run_at == now


def test_record_run_noop_when_disabled(tmp_path):
    cfg = ThrottleConfig(job_name="j", min_interval_seconds=0, state_dir=tmp_path)
    record_run(cfg)  # should not create any file
    assert not _state_path(cfg).exists()


# --- throttle_config.from_env ---

def test_from_env_returns_none_when_no_env(monkeypatch, tmp_path):
    from cronwrap import throttle_config
    monkeypatch.delenv("CRONWRAP_THROTTLE_SECONDS", raising=False)
    assert throttle_config.from_env("myjob") is None


def test_from_env_returns_config_when_set(monkeypatch, tmp_path):
    from cronwrap import throttle_config
    monkeypatch.setenv("CRONWRAP_THROTTLE_SECONDS", "600")
    monkeypatch.setenv("CRONWRAP_THROTTLE_DIR", str(tmp_path))
    cfg = throttle_config.from_env("myjob")
    assert cfg is not None
    assert cfg.min_interval_seconds == 600
    assert cfg.state_dir == tmp_path


def test_from_env_invalid_seconds_returns_none(monkeypatch):
    from cronwrap import throttle_config
    monkeypatch.setenv("CRONWRAP_THROTTLE_SECONDS", "bad")
    assert throttle_config.from_env("myjob") is None


def test_from_env_negative_seconds_clamped_to_none(monkeypatch):
    from cronwrap import throttle_config
    monkeypatch.setenv("CRONWRAP_THROTTLE_SECONDS", "-10")
    assert throttle_config.from_env("myjob") is None
