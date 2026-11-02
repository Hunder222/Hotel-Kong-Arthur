from decimal import Decimal

import pytest

from hotel_api.business.rules.numbers import largest_remainder_shares, round_half_up, safe_ratio

pytestmark = pytest.mark.unit


def test_round_half_up_rounds_ties_away_from_zero():
    assert round_half_up(Decimal("2.345")) == Decimal("2.35")
    assert round_half_up(Decimal("2.344")) == Decimal("2.34")
    assert round_half_up(Decimal("0.005")) == Decimal("0.01")
    assert round_half_up(5) == Decimal("5.00")



def test_safe_ratio_scales_rounds_and_returns_zero_for_a_zero_denominator():
    assert safe_ratio(5379, 78110, 100) == Decimal("6.89")
    assert safe_ratio(11234034, 1000) == Decimal("11234.03")
    assert safe_ratio(5, 0, 100) == Decimal("0.00")
    assert safe_ratio(0, 0) == Decimal("0.00")


def test_largest_remainder_shares_sum_to_exactly_100():
    shares = largest_remainder_shares([1, 1, 1])
    assert shares == [Decimal("33.34"), Decimal("33.33"), Decimal("33.33")]
    assert sum(shares) == Decimal("100.00")
    assert largest_remainder_shares([Decimal("2119671.00"), Decimal("9114363.00")])[0] == Decimal("18.87")


def test_largest_remainder_shares_are_all_zero_when_the_total_is_zero_or_empty():
    assert largest_remainder_shares([0, 0]) == [Decimal("0.00"), Decimal("0.00")]
    assert largest_remainder_shares([]) == []
