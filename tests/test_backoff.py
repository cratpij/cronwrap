"""Tests for cronwrap.backoff."""

import pytest

from cronwrap.backoff import BackoffConfig, compute_delay, from_env, is_enabled


# ---------------------------------------------------------------------------
# BackoffConfig validation
# ---------------------------------------------------------------------------

def test_default_config_is_enabled():
    cfg = BackoffConfig()
    assert is_enabled(cfg) is True


def test_zero_base_delay_disables_backoff():
    cfg = BackoffConfig(base_delay=0.0)
    assert is_enabled(cfg) is False


def test_negative_base_delay_raises():
    with pytest.raises(ValueError, match="base_delay"):
        BackoffConfig(base_delay=-1.0)


def test_max_delay_less_than_base_raises():
    with pytest.raises(ValueError, match="max_delay"):
        BackoffConfig(base_delay=10.0, max_delay=5.0)


def test_multiplier_less_than_one_raises():
    with pytest.raises(ValueError, match="multiplier"):
        BackoffConfig(multiplier=0.5)


# ---------------------------------------------------------------------------
# compute_delay — no jitter for deterministic assertions
# ---------------------------------------------------------------------------

def test_compute_delay_disabled_returns_zero():
    cfg = BackoffConfig(base_delay=0.0, jitter=False)
    assert compute_delay(cfg, attempt=0) == 0.0


def test_compute_delay_negative_attempt_returns_zero():
    cfg = BackoffConfig(base_delay=1.0, jitter=False)
    assert compute_delay(cfg, attempt=-1) == 0.0


def test_compute_delay_first_attempt_equals_base():
    cfg = BackoffConfig(base_delay=2.0, multiplier=2.0, max_delay=120.0, jitter=False)
    assert compute_delay(cfg, attempt=0) == pytest.approx(2.0)


def test_compute_delay_second_attempt_doubles():
    cfg = BackoffConfig(base_delay=2.0, multiplier=2.0, max_delay=120.0, jitter=False)
    assert compute_delay(cfg, attempt=1) == pytest.approx(4.0)


def test_compute_delay_capped_at_max():
    cfg = BackoffConfig(base_delay=1.0, multiplier=10.0, max_delay=5.0, jitter=False)
    # 1 * 10^3 = 1000, but capped at 5
    assert compute_delay(cfg, attempt=3) == pytest.approx(5.0)


def test_compute_delay_with_jitter_within_bounds():
    cfg = BackoffConfig(base_delay=4.0, multiplier=2.0, max_delay=60.0, jitter=True)
    for _ in range(50):
        delay = compute_delay(cfg, attempt=0)
        # base=4, jitter ±25% → [3.0, 5.0]
        assert 0.0 <= delay <= 60.0


# ---------------------------------------------------------------------------
# from_env
# ---------------------------------------------------------------------------

def test_from_env_defaults():
    cfg = from_env(env={})
    assert cfg.base_delay == pytest.approx(1.0)
    assert cfg.max_delay == pytest.approx(60.0)
    assert cfg.multiplier == pytest.approx(2.0)
    assert cfg.jitter is True


def test_from_env_custom_values():
    env = {
        "CRONWRAP_BACKOFF_BASE_DELAY": "3.0",
        "CRONWRAP_BACKOFF_MAX_DELAY": "30.0",
        "CRONWRAP_BACKOFF_MULTIPLIER": "3.0",
        "CRONWRAP_BACKOFF_JITTER": "false",
    }
    cfg = from_env(env=env)
    assert cfg.base_delay == pytest.approx(3.0)
    assert cfg.max_delay == pytest.approx(30.0)
    assert cfg.multiplier == pytest.approx(3.0)
    assert cfg.jitter is False


def test_from_env_invalid_float_falls_back_to_default():
    cfg = from_env(env={"CRONWRAP_BACKOFF_BASE_DELAY": "not-a-number"})
    assert cfg.base_delay == pytest.approx(1.0)


def test_from_env_jitter_disabled_via_zero():
    cfg = from_env(env={"CRONWRAP_BACKOFF_JITTER": "0"})
    assert cfg.jitter is False
