"""Competition ranking, "1224" style (data-model §4.3)."""

from __future__ import annotations

from decimal import Decimal
from typing import Callable, Sequence, TypeVar, Union

T = TypeVar("T")


def rank_descending(
    items: Sequence[T],
    value: Callable[[T], Union[int, Decimal]],
    name: Callable[[T], str],
) -> list[tuple[int, T]]:
    """Sort by `value` descending (ties by `name`) and attach ranks.

    Equal values share a rank and the next rank skips: values 10, 8, 8, 5 give ranks 1, 2, 2, 4.
    """
    ordered = sorted(items, key=lambda item: (-value(item), name(item)))
    ranked: list[tuple[int, T]] = []
    for position, item in enumerate(ordered, start=1):
        if position > 1 and value(item) == value(ordered[position - 2]):
            rank = ranked[-1][0]
        else:
            rank = position
        ranked.append((rank, item))
    return ranked
