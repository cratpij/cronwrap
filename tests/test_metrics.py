"""Tests for cronwrap.metrics."""
import json
import pytest
from pathlib import Path

from cronwrap.metrics import (
    JobMetrics,
    _metrics_path,
    load_metrics,
    save_metrics,
    record_run,
)


@pytest.fixture
def metrics_dir(tmp_path):
    return str(tmp_path / "metrics")


def test_job_metrics_defaults():
    m = JobMetrics(job_name="backup")
    assert m.total_runs == 0
    assert m.successful_runs == 0
    assert m.failed_runs == 0
    assert m.success_rate == 0.0
    assert m.average_duration is None


def test_success_rate_calculation():
    m = JobMetrics(job_name="backup", total_runs=4, successful_runs=3)
    assert m.success_rate == pytest.approx(0.75)


def test_average_duration():
    m = JobMetrics(job_name="backup", durations=[2.0, 4.0, 6.0])
    assert m.average_duration == pytest.approx(4.0)


def test_metrics_roundtrip():
    original = JobMetrics(
        job_name="nightly",
        total_runs=5,
        successful_runs=4,
        failed_runs=1,
        total_retries=2,
        last_exit_code=0,
        last_duration_seconds=1.5,
        durations=[1.0, 1.5, 2.0, 1.2, 1.5],
    )
    restored = JobMetrics.from_dict(original.to_dict())
    assert restored == original


def test_load_metrics_returns_default_when_missing(metrics_dir):
    m = load_metrics(metrics_dir, "nonexistent")
    assert m.job_name == "nonexistent"
    assert m.total_runs == 0


def test_save_and_load_metrics(metrics_dir):
    m = JobMetrics(job_name="deploy", total_runs=3, successful_runs=3, durations=[0.5, 0.6, 0.4])
    save_metrics(metrics_dir, m)
    loaded = load_metrics(metrics_dir, "deploy")
    assert loaded == m


def test_save_creates_directory(tmp_path):
    nested_dir = str(tmp_path / "a" / "b" / "metrics")
    m = JobMetrics(job_name="job")
    save_metrics(nested_dir, m)  # should not raise
    assert Path(nested_dir).exists()


def test_record_run_success(metrics_dir):
    m = record_run(metrics_dir, "etl", exit_code=0, duration_seconds=2.3, retries_used=1)
    assert m.total_runs == 1
    assert m.successful_runs == 1
    assert m.failed_runs == 0
    assert m.total_retries == 1
    assert m.last_exit_code == 0
    assert m.last_duration_seconds == pytest.approx(2.3)


def test_record_run_failure(metrics_dir):
    m = record_run(metrics_dir, "etl", exit_code=1, duration_seconds=0.5)
    assert m.failed_runs == 1
    assert m.successful_runs == 0


def test_record_run_accumulates(metrics_dir):
    record_run(metrics_dir, "etl", exit_code=0, duration_seconds=1.0)
    record_run(metrics_dir, "etl", exit_code=0, duration_seconds=2.0)
    m = record_run(metrics_dir, "etl", exit_code=1, duration_seconds=0.5)
    assert m.total_runs == 3
    assert m.successful_runs == 2
    assert m.failed_runs == 1
    assert len(m.durations) == 3


def test_metrics_path_sanitises_separators(tmp_path):
    import os
    path = _metrics_path(str(tmp_path), f"dir{os.sep}job name")
    assert os.sep not in path.stem
    assert " " not in path.stem
