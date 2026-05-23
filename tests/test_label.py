"""Tests for cronwrap.label."""
import pytest
from cronwrap.label import (
    LabelConfig,
    parse_labels,
    validate_label_key,
    validate_label_value,
    merge_labels,
    labels_from_env,
)


# ---------------------------------------------------------------------------
# validate_label_key
# ---------------------------------------------------------------------------

def test_valid_key_simple():
    assert validate_label_key("env") is True


def test_valid_key_with_dots_and_dashes():
    assert validate_label_key("app.name-v2") is True


def test_invalid_key_starts_with_digit():
    assert validate_label_key("1env") is False


def test_invalid_key_empty():
    assert validate_label_key("") is False


def test_invalid_key_contains_space():
    assert validate_label_key("my key") is False


# ---------------------------------------------------------------------------
# validate_label_value
# ---------------------------------------------------------------------------

def test_valid_value_short():
    assert validate_label_value("production") is True


def test_valid_value_at_max_length():
    assert validate_label_value("x" * 256) is True


def test_invalid_value_too_long():
    assert validate_label_value("x" * 257) is False


# ---------------------------------------------------------------------------
# parse_labels
# ---------------------------------------------------------------------------

def test_parse_labels_simple():
    cfg = parse_labels("env=prod,team=sre")
    assert cfg.labels == {"env": "prod", "team": "sre"}


def test_parse_labels_strips_whitespace():
    cfg = parse_labels(" env = prod , team = sre ")
    assert cfg.labels == {"env": "prod", "team": "sre"}


def test_parse_labels_drops_malformed_token():
    cfg = parse_labels("env=prod,badtoken,team=sre")
    assert "badtoken" not in cfg.labels
    assert cfg.labels == {"env": "prod", "team": "sre"}


def test_parse_labels_drops_invalid_key():
    cfg = parse_labels("1bad=value,good=ok")
    assert "1bad" not in cfg.labels
    assert cfg.labels["good"] == "ok"


def test_parse_labels_empty_string():
    cfg = parse_labels("")
    assert cfg.is_empty()


def test_parse_labels_value_with_equals():
    # value may itself contain '='
    cfg = parse_labels("expr=a=b")
    assert cfg.labels["expr"] == "a=b"


# ---------------------------------------------------------------------------
# LabelConfig helpers
# ---------------------------------------------------------------------------

def test_label_config_is_empty_true():
    assert LabelConfig().is_empty() is True


def test_label_config_is_empty_false():
    assert LabelConfig(labels={"k": "v"}).is_empty() is False


def test_label_config_as_dict_returns_copy():
    cfg = LabelConfig(labels={"k": "v"})
    d = cfg.as_dict()
    d["k"] = "changed"
    assert cfg.labels["k"] == "v"


# ---------------------------------------------------------------------------
# merge_labels
# ---------------------------------------------------------------------------

def test_merge_labels_later_wins():
    a = LabelConfig(labels={"env": "staging", "team": "sre"})
    b = LabelConfig(labels={"env": "prod"})
    merged = merge_labels(a, b)
    assert merged.labels == {"env": "prod", "team": "sre"}


def test_merge_labels_empty_inputs():
    merged = merge_labels(LabelConfig(), LabelConfig())
    assert merged.is_empty()


# ---------------------------------------------------------------------------
# labels_from_env
# ---------------------------------------------------------------------------

def test_labels_from_env_returns_none_when_missing():
    assert labels_from_env({}) is None


def test_labels_from_env_parses_value():
    cfg = labels_from_env({"CRONWRAP_LABELS": "env=prod,team=ops"})
    assert cfg is not None
    assert cfg.labels == {"env": "prod", "team": "ops"}


def test_labels_from_env_empty_string_returns_none():
    assert labels_from_env({"CRONWRAP_LABELS": "   "}) is None
