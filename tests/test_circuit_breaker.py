"""Tests for cronwrap.circuit_breaker and cronwrap.circuit_breaker_config."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from cronwrap.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    check_circuit,
    load_state,
    record_failure,
    record_success,
    save_state,
)


@pytest.fixture()
def cfg(tmp_path):
    return CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=60,
        state_dir=str(tmp_path / "circuit"),
    )


def test_circuit_state_roundtrip():
    s = CircuitState(consecutive_failures=2, opened_at=1234.5, state="open")
    assert CircuitState.from_dict(s.to_dict()) == s


def test_circuit_state_from_dict_defaults():
    s = CircuitState.from_dict({})
    assert s.consecutive_failures == 0
    assert s.opened_at is None
    assert s.state == "closed"


def test_load_state_returns_default_when_missing(cfg):
    state = load_state("myjob", cfg)
    assert state.state == "closed"
    assert state.consecutive_failures == 0


def test_save_and_load_roundtrip(cfg):
    state = CircuitState(consecutive_failures=1, state="closed")
    save_state("myjob", cfg, state)
    loaded = load_state("myjob", cfg)
    assert loaded.consecutive_failures == 1
    assert loaded.state == "closed"


def test_record_success_resets_state(cfg):
    record_failure("job", cfg)
    record_failure("job", cfg)
    state = record_success("job", cfg)
    assert state.consecutive_failures == 0
    assert state.state == "closed"
    assert state.opened_at is None


def test_record_failure_increments_count(cfg):
    state = record_failure("job", cfg)
    assert state.consecutive_failures == 1
    assert state.state == "closed"


def test_record_failure_opens_circuit_at_threshold(cfg):
    for _ in range(3):
        state = record_failure("job", cfg)
    assert state.state == "open"
    assert state.opened_at is not None


def test_record_failure_beyond_threshold_stays_open(cfg):
    for _ in range(5):
        state = record_failure("job", cfg)
    assert state.state == "open"
    assert state.consecutive_failures == 5


def test_check_circuit_passes_when_closed(cfg):
    state = check_circuit("job", cfg)
    assert state.state == "closed"


def test_check_circuit_raises_when_open(cfg):
    for _ in range(3):
        record_failure("job", cfg)
    with pytest.raises(CircuitOpenError, match="Circuit open"):
        check_circuit("job", cfg)


def test_check_circuit_transitions_to_half_open_after_timeout(cfg, monkeypatch):
    for _ in range(3):
        record_failure("job", cfg)
    # Simulate recovery timeout elapsed
    monkeypatch.setattr(time, "time", lambda: time.time() + 120)
    state = check_circuit("job", cfg)
    assert state.state == "half-open"


def test_check_circuit_disabled_when_threshold_zero(tmp_path):
    cfg = CircuitBreakerConfig(
        failure_threshold=0,
        recovery_timeout=60,
        state_dir=str(tmp_path),
    )
    # Even after many failures, disabled config never raises
    state = check_circuit("job", cfg)
    assert state.state == "closed"


def test_state_file_uses_safe_name(cfg, tmp_path):
    save_state("my job/name", cfg, CircuitState())
    files = list(Path(cfg.state_dir).iterdir())
    assert len(files) == 1
    assert " " not in files[0].name


# --- circuit_breaker_config tests ---

def test_from_env_returns_none_when_not_set(monkeypatch):
    from cronwrap import circuit_breaker_config
    monkeypatch.delenv("CRONWRAP_CB_FAILURE_THRESHOLD", raising=False)
    assert circuit_breaker_config.from_env() is None


def test_from_env_returns_config_when_set(monkeypatch):
    from cronwrap import circuit_breaker_config
    monkeypatch.setenv("CRONWRAP_CB_FAILURE_THRESHOLD", "4")
    monkeypatch.setenv("CRONWRAP_CB_RECOVERY_TIMEOUT", "120")
    monkeypatch.delenv("CRONWRAP_CB_STATE_DIR", raising=False)
    cfg = circuit_breaker_config.from_env()
    assert cfg is not None
    assert cfg.failure_threshold == 4
    assert cfg.recovery_timeout == 120


def test_from_env_invalid_threshold_falls_back_to_default(monkeypatch):
    from cronwrap import circuit_breaker_config
    monkeypatch.setenv("CRONWRAP_CB_FAILURE_THRESHOLD", "notanint")
    cfg = circuit_breaker_config.from_env()
    assert cfg.failure_threshold == 5


def test_from_env_custom_state_dir(monkeypatch, tmp_path):
    from cronwrap import circuit_breaker_config
    monkeypatch.setenv("CRONWRAP_CB_FAILURE_THRESHOLD", "3")
    monkeypatch.setenv("CRONWRAP_CB_STATE_DIR", str(tmp_path))
    cfg = circuit_breaker_config.from_env()
    assert cfg.state_dir == str(tmp_path)
