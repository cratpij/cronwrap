"""Tests for cronwrap.retry_policy."""

import pytest

from cronwrap.retry_policy import RetryPolicy, from_env


# ---------------------------------------------------------------------------
# Construction / validation
# ---------------------------------------------------------------------------

def test_default_policy_is_enabled():
    policy = RetryPolicy()
    assert policy.is_enabled() is True


def test_zero_retries_disables_policy():
    policy = RetryPolicy(max_retries=0)
    assert policy.is_enabled() is False


def test_negative_max_retries_raises():
    with pytest.raises(ValueError, match="max_retries"):
        RetryPolicy(max_retries=-1)


def test_negative_base_delay_raises():
    with pytest.raises(ValueError, match="base_delay"):
        RetryPolicy(base_delay=-1.0)


def test_max_delay_less_than_base_raises():
    with pytest.raises(ValueError, match="max_delay"):
        RetryPolicy(base_delay=10.0, max_delay=5.0)


# ---------------------------------------------------------------------------
# should_retry
# ---------------------------------------------------------------------------

def test_should_retry_within_limit():
    policy = RetryPolicy(max_retries=3)
    assert policy.should_retry(1) is True
    assert policy.should_retry(3) is True


def test_should_retry_beyond_limit():
    policy = RetryPolicy(max_retries=3)
    assert policy.should_retry(4) is False


# ---------------------------------------------------------------------------
# compute_delay — exponential
# ---------------------------------------------------------------------------

def test_compute_delay_first_attempt():
    policy = RetryPolicy(base_delay=5.0, exponential=True)
    assert policy.compute_delay(1) == 5.0


def test_compute_delay_second_attempt_doubles():
    policy = RetryPolicy(base_delay=5.0, exponential=True)
    assert policy.compute_delay(2) == 10.0


def test_compute_delay_capped_at_max():
    policy = RetryPolicy(base_delay=5.0, max_delay=15.0, exponential=True)
    # 5 * 2^3 = 40, capped at 15
    assert policy.compute_delay(4) == 15.0


def test_compute_delay_zero_attempt_returns_zero():
    policy = RetryPolicy(base_delay=5.0)
    assert policy.compute_delay(0) == 0.0


# ---------------------------------------------------------------------------
# compute_delay — linear (non-exponential)
# ---------------------------------------------------------------------------

def test_compute_delay_linear_constant():
    policy = RetryPolicy(base_delay=4.0, exponential=False)
    assert policy.compute_delay(1) == 4.0
    assert policy.compute_delay(3) == 4.0


# ---------------------------------------------------------------------------
# from_env
# ---------------------------------------------------------------------------

def test_from_env_returns_none_when_not_set(monkeypatch):
    monkeypatch.delenv("CRONWRAP_MAX_RETRIES", raising=False)
    assert from_env() is None


def test_from_env_reads_max_retries(monkeypatch):
    monkeypatch.setenv("CRONWRAP_MAX_RETRIES", "5")
    monkeypatch.delenv("CRONWRAP_RETRY_BASE_DELAY", raising=False)
    monkeypatch.delenv("CRONWRAP_RETRY_MAX_DELAY", raising=False)
    policy = from_env()
    assert policy is not None
    assert policy.max_retries == 5


def test_from_env_reads_delays(monkeypatch):
    monkeypatch.setenv("CRONWRAP_MAX_RETRIES", "2")
    monkeypatch.setenv("CRONWRAP_RETRY_BASE_DELAY", "3.0")
    monkeypatch.setenv("CRONWRAP_RETRY_MAX_DELAY", "30.0")
    policy = from_env()
    assert policy.base_delay == 3.0
    assert policy.max_delay == 30.0


def test_from_env_invalid_retries_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("CRONWRAP_MAX_RETRIES", "not-a-number")
    policy = from_env()
    assert policy is not None
    assert policy.max_retries == 3  # default


def test_from_env_exponential_can_be_disabled(monkeypatch):
    monkeypatch.setenv("CRONWRAP_MAX_RETRIES", "2")
    monkeypatch.setenv("CRONWRAP_RETRY_EXPONENTIAL", "false")
    policy = from_env()
    assert policy.exponential is False


def test_from_env_jitter_can_be_enabled(monkeypatch):
    monkeypatch.setenv("CRONWRAP_MAX_RETRIES", "2")
    monkeypatch.setenv("CRONWRAP_RETRY_JITTER", "true")
    policy = from_env()
    assert policy.jitter is True
