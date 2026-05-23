"""Tests for cronwrap.runner module."""

import pytest
from unittest.mock import patch, MagicMock
from cronwrap.runner import run_job, RunnerConfig, JobResult


def _make_proc(returncode: int, stdout: str = "", stderr: str = "") -> MagicMock:
    proc = MagicMock()
    proc.returncode = returncode
    proc.stdout = stdout
    proc.stderr = stderr
    return proc


class TestRunJob:
    def test_successful_command_returns_success(self):
        config = RunnerConfig(command="echo hello")
        with patch("cronwrap.runner.subprocess.run", return_value=_make_proc(0, stdout="hello\n")):
            result = run_job(config)

        assert result.success is True
        assert result.returncode == 0
        assert result.attempts == 1

    def test_failed_command_no_retries(self):
        config = RunnerConfig(command="false", retries=0)
        with patch("cronwrap.runner.subprocess.run", return_value=_make_proc(1)):
            result = run_job(config)

        assert result.success is False
        assert result.attempts == 1

    def test_retries_on_failure(self):
        config = RunnerConfig(command="false", retries=2, retry_delay=0)
        mock_proc = _make_proc(1)
        with patch("cronwrap.runner.subprocess.run", return_value=mock_proc) as mock_run:
            with patch("cronwrap.runner.time.sleep") as mock_sleep:
                result = run_job(config)

        assert result.attempts == 3
        assert mock_run.call_count == 3
        assert mock_sleep.call_count == 2

    def test_succeeds_on_second_attempt(self):
        config = RunnerConfig(command="maybe", retries=2, retry_delay=0)
        side_effects = [_make_proc(1), _make_proc(0, stdout="ok")]
        with patch("cronwrap.runner.subprocess.run", side_effect=side_effects):
            with patch("cronwrap.runner.time.sleep"):
                result = run_job(config)

        assert result.success is True
        assert result.attempts == 2

    def test_timeout_handled_gracefully(self):
        import subprocess
        config = RunnerConfig(command="sleep 100", retries=0, timeout=0.001)
        with patch(
            "cronwrap.runner.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="sleep 100", timeout=0.001),
        ):
            result = run_job(config)

        assert result.success is False
        assert result.returncode == -1
        assert "TimeoutExpired" in result.stderr

    def test_result_contains_stdout_and_stderr(self):
        config = RunnerConfig(command="echo test")
        with patch(
            "cronwrap.runner.subprocess.run",
            return_value=_make_proc(0, stdout="output\n", stderr="warn\n"),
        ):
            result = run_job(config)

        assert result.stdout == "output\n"
        assert result.stderr == "warn\n"

    def test_elapsed_time_is_positive(self):
        config = RunnerConfig(command="true")
        with patch("cronwrap.runner.subprocess.run", return_value=_make_proc(0)):
            result = run_job(config)

        assert result.elapsed >= 0
