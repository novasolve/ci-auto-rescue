from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Union

Scalar = Union[float, int, str, datetime]

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def to_datetime(value: Scalar) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (float, int)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return now_utc()
    return now_utc()

def delta_between(a: Scalar, b: Scalar) -> timedelta:
    """Return a timezone-aware timedelta as to_datetime(a) - to_datetime(b)."""
    return to_datetime(a) - to_datetime(b)

def seconds_between(a: Scalar, b: Scalar) -> float:
    return delta_between(a, b).total_seconds()
