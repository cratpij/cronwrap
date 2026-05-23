"""Tests for cronwrap.webhook."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from cronwrap.webhook import WebhookConfig, build_payload, send_webhook


@pytest.fixture()
def cfg() -> WebhookConfig:
    return WebhookConfig(url="https://example.com/hook", job_name="backup")


def test_build_payload_failure(cfg):
    payload = build_payload(cfg, exit_code=1, stdout="out", stderr="err")
    assert payload["job"] == "backup"
    assert payload["exit_code"] == 1
    assert payload["status"] == "failure"
    assert payload["stdout"] == "out"
    assert payload["stderr"] == "err"


def test_build_payload_success(cfg):
    payload = build_payload(cfg, exit_code=0, stdout="", stderr="")
    assert payload["status"] == "success"


def _mock_response(status: int):
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_send_webhook_returns_true_on_200(cfg):
    with patch("urllib.request.urlopen", return_value=_mock_response(200)):
        result = send_webhook(cfg, exit_code=1, stdout="", stderr="")
    assert result is True


def test_send_webhook_returns_false_on_500(cfg):
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
        cfg.url, 500, "Server Error", {}, None
    )):
        result = send_webhook(cfg, exit_code=1, stdout="", stderr="")
    assert result is False


def test_send_webhook_includes_extra_headers(cfg):
    cfg.extra_headers = {"Authorization": "Bearer tok"}
    captured = {}

    def fake_urlopen(req, timeout):
        captured["headers"] = dict(req.headers)
        return _mock_response(204)

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        send_webhook(cfg, exit_code=0, stdout="", stderr="")

    assert "Authorization" in captured["headers"]


def test_send_webhook_posts_json(cfg):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["data"] = json.loads(req.data.decode())
        return _mock_response(200)

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        send_webhook(cfg, exit_code=2, stdout="hello", stderr="world")

    assert captured["data"]["exit_code"] == 2
    assert captured["data"]["stdout"] == "hello"
