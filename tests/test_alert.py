"""Tests for cronwrap.alert throttling logic."""

import json
import time
from pathlib import Path

import pytest

from cronwrap.alert import (
    AlertConfig,
    AlertState,
    load_state,
    record_alert,
    save_state,
    should_alert,
)


@pytest.fixture()
def cfg(tmp_path: Path) -> AlertConfig:
    return AlertConfig(state_dir=tmp_path / "alerts", cooldown_seconds=600)


# ---------------------------------------------------------------------------
# AlertState serialisation
# ---------------------------------------------------------------------------

def test_alert_state_roundtrip():
    state = AlertState(job_name="backup", last_alerted_at=1_000_000.0, alert_count=3)
    assert AlertState.from_dict(state.to_dict()) == state


def test_alert_state_from_dict_defaults_count():
    data = {"job_name": "x", "last_alerted_at": 0.0}
    state = AlertState.from_dict(data)
    assert state.alert_count == 0


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------

def test_load_state_returns_none_when_missing(cfg):
    assert load_state(cfg, "nonexistent") is None


def test_save_and_load_roundtrip(cfg):
    state = AlertState(job_name="myjob", last_alerted_at=500.0, alert_count=1)
    save_state(cfg, state)
    loaded = load_state(cfg, "myjob")
    assert loaded == state


def test_save_creates_state_dir(tmp_path):
    cfg = AlertConfig(state_dir=tmp_path / "deep" / "nested")
    state = AlertState(job_name="j", last_alerted_at=1.0)
    save_state(cfg, state)
    assert (tmp_path / "deep" / "nested").is_dir()


def test_load_state_returns_none_on_corrupt_json(cfg):
    cfg.state_dir.mkdir(parents=True, exist_ok=True)
    (cfg.state_dir / "bad.alert.json").write_text("not-json")
    assert load_state(cfg, "bad") is None


# ---------------------------------------------------------------------------
# should_alert
# ---------------------------------------------------------------------------

def test_should_alert_true_when_no_prior_state(cfg):
    assert should_alert(cfg, "newjob") is True


def test_should_alert_false_within_cooldown(cfg):
    now = time.time()
    record_alert(cfg, "myjob", now=now)
    assert should_alert(cfg, "myjob", now=now + 10) is False


def test_should_alert_true_after_cooldown_expires(cfg):
    now = time.time()
    record_alert(cfg, "myjob", now=now)
    assert should_alert(cfg, "myjob", now=now + cfg.cooldown_seconds + 1) is True


def test_should_alert_true_exactly_at_cooldown_boundary(cfg):
    now = 1_000_000.0
    record_alert(cfg, "myjob", now=now)
    # exactly at boundary should be allowed
    assert should_alert(cfg, "myjob", now=now + cfg.cooldown_seconds) is True


# ---------------------------------------------------------------------------
# record_alert
# ---------------------------------------------------------------------------

def test_record_alert_increments_count(cfg):
    now = 1_000_000.0
    s1 = record_alert(cfg, "job", now=now)
    s2 = record_alert(cfg, "job", now=now + 700)
    assert s2.alert_count == 2


def test_record_alert_updates_timestamp(cfg):
    now = 1_000_000.0
    record_alert(cfg, "job", now=now)
    s2 = record_alert(cfg, "job", now=now + 700)
    assert s2.last_alerted_at == now + 700
