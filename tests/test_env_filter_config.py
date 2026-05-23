"""Tests for cronwrap.env_filter_config."""
import pytest

from cronwrap.env_filter_config import from_env


def test_returns_none_when_no_env_vars(monkeypatch):
    monkeypatch.delenv("CRONWRAP_ENV_STRIP_VARS", raising=False)
    monkeypatch.delenv("CRONWRAP_ENV_ALLOWLIST", raising=False)
    monkeypatch.delenv("CRONWRAP_ENV_REDACT", raising=False)
    monkeypatch.delenv("CRONWRAP_ENV_REDACT_PLACEHOLDER", raising=False)
    assert from_env() is None


def test_strip_vars_parsed_from_env(monkeypatch):
    monkeypatch.setenv("CRONWRAP_ENV_STRIP_VARS", "FOO,BAR, BAZ ")
    monkeypatch.delenv("CRONWRAP_ENV_ALLOWLIST", raising=False)
    monkeypatch.delenv("CRONWRAP_ENV_REDACT", raising=False)
    cfg = from_env()
    assert cfg is not None
    assert cfg.strip_vars == ["FOO", "BAR", "BAZ"]


def test_allowlist_parsed_from_env(monkeypatch):
    monkeypatch.setenv("CRONWRAP_ENV_ALLOWLIST", "PATH,HOME")
    monkeypatch.delenv("CRONWRAP_ENV_STRIP_VARS", raising=False)
    monkeypatch.delenv("CRONWRAP_ENV_REDACT", raising=False)
    cfg = from_env()
    assert cfg is not None
    assert cfg.allowlist == ["PATH", "HOME"]


def test_allowlist_none_when_empty_string(monkeypatch):
    monkeypatch.setenv("CRONWRAP_ENV_ALLOWLIST", "")
    monkeypatch.setenv("CRONWRAP_ENV_STRIP_VARS", "FOO")
    monkeypatch.delenv("CRONWRAP_ENV_REDACT", raising=False)
    cfg = from_env()
    assert cfg is not None
    assert cfg.allowlist is None


@pytest.mark.parametrize("value", ["1", "true", "yes", "True", "YES"])
def test_redact_enabled(monkeypatch, value):
    monkeypatch.setenv("CRONWRAP_ENV_REDACT", value)
    monkeypatch.delenv("CRONWRAP_ENV_STRIP_VARS", raising=False)
    monkeypatch.delenv("CRONWRAP_ENV_ALLOWLIST", raising=False)
    cfg = from_env()
    assert cfg is not None
    assert cfg.redact is True


def test_custom_placeholder(monkeypatch):
    monkeypatch.setenv("CRONWRAP_ENV_REDACT", "1")
    monkeypatch.setenv("CRONWRAP_ENV_REDACT_PLACEHOLDER", "<HIDDEN>")
    monkeypatch.delenv("CRONWRAP_ENV_STRIP_VARS", raising=False)
    monkeypatch.delenv("CRONWRAP_ENV_ALLOWLIST", raising=False)
    cfg = from_env()
    assert cfg is not None
    assert cfg.redact_placeholder == "<HIDDEN>"


def test_redact_false_for_unknown_value(monkeypatch):
    monkeypatch.setenv("CRONWRAP_ENV_REDACT", "no")
    monkeypatch.setenv("CRONWRAP_ENV_STRIP_VARS", "SOME_VAR")
    monkeypatch.delenv("CRONWRAP_ENV_ALLOWLIST", raising=False)
    cfg = from_env()
    assert cfg is not None
    assert cfg.redact is False
