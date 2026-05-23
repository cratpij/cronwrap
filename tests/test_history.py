"""Tests for cronwrap.history module."""

from datetime import datetime
from pathlib import Path

import pytest

from cronwrap.history import (
    RunRecord,
    append_record,
    last_record,
    load_records,
    make_record,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _record(**kwargs) -> RunRecord:
    defaults = dict(
        job_name="backup",
        command="/usr/bin/backup.sh",
        started_at="2024-03-15T10:00:00",
        finished_at="2024-03-15T10:01:00",
        exit_code=0,
        attempts=1,
        stdout="done",
        stderr="",
    )
    defaults.update(kwargs)
    return RunRecord(**defaults)


# ---------------------------------------------------------------------------
# RunRecord
# ---------------------------------------------------------------------------


def test_record_succeeded_true_on_zero_exit():
    assert _record(exit_code=0).succeeded is True


def test_record_succeeded_false_on_nonzero_exit():
    assert _record(exit_code=1).succeeded is False


def test_record_to_json_roundtrip():
    rec = _record()
    import json
    data = json.loads(rec.to_json())
    assert data["job_name"] == "backup"
    assert data["exit_code"] == 0


def test_record_from_dict_roundtrip():
    rec = _record(stderr="oops")
    restored = RunRecord.from_dict(
        dict(
            job_name=rec.job_name,
            command=rec.command,
            started_at=rec.started_at,
            finished_at=rec.finished_at,
            exit_code=rec.exit_code,
            attempts=rec.attempts,
            stdout=rec.stdout,
            stderr=rec.stderr,
        )
    )
    assert restored == rec


# ---------------------------------------------------------------------------
# make_record
# ---------------------------------------------------------------------------


def test_make_record_converts_datetimes():
    rec = make_record(
        job_name="test",
        command="echo hi",
        started_at=datetime(2024, 1, 1, 12, 0),
        finished_at=datetime(2024, 1, 1, 12, 1),
        exit_code=0,
        attempts=1,
    )
    assert rec.started_at == "2024-01-01T12:00:00"
    assert rec.finished_at == "2024-01-01T12:01:00"


# ---------------------------------------------------------------------------
# append_record / load_records
# ---------------------------------------------------------------------------


def test_append_and_load(tmp_path):
    hf = tmp_path / "history.jsonl"
    rec = _record()
    append_record(rec, history_file=hf)
    records = load_records(history_file=hf)
    assert len(records) == 1
    assert records[0] == rec


def test_load_returns_empty_list_when_file_missing(tmp_path):
    assert load_records(history_file=tmp_path / "no.jsonl") == []


def test_load_filters_by_job_name(tmp_path):
    hf = tmp_path / "history.jsonl"
    append_record(_record(job_name="alpha"), history_file=hf)
    append_record(_record(job_name="beta"), history_file=hf)
    append_record(_record(job_name="alpha"), history_file=hf)
    result = load_records(history_file=hf, job_name="alpha")
    assert len(result) == 2
    assert all(r.job_name == "alpha" for r in result)


def test_load_respects_limit(tmp_path):
    hf = tmp_path / "history.jsonl"
    for i in range(5):
        append_record(_record(exit_code=i), history_file=hf)
    result = load_records(history_file=hf, limit=3)
    assert len(result) == 3
    assert result[-1].exit_code == 4  # last entry


def test_load_skips_malformed_lines(tmp_path):
    hf = tmp_path / "history.jsonl"
    hf.write_text('{"bad": true}\n{not json}\n')
    result = load_records(history_file=hf)
    assert result == []


def test_append_creates_parent_dirs(tmp_path):
    hf = tmp_path / "a" / "b" / "history.jsonl"
    append_record(_record(), history_file=hf)
    assert hf.exists()


# ---------------------------------------------------------------------------
# last_record
# ---------------------------------------------------------------------------


def test_last_record_returns_most_recent(tmp_path):
    hf = tmp_path / "history.jsonl"
    append_record(_record(exit_code=0), history_file=hf)
    append_record(_record(exit_code=2), history_file=hf)
    rec = last_record("backup", history_file=hf)
    assert rec is not None
    assert rec.exit_code == 2


def test_last_record_returns_none_when_no_match(tmp_path):
    hf = tmp_path / "history.jsonl"
    append_record(_record(job_name="other"), history_file=hf)
    assert last_record("backup", history_file=hf) is None
