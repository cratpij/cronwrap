"""Tests for the cronwrap CLI entry point."""

from unittest.mock import MagicMock, patch

import pytest

from cronwrap.cli import build_parser, main
from cronwrap.runner import JobResult


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

def test_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["--", "echo", "hi"])
    assert args.retries == 0
    assert args.retry_delay == 0.0
    assert args.timeout is None
    assert args.notify_email is None
    assert args.smtp_host == "localhost"
    assert args.smtp_port == 25
    assert args.from_email == "cronwrap@localhost"


def test_parser_custom_values():
    parser = build_parser()
    args = parser.parse_args([
        "--retries", "3",
        "--retry-delay", "1.5",
        "--timeout", "60",
        "--job-name", "my-job",
        "--notify-email", "ops@example.com",
        "--smtp-host", "mail.example.com",
        "--smtp-port", "587",
        "--from-email", "cron@example.com",
        "--", "python", "script.py",
    ])
    assert args.retries == 3
    assert args.retry_delay == 1.5
    assert args.timeout == 60.0
    assert args.job_name == "my-job"
    assert args.notify_email == "ops@example.com"
    assert args.smtp_host == "mail.example.com"
    assert args.smtp_port == 587
    assert args.from_email == "cron@example.com"


# ---------------------------------------------------------------------------
# main() integration tests
# ---------------------------------------------------------------------------

_SUCCESS = JobResult(success=True, returncode=0, stdout="ok", stderr="", attempts=1)
_FAILURE = JobResult(success=False, returncode=1, stdout="", stderr="boom", attempts=1)


@patch("cronwrap.cli.run_job", return_value=_SUCCESS)
def test_main_returns_0_on_success(mock_run):
    rc = main(["--", "echo", "hello"])
    assert rc == 0
    mock_run.assert_called_once()


@patch("cronwrap.cli.run_job", return_value=_FAILURE)
def test_main_returns_1_on_failure(mock_run):
    rc = main(["--", "false"])
    assert rc == 1


@patch("cronwrap.cli.send_failure_email")
@patch("cronwrap.cli.run_job", return_value=_FAILURE)
def test_main_sends_email_on_failure(mock_run, mock_notify):
    rc = main([
        "--notify-email", "ops@example.com",
        "--", "false",
    ])
    assert rc == 1
    mock_notify.assert_called_once()
    notifier_cfg, result = mock_notify.call_args.args
    assert notifier_cfg.to_email == "ops@example.com"
    assert result is _FAILURE


@patch("cronwrap.cli.send_failure_email")
@patch("cronwrap.cli.run_job", return_value=_SUCCESS)
def test_main_does_not_send_email_on_success(mock_run, mock_notify):
    main(["--notify-email", "ops@example.com", "--", "true"])
    mock_notify.assert_not_called()


@patch("cronwrap.cli.send_failure_email")
@patch("cronwrap.cli.run_job", return_value=_FAILURE)
def test_main_does_not_send_email_without_address(mock_run, mock_notify):
    main(["--", "false"])
    mock_notify.assert_not_called()


@patch("cronwrap.cli.run_job", return_value=_SUCCESS)
def test_main_passes_runner_config(mock_run):
    main(["--retries", "2", "--retry-delay", "0.5", "--timeout", "30", "--", "sleep", "1"])
    cfg = mock_run.call_args.args[0]
    assert cfg.retries == 2
    assert cfg.retry_delay == 0.5
    assert cfg.timeout == 30.0
    assert cfg.command == ["sleep", "1"]
