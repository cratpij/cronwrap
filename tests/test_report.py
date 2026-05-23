"""Tests for cronwrap.report."""
import pytest
from cronwrap.metrics import JobMetrics, save_metrics
from cronwrap.report import list_tracked_jobs, format_metrics, build_report


@pytest.fixture
def metrics_dir(tmp_path):
    return str(tmp_path / "metrics")


def _store(metrics_dir, **kwargs):
    m = JobMetrics(**kwargs)
    save_metrics(metrics_dir, m)
    return m


def test_list_tracked_jobs_empty(metrics_dir):
    assert list_tracked_jobs(metrics_dir) == []


def test_list_tracked_jobs_missing_dir(tmp_path):
    assert list_tracked_jobs(str(tmp_path / "ghost")) == []


def test_list_tracked_jobs_returns_names(metrics_dir):
    _store(metrics_dir, job_name="alpha")
    _store(metrics_dir, job_name="beta")
    jobs = list_tracked_jobs(metrics_dir)
    assert "alpha" in jobs
    assert "beta" in jobs


def test_format_metrics_contains_job_name():
    m = JobMetrics(job_name="nightly-backup", total_runs=10, successful_runs=9, failed_runs=1)
    text = format_metrics(m)
    assert "nightly-backup" in text


def test_format_metrics_shows_success_rate():
    m = JobMetrics(job_name="job", total_runs=4, successful_runs=3, failed_runs=1)
    text = format_metrics(m)
    assert "75.0%" in text


def test_format_metrics_omits_duration_when_none():
    m = JobMetrics(job_name="job")
    text = format_metrics(m)
    assert "duration" not in text.lower()


def test_format_metrics_includes_duration_when_present():
    m = JobMetrics(job_name="job", durations=[1.5, 2.5], last_duration_seconds=2.5)
    text = format_metrics(m)
    assert "2.00s" in text  # average
    assert "2.50s" in text  # last


def test_build_report_no_data(metrics_dir):
    report = build_report(metrics_dir)
    assert "No metrics" in report


def test_build_report_contains_all_jobs(metrics_dir):
    _store(metrics_dir, job_name="job-a", total_runs=2, successful_runs=2)
    _store(metrics_dir, job_name="job-b", total_runs=1, failed_runs=1)
    report = build_report(metrics_dir)
    assert "job-a" in report
    assert "job-b" in report


def test_build_report_separator_present(metrics_dir):
    _store(metrics_dir, job_name="x")
    _store(metrics_dir, job_name="y")
    report = build_report(metrics_dir)
    assert "---" in report
