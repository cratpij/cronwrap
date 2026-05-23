"""Tests for cronwrap.webhook_config."""

from __future__ import annotations

import pytest

from cronwrap.webhook_config import from_env


def test_returns_none_when_no_url(monkeypatch):
    monkeypatch.delenv("CRONWRAP_WEBHOOK_URL", raising=False)
    assert from_env("myjob") is None


def test_returns_config_when_url_set(monkeypatch):
    monkeypatch.setenv("CRONWRAP_WEBHOOK_URL", "https://hooks.example.com/abc")
    cfg = from_env("myjob")
    assert cfg is not None
    assert cfg.url == "https://hooks.example.com/abc"
    assert cfg.job_name == "myjob"


def test_default_timeout(monkeypatch):
    monkeypatch.setenv("CRONWRAP_WEBHOOK_URL", "https://example.com")
    monkeypatch.delenv("CRONWRAP_WEBHOOK_TIMEOUT", raising=False)
    cfg = from_env("j")
    assert cfg.timeout_seconds == 10


def test_custom_timeout(monkeypatch):
    monkeypatch.setenv("CRONWRAP_WEBHOOK_URL", "https://example.com")
    monkeypatch.setenv("CRONWRAP_WEBHOOK_TIMEOUT", "30")
    cfg = from_env("j")
    assert cfg.timeout_seconds == 30


def test_invalid_timeout_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("CRONWRAP_WEBHOOK_URL", "https://example.com")
    monkeypatch.setenv("CRONWRAP_WEBHOOK_TIMEOUT", "notanumber")
    cfg = from_env("j")
    assert cfg.timeout_seconds == 10


def test_timeout_clamped_to_minimum(monkeypatch):
    monkeypatch.setenv("CRONWRAP_WEBHOOK_URL", "https://example.com")
    monkeypatch.setenv("CRONWRAP_WEBHOOK_TIMEOUT", "0")
    cfg = from_env("j")
    assert cfg.timeout_seconds >= 1


def test_token_added_as_bearer_header(monkeypatch):
    monkeypatch.setenv("CRONWRAP_WEBHOOK_URL", "https://example.com")
    monkeypatch.setenv("CRONWRAP_WEBHOOK_TOKEN", "secret123")
    cfg = from_env("j")
    assert cfg.extra_headers.get("Authorization") == "Bearer secret123"


def test_no_token_means_no_auth_header(monkeypatch):
    monkeypatch.setenv("CRONWRAP_WEBHOOK_URL", "https://example.com")
    monkeypatch.delenv("CRONWRAP_WEBHOOK_TOKEN", raising=False)
    cfg = from_env("j")
    assert "Authorization" not in cfg.extra_headers
