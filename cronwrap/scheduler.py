"""Cron schedule parsing and next-run calculation utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


CRON_FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day": (1, 31),
    "month": (1, 12),
    "weekday": (0, 6),
}

NAMED_SCHEDULES = {
    "@hourly": "0 * * * *",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@weekly": "0 0 * * 0",
    "@monthly": "0 0 1 * *",
}


@dataclass
class CronSchedule:
    """Parsed representation of a cron expression."""

    expression: str
    minute: str
    hour: str
    day: str
    month: str
    weekday: str

    def __str__(self) -> str:  # pragma: no cover
        return self.expression


def parse_schedule(expression: str) -> CronSchedule:
    """Parse a cron expression string into a CronSchedule.

    Supports standard 5-field expressions and named shortcuts.

    Raises ValueError for invalid expressions.
    """
    expr = expression.strip()
    expr = NAMED_SCHEDULES.get(expr, expr)

    parts = expr.split()
    if len(parts) != 5:
        raise ValueError(
            f"Invalid cron expression {expression!r}: expected 5 fields, got {len(parts)}"
        )

    minute, hour, day, month, weekday = parts
    _validate_fields(minute, hour, day, month, weekday)

    return CronSchedule(
        expression=expr,
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        weekday=weekday,
    )


def _validate_fields(
    minute: str, hour: str, day: str, month: str, weekday: str
) -> None:
    fields = zip(
        ["minute", "hour", "day", "month", "weekday"],
        [minute, hour, day, month, weekday],
    )
    for name, value in fields:
        lo, hi = CRON_FIELD_RANGES[name]
        if not _is_valid_field(value, lo, hi):
            raise ValueError(
                f"Invalid cron field {name}={value!r} (allowed range {lo}-{hi})"
            )


def _is_valid_field(value: str, lo: int, hi: int) -> bool:
    """Return True if *value* is a syntactically valid cron field."""
    if value == "*":
        return True
    # */step
    if re.fullmatch(r"\*/\d+", value):
        step = int(value[2:])
        return step >= 1
    # range or single number
    if re.fullmatch(r"\d+(-\d+)?(,\d+(-\d+)?)*", value):
        numbers = re.findall(r"\d+", value)
        return all(lo <= int(n) <= hi for n in numbers)
    return False


def next_run(schedule: CronSchedule, after: Optional[datetime] = None) -> datetime:
    """Return the next datetime at which *schedule* would fire.

    Searches up to one year ahead; raises RuntimeError if no match found.
    """
    now = (after or datetime.now()).replace(second=0, microsecond=0)
    candidate = now + timedelta(minutes=1)
    deadline = now + timedelta(days=366)

    while candidate < deadline:
        if (
            _field_matches(schedule.month, candidate.month, 1, 12)
            and _field_matches(schedule.day, candidate.day, 1, 31)
            and _field_matches(schedule.weekday, candidate.weekday(), 0, 6)
            and _field_matches(schedule.hour, candidate.hour, 0, 23)
            and _field_matches(schedule.minute, candidate.minute, 0, 59)
        ):
            return candidate
        candidate += timedelta(minutes=1)

    raise RuntimeError(f"No next run found for schedule {schedule.expression!r} within one year")


def _field_matches(field: str, value: int, lo: int, hi: int) -> bool:
    if field == "*":
        return True
    if re.fullmatch(r"\*/\d+", field):
        step = int(field[2:])
        return (value - lo) % step == 0
    for part in field.split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            if int(a) <= value <= int(b):
                return True
        elif int(part) == value:
            return True
    return False
