"""Tests for cronwrap.heartbeat and cronwrap.heartbeat_config."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cronwrap.heartbeat import (
    HeartbeatConfig,
    build_url,
    is_enabled,
    send_heartbeat,
)
from cronwrap.heartbeat_config import from_env


# ---------------------------------------------------------------------------
# is_enabled
# ---------------------------------------------------------------------------

def test_is_enabled_false_when_no_url():
    assert is_enabled(HeartbeatConfig()) is False


def test_is_enabled_false_when_blank_url():
    assert is_enabled(HeartbeatConfig(url="   ")) is False


def test_is_enabled_true_when_url_set():
    assert is_enabled(HeartbeatConfig(url="https://hc-ping.example.com/abc")) is True


# ---------------------------------------------------------------------------
# build_url
# ---------------------------------------------------------------------------

def test_build_url_success_returns_base():
    cfg = HeartbeatConfig(url="https://example.com/ping/abc", ping_on_failure=True)
    assert build_url(cfg, success=True) == "https://example.com/ping/abc"


def test_build_url_failure_with_ping_on_failure_appends_suffix():
    cfg = HeartbeatConfig(url="https://example.com/ping/abc", ping_on_failure=True)
    assert build_url(cfg, success=False) == "https://example.com/ping/abc/fail"


def test_build_url_failure_without_ping_on_failure_returns_base():
    cfg = HeartbeatConfig(url="https://example.com/ping/abc", ping_on_failure=False)
    assert build_url(cfg, success=False) == "https://example.com/ping/abc"


def test_build_url_strips_trailing_slash():
    cfg = HeartbeatConfig(url="https://example.com/ping/abc/", ping_on_failure=True)
    assert build_url(cfg, success=False) == "https://example.com/ping/abc/fail"


# ---------------------------------------------------------------------------
# send_heartbeat
# ---------------------------------------------------------------------------

def _mock_response(status: int) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_send_heartbeat_returns_false_when_disabled():
    cfg = HeartbeatConfig()
    assert send_heartbeat(cfg, success=True) is False


def test_send_heartbeat_returns_false_on_failure_when_not_configured():
    cfg = HeartbeatConfig(url="https://example.com/ping/abc", ping_on_failure=False)
    assert send_heartbeat(cfg, success=False) is False


def test_send_heartbeat_returns_true_on_200():
    cfg = HeartbeatConfig(url="https://example.com/ping/abc")
    with patch("cronwrap.heartbeat.urllib.request.urlopen", return_value=_mock_response(200)):
        assert send_heartbeat(cfg, success=True) is True


def test_send_heartbeat_returns_false_on_500():
    cfg = HeartbeatConfig(url="https://example.com/ping/abc")
    with patch("cronwrap.heartbeat.urllib.request.urlopen", return_value=_mock_response(500)):
        assert send_heartbeat(cfg, success=True) is False


def test_send_heartbeat_swallows_network_error():
    import urllib.error
    cfg = HeartbeatConfig(url="https://example.com/ping/abc")
    with patch("cronwrap.heartbeat.urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        assert send_heartbeat(cfg, success=True) is False


# ---------------------------------------------------------------------------
# from_env
# ---------------------------------------------------------------------------

def test_returns_none_when_no_url():
    assert from_env({}) is None


def test_returns_config_when_url_set():
    cfg = from_env({"CRONWRAP_HEARTBEAT_URL": "https://example.com/ping/abc"})
    assert cfg is not None
    assert cfg.url == "https://example.com/ping/abc"


def test_custom_timeout():
    cfg = from_env({"CRONWRAP_HEARTBEAT_URL": "https://x.com/p", "CRONWRAP_HEARTBEAT_TIMEOUT": "30"})
    assert cfg.timeout == 30


def test_invalid_timeout_falls_back_to_default():
    cfg = from_env({"CRONWRAP_HEARTBEAT_URL": "https://x.com/p", "CRONWRAP_HEARTBEAT_TIMEOUT": "bad"})
    assert cfg.timeout == 10


def test_ping_on_failure_enabled():
    cfg = from_env({"CRONWRAP_HEARTBEAT_URL": "https://x.com/p", "CRONWRAP_HEARTBEAT_ON_FAILURE": "true"})
    assert cfg.ping_on_failure is True


def test_custom_failure_suffix():
    cfg = from_env({"CRONWRAP_HEARTBEAT_URL": "https://x.com/p", "CRONWRAP_HEARTBEAT_FAIL_SUFFIX": "/down"})
    assert cfg.failure_suffix == "/down"
