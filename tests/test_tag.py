"""Tests for cronwrap.tag and cronwrap.tag_config."""

from __future__ import annotations

import pytest

from cronwrap.tag import (
    TagConfig,
    build_tag_config,
    parse_tags,
    validate_tag,
)
from cronwrap.tag_config import from_env


# ---------------------------------------------------------------------------
# parse_tags
# ---------------------------------------------------------------------------

def test_parse_tags_simple():
    assert parse_tags("deploy,prod") == ["deploy", "prod"]


def test_parse_tags_strips_whitespace():
    assert parse_tags(" deploy , prod ") == ["deploy", "prod"]


def test_parse_tags_deduplicates():
    assert parse_tags("a,b,a") == ["a", "b"]


def test_parse_tags_sorted():
    result = parse_tags("z,a,m")
    assert result == ["a", "m", "z"]


def test_parse_tags_drops_empty_tokens():
    assert parse_tags("a,,b,") == ["a", "b"]


def test_parse_tags_empty_string():
    assert parse_tags("") == []


# ---------------------------------------------------------------------------
# validate_tag
# ---------------------------------------------------------------------------

def test_validate_tag_alphanumeric():
    assert validate_tag("deploy123") is True


def test_validate_tag_hyphen_underscore():
    assert validate_tag("my-tag_1") is True


def test_validate_tag_rejects_space():
    assert validate_tag("bad tag") is False


def test_validate_tag_rejects_dot():
    assert validate_tag("v1.0") is False


def test_validate_tag_rejects_empty():
    assert validate_tag("") is False


# ---------------------------------------------------------------------------
# build_tag_config
# ---------------------------------------------------------------------------

def test_build_tag_config_valid_tags():
    cfg = build_tag_config("prod,deploy")
    assert cfg.tags == ["deploy", "prod"]


def test_build_tag_config_filters_invalid():
    cfg = build_tag_config("good,bad tag,also-good")
    assert "bad tag" not in cfg.tags
    assert "good" in cfg.tags
    assert "also-good" in cfg.tags


def test_build_tag_config_none_returns_empty():
    cfg = build_tag_config(None)
    assert cfg.is_empty()


def test_build_tag_config_empty_string_returns_empty():
    cfg = build_tag_config("")
    assert cfg.is_empty()


# ---------------------------------------------------------------------------
# TagConfig helpers
# ---------------------------------------------------------------------------

def test_tag_config_as_csv():
    cfg = TagConfig(tags=["a", "b", "c"])
    assert cfg.as_csv() == "a,b,c"


def test_tag_config_is_empty_true():
    assert TagConfig().is_empty() is True


def test_tag_config_is_empty_false():
    assert TagConfig(tags=["x"]).is_empty() is False


# ---------------------------------------------------------------------------
# from_env
# ---------------------------------------------------------------------------

def test_from_env_reads_cronwrap_tags():
    cfg = from_env({"CRONWRAP_TAGS": "prod,deploy"})
    assert "prod" in cfg.tags
    assert "deploy" in cfg.tags


def test_from_env_missing_var_returns_empty():
    cfg = from_env({})
    assert cfg.is_empty()


def test_from_env_invalid_tags_filtered():
    cfg = from_env({"CRONWRAP_TAGS": "ok,bad tag"})
    assert cfg.tags == ["ok"]
