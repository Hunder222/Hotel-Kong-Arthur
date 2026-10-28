"""Shared DTO building blocks."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import PlainSerializer

# Money and rates leave the API as JSON numbers, never strings (research R10).
AmountDkk = Annotated[
    Decimal,
    PlainSerializer(lambda value: float(value), return_type=float, when_used="json"),
]

# Percentages (0-100, 2 decimals) are also JSON numbers.
Percent = AmountDkk


REPORTING_TIME_ZONE = "Europe/Copenhagen"


def with_zone(value: datetime | None) -> datetime | None:
    """MySQL returns naive timestamps in the database's time zone (Europe/Copenhagen, set by TZ)."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=ZoneInfo(REPORTING_TIME_ZONE))
    return value
