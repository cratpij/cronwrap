"""Tests for cronwrap.deadline_config."""
from __future__ import annotations

import pytest

from cronwrap.deadline_config import from_env


def test_returns_none_when_no_env_vars():
    assert from_env({}) is None


def test_returns_none_when_deadline_zero():
    assert from_env({"CRONWRAP_DEADLINE_SECONDS": "0"}) is None


def test_returns_none_when_deadline_negative():
    # Negative values are clamped to 0, which disables the feature.
    assert from_env({"CRONWRAP_DEADLINE_SECONDS": "-30"}) is None


def test_returns_none_when_deadline_invalid():
    assert from_env({"CRONWRAP_DEADLINE_SECONDS": "abc"}) is None


def test_returns_config_with_valid_deadline_no_scheduled_at():
    cfg = from_env({"CRONWRAP_DEADLINE_SECONDS": "120"})
    assert cfg is not None
    assert cfg.max_delay_seconds == 120
    assert cfg.scheduled_at is None
    # is_enabled() requires scheduled_at, so it should be False here.
    assert cfg.is_enabled() is False


def test_returns_config_with_deadline_and_scheduled_at():
    env = {
        "CRONWRAP_DEADLINE_SECONDS": "60",
        "CRONWRAP_SCHEDULED_AT": "1700000000.0",
    }
    cfg = from_env(env)
    assert cfg is not None
    assert cfg.max_delay_seconds == 60
    assert cfg.scheduled_at == pytest.approx(1_700_000_000.0)
    assert cfg.is_enabled() is True


def test_invalid_scheduled_at_treated_as_none():
    env = {
        "CRONWRAP_DEADLINE_SECONDS": "60",
        "CRONWRAP_SCHEDULED_AT": "not-a-float",
    }
    cfg = from_env(env)
    assert cfg is not None
    assert cfg.scheduled_at is None


def test_empty_scheduled_at_treated_as_none():
    env = {
        "CRONWRAP_DEADLINE_SECONDS": "60",
        "CRONWRAP_SCHEDULED_AT": "",
    }
    cfg = from_env(env)
    assert cfg is not None
    assert cfg.scheduled_at is None


def test_reads_from_os_environ_by_default(monkeypatch):
    monkeypatch.setenv("CRONWRAP_DEADLINE_SECONDS", "45")
    monkeypatch.setenv("CRONWRAP_SCHEDULED_AT", "1234567890.5")
    cfg = from_env()
    assert cfg is not None
    assert cfg.max_delay_seconds == 45
    assert cfg.scheduled_at == pytest.approx(1_234_567_890.5)
