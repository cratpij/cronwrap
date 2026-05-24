"""Tests for cronwrap.rate_limit."""
import json
import time
from pathlib import Path

import pytest

from cronwrap.rate_limit import (
    RateLimitConfig,
    RateLimitState,
    _state_path,
    check_rate_limit,
    load_state,
    save_state,
)


@pytest.fixture
def cfg(tmp_path):
    return RateLimitConfig(
        max_runs=3,
        window_seconds=60,
        state_dir=tmp_path,
        job_name="my-job",
    )


def test_is_enabled_with_positive_values(cfg):
    assert cfg.is_enabled() is True


def test_is_disabled_when_max_runs_zero(tmp_path):
    cfg = RateLimitConfig(max_runs=0, window_seconds=60, state_dir=tmp_path, job_name="j")
    assert cfg.is_enabled() is False


def test_is_disabled_when_window_zero(tmp_path):
    cfg = RateLimitConfig(max_runs=3, window_seconds=0, state_dir=tmp_path, job_name="j")
    assert cfg.is_enabled() is False


def test_state_roundtrip():
    state = RateLimitState(run_timestamps=[1.0, 2.0, 3.0])
    assert RateLimitState.from_dict(state.to_dict()).run_timestamps == [1.0, 2.0, 3.0]


def test_state_from_dict_defaults_empty():
    state = RateLimitState.from_dict({})
    assert state.run_timestamps == []


def test_state_path_uses_job_name(cfg):
    p = _state_path(cfg)
    assert "my-job" in p.name
    assert p.suffix == ".json"


def test_state_path_sanitises_slashes(tmp_path):
    cfg = RateLimitConfig(max_runs=1, window_seconds=60, state_dir=tmp_path, job_name="a/b")
    assert "/" not in _state_path(cfg).name


def test_load_state_missing_file_returns_empty(cfg):
    state = load_state(cfg)
    assert state.run_timestamps == []


def test_save_and_load_roundtrip(cfg):
    state = RateLimitState(run_timestamps=[100.0, 200.0])
    save_state(cfg, state)
    loaded = load_state(cfg)
    assert loaded.run_timestamps == [100.0, 200.0]


def test_check_rate_limit_allows_under_limit(cfg):
    now = time.time()
    assert check_rate_limit(cfg, now=now) is True
    assert check_rate_limit(cfg, now=now + 1) is True
    assert check_rate_limit(cfg, now=now + 2) is True


def test_check_rate_limit_blocks_over_limit(cfg):
    now = time.time()
    for i in range(3):
        check_rate_limit(cfg, now=now + i)
    assert check_rate_limit(cfg, now=now + 3) is False


def test_check_rate_limit_resets_after_window(cfg):
    now = time.time()
    for i in range(3):
        check_rate_limit(cfg, now=now + i)
    # advance past the window
    assert check_rate_limit(cfg, now=now + 120) is True


def test_check_rate_limit_disabled_always_allows(tmp_path):
    cfg = RateLimitConfig(max_runs=0, window_seconds=60, state_dir=tmp_path, job_name="j")
    for _ in range(10):
        assert check_rate_limit(cfg) is True


def test_check_rate_limit_creates_state_dir(tmp_path):
    state_dir = tmp_path / "nested" / "dir"
    cfg = RateLimitConfig(max_runs=2, window_seconds=30, state_dir=state_dir, job_name="j")
    assert check_rate_limit(cfg) is True
    assert state_dir.exists()
