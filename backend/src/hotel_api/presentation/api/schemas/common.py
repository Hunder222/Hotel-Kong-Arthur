"""Shared DTO building blocks."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer

# Money and rates leave the API as JSON numbers, never strings (research R10).
AmountDkk = Annotated[
    Decimal,
    PlainSerializer(lambda value: float(value), return_type=float, when_used="json"),
]

# Percentages (0-100, 2 decimals) are also JSON numbers.
Percent = AmountDkk
