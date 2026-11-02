"""Competition ranking ("1224", data-model §4.3): equal values share a rank and the next rank is skipped."""

from __future__ import annotations

from typing import Any, Callable, Sequence, TypeVar

T = TypeVar("T")


def competition_ranks(
    items: Sequence[T],
    key: Callable[[T], Any],
    tie_key: Callable[[T], Any],
) -> list[tuple[int, T]]:
    """Rank `items` by `key` descending; ties share a rank and are listed in `tie_key` order.

    Returns `(rank, item)` pairs in rank order, e.g. values 10, 7, 7, 3 get ranks 1, 2, 2, 4.
    """
    ordered = sorted(items, key=tie_key)
    ordered = sorted(ordered, key=key, reverse=True)  # stable: ties keep their tie_key order
    ranked: list[tuple[int, T]] = []
    for position, item in enumerate(ordered, start=1):
        if ranked and key(ranked[-1][1]) == key(item):
            ranked.append((ranked[-1][0], item))
        else:
            ranked.append((position, item))
    return ranked
