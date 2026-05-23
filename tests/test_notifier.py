"""Tests for cronwrap.notifier."""

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from cronwrap.notifier import (
    NotifierConfig,
    build_email_body,
    send_failure_email,
)


# ---------------------------------------------------------------------------
# build_email_body
# ---------------------------------------------------------------------------

def test_build_email_body_contains_job_name():
    body = build_email_body("backup", "tar -czf /tmp/b.tgz /data", 1, "", "", 3)
    assert "backup" in body
    assert "3 attempt" in body
    assert "exit code" in body.lower()


def test_build_email_body_includes_stdout_and_stderr():
    body = build_email_body("myjob", "cmd", 2, "some output", "some error", 1)
    assert "some output" in body
    assert "some error" in body


def test_build_email_body_omits_empty_streams():
    body = build_email_body("myjob", "cmd", 1, "", "", 1)
    assert "--- stdout ---" not in body
    assert "--- stderr ---" not in body


# ---------------------------------------------------------------------------
# send_failure_email
# ---------------------------------------------------------------------------

def _default_config(**kwargs):
    base = dict(
        smtp_host="smtp.example.com",
        smtp_port=25,
        from_address="alerts@example.com",
        to_addresses=["ops@example.com"],
    )
    base.update(kwargs)
    return NotifierConfig(**base)


@patch("cronwrap.notifier.smtplib.SMTP")
def test_send_failure_email_success(mock_smtp_cls):
    mock_server = MagicMock()
    mock_smtp_cls.return_value = mock_server

    result = send_failure_email(
        _default_config(), "backup", "tar -czf /tmp/b.tgz /data",
        1, "stdout text", "stderr text", 2,
    )

    assert result is True
    mock_server.sendmail.assert_called_once()
    mock_server.quit.assert_called_once()


@patch("cronwrap.notifier.smtplib.SMTP")
def test_send_failure_email_uses_tls(mock_smtp_cls):
    mock_server = MagicMock()
    mock_smtp_cls.return_value = mock_server
    cfg = _default_config(use_tls=True)

    send_failure_email(cfg, "job", "cmd", 1, "", "", 1)

    mock_server.starttls.assert_called_once()


@patch("cronwrap.notifier.smtplib.SMTP")
def test_send_failure_email_smtp_error_returns_false(mock_smtp_cls):
    mock_smtp_cls.side_effect = smtplib.SMTPException("connection refused")

    result = send_failure_email(
        _default_config(), "job", "cmd", 1, "", "", 1
    )

    assert result is False


def test_send_failure_email_no_recipients_returns_false():
    cfg = _default_config(to_addresses=[])
    result = send_failure_email(cfg, "job", "cmd", 1, "", "", 1)
    assert result is False
