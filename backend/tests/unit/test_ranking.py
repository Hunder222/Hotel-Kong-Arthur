import pytest

from hotel_api.business.rules.ranking import competition_ranks

pytestmark = pytest.mark.unit


def rank(pairs):
    return competition_ranks(pairs, key=lambda p: p[1], tie_key=lambda p: p[0])


def test_highest_value_gets_rank_one():
    assert rank([("a", 3), ("b", 10), ("c", 7)]) == [(1, ("b", 10)), (2, ("c", 7)), (3, ("a", 3))]


def test_equal_values_share_a_rank_and_the_next_rank_is_skipped():
    ranked = rank([("a", 10), ("b", 7), ("c", 7), ("d", 3)])
    assert [r for r, _ in ranked] == [1, 2, 2, 4]


def test_ties_are_ordered_alphabetically_by_the_tie_key():
    ranked = rank([("zebra", 5), ("apple", 5), ("mango", 5)])
    assert [(r, name) for r, (name, _) in ranked] == [(1, "apple"), (1, "mango"), (1, "zebra")]


def test_empty_input_gives_no_ranks():
    assert rank([]) == []
