"""Tests for cronwrap.jitter."""

from __future__ import annotations

import pytest

from cronwrap.jitter import JitterConfig, apply_jitter, sample_delay


# ---------------------------------------------------------------------------
# JitterConfig
# ---------------------------------------------------------------------------

def test_jitter_disabled_by_default():
    cfg = JitterConfig()
    assert cfg.is_enabled() is False


def test_jitter_enabled_with_positive_max():
    cfg = JitterConfig(max_seconds=5)
    assert cfg.is_enabled() is True


def test_jitter_disabled_when_zero():
    cfg = JitterConfig(max_seconds=0)
    assert cfg.is_enabled() is False


# ---------------------------------------------------------------------------
# sample_delay
# ---------------------------------------------------------------------------

def test_sample_delay_zero_when_disabled():
    cfg = JitterConfig(max_seconds=0)
    assert sample_delay(cfg) == 0.0


def test_sample_delay_within_bounds():
    cfg = JitterConfig(max_seconds=10)
    for _ in range(50):
        delay = sample_delay(cfg)
        assert 0.0 <= delay <= 10.0


def test_sample_delay_deterministic_with_seed():
    cfg = JitterConfig(max_seconds=30, seed=42)
    d1 = sample_delay(cfg)
    d2 = sample_delay(cfg)
    assert d1 == d2


def test_sample_delay_different_seeds_differ():
    d1 = sample_delay(JitterConfig(max_seconds=100, seed=1))
    d2 = sample_delay(JitterConfig(max_seconds=100, seed=2))
    assert d1 != d2


# ---------------------------------------------------------------------------
# apply_jitter
# ---------------------------------------------------------------------------

def test_apply_jitter_disabled_returns_zero():
    slept = []
    result = apply_jitter(JitterConfig(max_seconds=0), _sleep=slept.append)
    assert result == 0.0
    assert slept == []


def test_apply_jitter_enabled_calls_sleep():
    slept = []
    cfg = JitterConfig(max_seconds=5, seed=7)
    result = apply_jitter(cfg, _sleep=slept.append)
    assert len(slept) == 1
    assert slept[0] == result
    assert 0.0 < result <= 5.0


def test_apply_jitter_returns_actual_sleep_duration():
    recorded = []
    cfg = JitterConfig(max_seconds=20, seed=99)
    delay = apply_jitter(cfg, _sleep=recorded.append)
    assert delay == recorded[0]
