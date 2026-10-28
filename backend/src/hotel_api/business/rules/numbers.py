"""Rounding and ratio rules (research R10): half-up to 2 decimals, zero-safe division, shares = 100."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from typing import Sequence, Union

Number = Union[int, Decimal]

_CENT = Decimal("0.01")


def round_half_up(value: Number, places: int = 2) -> Decimal:
    return Decimal(value).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def safe_ratio(numerator: Number, denominator: Number) -> Decimal:
    """numerator / denominator, or 0 when the denominator is 0 (spec edge case). Not rounded."""
    if denominator == 0:
        return Decimal(0)
    return Decimal(numerator) / Decimal(denominator)


def safe_average(total: Number, count: Number) -> Decimal:
    """Average rounded half-up to 2 decimals; 0.00 for an empty set."""
    return round_half_up(safe_ratio(total, count))


def safe_pct(part: Number, whole: Number) -> Decimal:
    """part / whole x 100, rounded half-up to 2 decimals; 0.00 when whole is 0."""
    return round_half_up(safe_ratio(part, whole) * 100)


def shares_pct(values: Sequence[Number]) -> list[Decimal]:
    """Percent shares of one breakdown, 2 decimals, summing to exactly 100.00 (largest remainder).

    Ties in the remainder go to the earlier item. All zeros give all 0.00.
    """
    if any(v < 0 for v in values):
        raise ValueError("shares are only defined for non-negative values")
    total = sum((Fraction(v) for v in values), Fraction(0))
    if total == 0:
        return [Decimal("0.00") for _ in values]
    raw = [Fraction(v) * 10000 / total for v in values]  # hundredths of a percent, exact
    floors = [r.numerator // r.denominator for r in raw]
    missing = 10000 - sum(floors)
    by_remainder = sorted(range(len(values)), key=lambda i: (-(raw[i] - floors[i]), i))
    for i in by_remainder[:missing]:
        floors[i] += 1
    return [Decimal(f) * _CENT for f in floors]
