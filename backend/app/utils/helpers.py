"""
Utility helpers shared across services.
"""
from datetime import date, datetime, timezone
from typing import Optional


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


def days_between(d1: date, d2: date) -> int:
    return (d2 - d1).days


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator
