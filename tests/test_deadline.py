"""Tests for cronwrap.deadline."""
from __future__ import annotations

import pytest

from cronwrap.deadline import DeadlineConfig, DeadlineMissed, check_deadline


# ---------------------------------------------------------------------------
# DeadlineConfig.is_enabled
# ---------------------------------------------------------------------------

def test_is_disabled_by_default():
    cfg = DeadlineConfig()
    assert cfg.is_enabled() is False


def test_is_disabled_when_max_delay_zero():
    cfg = DeadlineConfig(max_delay_seconds=0, scheduled_at=1_000_000.0)
    assert cfg.is_enabled() is False


def test_is_disabled_when_scheduled_at_none():
    cfg = DeadlineConfig(max_delay_seconds=60, scheduled_at=None)
    assert cfg.is_enabled() is False


def test_is_enabled_with_both_fields():
    cfg = DeadlineConfig(max_delay_seconds=60, scheduled_at=1_000_000.0)
    assert cfg.is_enabled() is True


# ---------------------------------------------------------------------------
# DeadlineMissed
# ---------------------------------------------------------------------------

def test_deadline_missed_message():
    exc = DeadlineMissed(delay=75.3, max_delay=60)
    assert "75.3" in str(exc)
    assert "60" in str(exc)
    assert exc.delay == 75.3
    assert exc.max_delay == 60


# ---------------------------------------------------------------------------
# check_deadline
# ---------------------------------------------------------------------------

def test_check_deadline_noop_when_disabled():
    cfg = DeadlineConfig()  # disabled
    # Should not raise regardless of time.
    check_deadline(cfg, now=9_999_999.0)


def test_check_deadline_passes_when_within_window():
    scheduled = 1_000_000.0
    cfg = DeadlineConfig(max_delay_seconds=60, scheduled_at=scheduled)
    # 30 seconds late — within the 60-second window.
    check_deadline(cfg, now=scheduled + 30)


def test_check_deadline_passes_at_exact_boundary():
    scheduled = 1_000_000.0
    cfg = DeadlineConfig(max_delay_seconds=60, scheduled_at=scheduled)
    # Exactly at the boundary — still allowed.
    check_deadline(cfg, now=scheduled + 60)


def test_check_deadline_raises_when_past_deadline():
    scheduled = 1_000_000.0
    cfg = DeadlineConfig(max_delay_seconds=60, scheduled_at=scheduled)
    with pytest.raises(DeadlineMissed) as exc_info:
        check_deadline(cfg, now=scheduled + 61)
    assert exc_info.value.delay == pytest.approx(61.0)
    assert exc_info.value.max_delay == 60


def test_check_deadline_uses_real_clock_when_now_omitted(monkeypatch):
    """When *now* is None the function calls time.time()."""
    import cronwrap.deadline as dl_mod
    scheduled = 1_000_000.0
    monkeypatch.setattr(dl_mod.time, "time", lambda: scheduled + 5)
    cfg = DeadlineConfig(max_delay_seconds=60, scheduled_at=scheduled)
    check_deadline(cfg)  # should not raise
