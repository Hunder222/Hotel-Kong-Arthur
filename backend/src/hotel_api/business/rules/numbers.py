"""Number rules (research R10): half-up rounding to 2 decimals, safe ratios and share rounding."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Sequence, Union

Number = Union[int, Decimal]


def round_half_up(value: Number, places: int = 2) -> Decimal:
    return Decimal(value).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)



def safe_ratio(numerator: Number, denominator: Number, scale: int = 1) -> Decimal:
    """`numerator / denominator * scale` rounded half-up to 2 decimals; `0.00` when the denominator is 0."""
    if denominator == 0:
        return Decimal("0.00")
    return round_half_up(Decimal(numerator) * scale / Decimal(denominator))


def largest_remainder_shares(values: Sequence[Number]) -> list[Decimal]:
    """Percentage shares with 2 decimals that sum to exactly `100.00` (all `0.00` when the total is 0).

    Each share is floored to a hundredth of a percent, then the leftover hundredths go to the entries
    with the largest remainders (ties: the earlier entry first).
    """
    total = sum(Decimal(v) for v in values)
    if total == 0:
        return [Decimal("0.00") for _ in values]
    exact = [Decimal(v) * 10000 / total for v in values]  # in hundredths of a percent
    floors = [int(x) for x in exact]
    leftover = 10000 - sum(floors)
    by_remainder = sorted(range(len(values)), key=lambda i: (-(exact[i] - floors[i]), i))
    for i in by_remainder[:leftover]:
        floors[i] += 1
    return [Decimal(f) / 100 for f in floors]
