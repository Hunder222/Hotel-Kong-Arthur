"""Strict parsing of raw (JSON-like) values shared by the validation rules. Internal helpers."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

MIN_DATE = date(2000, 1, 1)
MAX_DATE = date(2100, 12, 31)
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def clean_text(value: Any, max_length: int = 100) -> str | None:
    """Trimmed text of 1..max_length characters, else None."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text if 1 <= len(text) <= max_length else None


def whole_number(value: Any) -> int | None:
    """An integer value (ints, or floats/Decimals without a fraction). Booleans and text are rejected."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, Decimal) and value.is_finite() and value == value.to_integral_value():
        return int(value)
    return None


def iso_date(value: Any) -> date | None:
    """A real calendar date, YYYY-MM-DD only, within 2000-01-01..2100-12-31."""
    parsed: date | None = None
    if isinstance(value, datetime):
        return None
    if isinstance(value, date):
        parsed = value
    elif isinstance(value, str) and _ISO_DATE.fullmatch(value):
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            return None
    if parsed is None or not (MIN_DATE <= parsed <= MAX_DATE):
        return None
    return parsed


def money(value: Any) -> Decimal | None:
    """A positive amount with at most 2 decimals, as Decimal. Text and booleans are rejected."""
    if isinstance(value, bool):
        return None
    try:
        if isinstance(value, (int, Decimal)):
            amount = Decimal(value)
        elif isinstance(value, float):
            amount = Decimal(str(value))
        else:
            return None
    except InvalidOperation:
        return None
    if not amount.is_finite() or amount <= 0:
        return None
    cents = amount.quantize(Decimal("0.01"))
    return cents if cents == amount else None
