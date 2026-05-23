"""Tests for cronwrap.alert_config environment-based factory."""

import pytest

from cronwrap.alert_config import from_env, _DEFAULT_COOLDOWN, _DEFAULT_STATE_DIR


def test_defaults_when_no_env_vars(monkeypatch):
    monkeypatch.delenv("CRONWRAP_ALERT_DIR", raising=False)
    monkeypatch.delenv("CRONWRAP_ALERT_COOLDOWN", raising=False)
    cfg = from_env()
    assert cfg.state_dir == _DEFAULT_STATE_DIR
    assert cfg.cooldown_seconds == _DEFAULT_COOLDOWN


def test_custom_dir_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CRONWRAP_ALERT_DIR", str(tmp_path / "myalerts"))
    monkeypatch.delenv("CRONWRAP_ALERT_COOLDOWN", raising=False)
    cfg = from_env()
    assert cfg.state_dir == tmp_path / "myalerts"


def test_custom_cooldown_from_env(monkeypatch):
    monkeypatch.delenv("CRONWRAP_ALERT_DIR", raising=False)
    monkeypatch.setenv("CRONWRAP_ALERT_COOLDOWN", "120")
    cfg = from_env()
    assert cfg.cooldown_seconds == 120


def test_invalid_cooldown_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("CRONWRAP_ALERT_COOLDOWN", "not-a-number")
    cfg = from_env()
    assert cfg.cooldown_seconds == _DEFAULT_COOLDOWN


def test_negative_cooldown_clamped_to_zero(monkeypatch):
    monkeypatch.setenv("CRONWRAP_ALERT_COOLDOWN", "-60")
    cfg = from_env()
    assert cfg.cooldown_seconds == 0


def test_zero_cooldown_means_always_alert(monkeypatch):
    monkeypatch.setenv("CRONWRAP_ALERT_COOLDOWN", "0")
    cfg = from_env()
    assert cfg.cooldown_seconds == 0
