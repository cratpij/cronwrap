"""Tests for cronwrap.env_filter."""
import pytest

from cronwrap.env_filter import (
    EnvFilterConfig,
    filter_env,
    is_sensitive,
    safe_env,
)

_SAMPLE_ENV = {
    "PATH": "/usr/bin",
    "HOME": "/root",
    "DB_PASSWORD": "s3cr3t",
    "API_TOKEN": "tok_abc",
    "MY_SECRET_KEY": "hidden",
    "PRIVATE_KEY": "pem_data",
    "APP_CREDENTIAL": "cred",
    "NORMAL_VAR": "value",
}


def test_is_sensitive_password():
    assert is_sensitive("DB_PASSWORD", []) is True


def test_is_sensitive_token():
    assert is_sensitive("API_TOKEN", []) is True


def test_is_sensitive_secret():
    assert is_sensitive("MY_SECRET_KEY", []) is True


def test_is_sensitive_private():
    assert is_sensitive("PRIVATE_KEY", []) is True


def test_is_sensitive_credential():
    assert is_sensitive("APP_CREDENTIAL", []) is True


def test_is_sensitive_normal_var_is_false():
    assert is_sensitive("NORMAL_VAR", []) is False


def test_is_sensitive_extra_strip():
    assert is_sensitive("MY_CUSTOM_VAR", ["MY_CUSTOM_VAR"]) is True


def test_is_sensitive_case_insensitive_extra():
    assert is_sensitive("my_custom_var", ["MY_CUSTOM_VAR"]) is True


def test_filter_env_removes_sensitive_by_default():
    cfg = EnvFilterConfig()
    result = filter_env(_SAMPLE_ENV, cfg)
    assert "DB_PASSWORD" not in result
    assert "API_TOKEN" not in result
    assert "PATH" in result
    assert "NORMAL_VAR" in result


def test_filter_env_redact_mode_keeps_key():
    cfg = EnvFilterConfig(redact=True)
    result = filter_env(_SAMPLE_ENV, cfg)
    assert result["DB_PASSWORD"] == "***REDACTED***"
    assert result["API_TOKEN"] == "***REDACTED***"


def test_filter_env_custom_redact_placeholder():
    cfg = EnvFilterConfig(redact=True, redact_placeholder="<hidden>")
    result = filter_env({"MY_SECRET": "val"}, cfg)
    assert result["MY_SECRET"] == "<hidden>"


def test_filter_env_allowlist_mode():
    cfg = EnvFilterConfig(allowlist=["PATH", "HOME"])
    result = filter_env(_SAMPLE_ENV, cfg)
    assert set(result.keys()) == {"PATH", "HOME"}


def test_filter_env_allowlist_excludes_sensitive():
    cfg = EnvFilterConfig(allowlist=["PATH", "DB_PASSWORD"])
    result = filter_env(_SAMPLE_ENV, cfg)
    # DB_PASSWORD is in allowlist but still sensitive → stripped
    assert "DB_PASSWORD" not in result
    assert "PATH" in result


def test_filter_env_extra_strip_vars():
    cfg = EnvFilterConfig(strip_vars=["NORMAL_VAR"])
    result = filter_env(_SAMPLE_ENV, cfg)
    assert "NORMAL_VAR" not in result


def test_safe_env_returns_dict(monkeypatch):
    monkeypatch.setenv("SAFE_VAR", "hello")
    monkeypatch.setenv("DB_PASSWORD", "should_be_gone")
    result = safe_env()
    assert "SAFE_VAR" in result
    assert "DB_PASSWORD" not in result
