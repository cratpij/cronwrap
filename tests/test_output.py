"""Tests for cronwrap.output."""

import pytest

from cronwrap.output import (
    CapturedOutput,
    OutputConfig,
    capture_output,
    format_output,
    truncate,
    DEFAULT_MAX_BYTES,
)


# ---------------------------------------------------------------------------
# truncate
# ---------------------------------------------------------------------------

def test_truncate_short_string_unchanged():
    assert truncate("hello", 100) == "hello"


def test_truncate_exact_boundary_unchanged():
    text = "a" * 10
    assert truncate(text, 10) == text


def test_truncate_long_string_appends_notice():
    text = "x" * 200
    result = truncate(text, 100)
    assert result.endswith("... [output truncated]")
    assert len(result.encode("utf-8")) > 100  # notice adds a few bytes, that's fine
    assert result.startswith("x" * 100)


def test_truncate_zero_max_returns_empty():
    assert truncate("anything", 0) == ""


def test_truncate_multibyte_chars_safe():
    # Each emoji is 4 bytes; 3 emojis = 12 bytes
    text = "\U0001F600" * 3
    result = truncate(text, 5)  # not enough for even one emoji
    assert "[output truncated]" in result


# ---------------------------------------------------------------------------
# capture_output
# ---------------------------------------------------------------------------

def test_capture_output_basic():
    cfg = OutputConfig()
    out = capture_output("hello stdout", "hello stderr", cfg)
    assert out.stdout == "hello stdout"
    assert out.stderr == "hello stderr"


def test_capture_output_excludes_stdout():
    cfg = OutputConfig(include_stdout=False)
    out = capture_output("ignored", "kept", cfg)
    assert out.stdout == ""
    assert out.stderr == "kept"


def test_capture_output_excludes_stderr():
    cfg = OutputConfig(include_stderr=False)
    out = capture_output("kept", "ignored", cfg)
    assert out.stdout == "kept"
    assert out.stderr == ""


def test_capture_output_none_inputs():
    cfg = OutputConfig()
    out = capture_output(None, None, cfg)
    assert out.stdout == ""
    assert out.stderr == ""


def test_capture_output_truncates_when_over_limit():
    cfg = OutputConfig(max_bytes=10)
    long_text = "a" * 100
    out = capture_output(long_text, "", cfg)
    assert "[output truncated]" in out.stdout


# ---------------------------------------------------------------------------
# CapturedOutput.is_empty
# ---------------------------------------------------------------------------

def test_is_empty_true_when_blank():
    assert CapturedOutput(stdout="  ", stderr="\n").is_empty()


def test_is_empty_false_when_has_content():
    assert not CapturedOutput(stdout="data", stderr="").is_empty()


# ---------------------------------------------------------------------------
# format_output
# ---------------------------------------------------------------------------

def test_format_output_both_streams():
    out = CapturedOutput(stdout="out line", stderr="err line")
    result = format_output(out)
    assert "--- stdout ---" in result
    assert "out line" in result
    assert "--- stderr ---" in result
    assert "err line" in result


def test_format_output_only_stdout():
    out = CapturedOutput(stdout="only this", stderr="")
    result = format_output(out)
    assert "stdout" in result
    assert "stderr" not in result


def test_format_output_empty_returns_placeholder():
    out = CapturedOutput(stdout="", stderr="")
    assert format_output(out) == "(no output)"
