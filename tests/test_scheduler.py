"""Tests for cronwrap.scheduler module."""

import pytest
from datetime import datetime

from cronwrap.scheduler import (
    CronSchedule,
    parse_schedule,
    next_run,
    NAMED_SCHEDULES,
)


# ---------------------------------------------------------------------------
# parse_schedule
# ---------------------------------------------------------------------------


def test_parse_standard_expression():
    sched = parse_schedule("30 6 * * 1")
    assert sched.minute == "30"
    assert sched.hour == "6"
    assert sched.day == "*"
    assert sched.month == "*"
    assert sched.weekday == "1"


def test_parse_named_daily():
    sched = parse_schedule("@daily")
    assert sched.expression == NAMED_SCHEDULES["@daily"]
    assert sched.hour == "0"
    assert sched.minute == "0"


def test_parse_named_hourly():
    sched = parse_schedule("@hourly")
    assert sched.minute == "0"
    assert sched.hour == "*"


def test_parse_named_weekly():
    sched = parse_schedule("@weekly")
    assert sched.weekday == "0"


def test_parse_named_monthly():
    sched = parse_schedule("@monthly")
    assert sched.day == "1"


def test_parse_step_expression():
    sched = parse_schedule("*/15 * * * *")
    assert sched.minute == "*/15"


def test_parse_range_expression():
    sched = parse_schedule("0 9-17 * * 1-5")
    assert sched.hour == "9-17"
    assert sched.weekday == "1-5"


def test_parse_wrong_field_count_raises():
    with pytest.raises(ValueError, match="expected 5 fields"):
        parse_schedule("* * * *")


def test_parse_invalid_minute_raises():
    with pytest.raises(ValueError, match="minute"):
        parse_schedule("60 * * * *")


def test_parse_invalid_hour_raises():
    with pytest.raises(ValueError, match="hour"):
        parse_schedule("0 25 * * *")


def test_parse_invalid_month_raises():
    with pytest.raises(ValueError, match="month"):
        parse_schedule("0 0 * 13 *")


# ---------------------------------------------------------------------------
# next_run
# ---------------------------------------------------------------------------


_FIXED = datetime(2024, 3, 15, 10, 0)  # Friday


def test_next_run_every_minute():
    sched = parse_schedule("* * * * *")
    result = next_run(sched, after=_FIXED)
    assert result == datetime(2024, 3, 15, 10, 1)


def test_next_run_specific_time_same_day():
    sched = parse_schedule("30 14 * * *")
    result = next_run(sched, after=_FIXED)
    assert result == datetime(2024, 3, 15, 14, 30)


def test_next_run_specific_time_next_day():
    after = datetime(2024, 3, 15, 15, 0)
    sched = parse_schedule("0 10 * * *")
    result = next_run(sched, after=after)
    assert result == datetime(2024, 3, 16, 10, 0)


def test_next_run_step_minutes():
    sched = parse_schedule("*/15 * * * *")
    after = datetime(2024, 3, 15, 10, 7)
    result = next_run(sched, after=after)
    assert result.minute == 15


def test_next_run_weekday_filter():
    # _FIXED is Friday (weekday=4); next Monday is 2024-03-18
    sched = parse_schedule("0 9 * * 0")  # Sunday
    result = next_run(sched, after=_FIXED)
    assert result.weekday() == 6  # Sunday
    assert result == datetime(2024, 3, 17, 9, 0)


def test_next_run_specific_day_of_month():
    sched = parse_schedule("0 0 1 * *")
    after = datetime(2024, 3, 15, 0, 0)
    result = next_run(sched, after=after)
    assert result == datetime(2024, 4, 1, 0, 0)
