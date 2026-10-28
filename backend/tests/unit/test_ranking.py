import pytest

from hotel_api.business.rules.ranking import rank_descending

pytestmark = pytest.mark.unit


def ranked(rows):
    return [(rank, name) for rank, (name, _) in rank_descending(rows, lambda r: r[1], lambda r: r[0])]


def test_orders_by_value_descending():
    assert ranked([("a", 1), ("b", 3), ("c", 2)]) == [(1, "b"), (2, "c"), (3, "a")]


def test_ties_share_a_rank_and_the_next_rank_skips():
    assert ranked([("a", 10), ("b", 8), ("c", 8), ("d", 5)]) == [(1, "a"), (2, "b"), (2, "c"), (4, "d")]


def test_ties_are_listed_by_name():
    assert ranked([("zed", 7), ("alpha", 7), ("mid", 7)]) == [(1, "alpha"), (1, "mid"), (1, "zed")]


def test_empty_input():
    assert ranked([]) == []
