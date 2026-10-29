"""Decimal rounding rule (research R10): half-up to 2 decimals for currency amounts."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Union

Number = Union[int, Decimal]


def round_half_up(value: Number, places: int = 2) -> Decimal:
    return Decimal(value).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)

