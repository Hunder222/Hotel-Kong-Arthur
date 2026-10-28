from decimal import Decimal

import pytest

from hotel_api.business.rules.numbers import (
    round_half_up,
    safe_average,
    safe_pct,
    safe_ratio,
    shares_pct,
)

pytestmark = pytest.mark.unit


def test_round_half_up_rounds_ties_away_from_zero():
    assert round_half_up(Decimal("2.345")) == Decimal("2.35")
    assert round_half_up(Decimal("2.344")) == Decimal("2.34")
    assert round_half_up(Decimal("0.005")) == Decimal("0.01")
    assert round_half_up(5) == Decimal("5.00")


def test_zero_denominator_gives_zero():
    assert safe_ratio(5, 0) == 0
    assert safe_average(100, 0) == Decimal("0.00")
    assert safe_pct(3, 0) == Decimal("0.00")


def test_safe_values_match_the_sample_data_kpis():
    assert safe_pct(5379, 78110) == Decimal("6.89")
    assert safe_average(5379, 1000) == Decimal("5.38")
    assert safe_average(11234034, 5379) == Decimal("2088.50")


def test_shares_sum_to_exactly_100():
    shares = shares_pct([1, 1, 1])
    assert shares == [Decimal("33.34"), Decimal("33.33"), Decimal("33.33")]
    assert sum(shares) == Decimal("100.00")


def test_shares_for_the_sample_season_revenue():
    shares = shares_pct([3354077, 3809387, 4070570])
    assert shares == [Decimal("29.86"), Decimal("33.91"), Decimal("36.23")]


def test_shares_for_the_bar_category_split():
    assert shares_pct([Decimal("7104755.43"), Decimal("6343884.91")]) == [Decimal("52.83"), Decimal("47.17")]
    assert shares_pct([62077, 117881]) == [Decimal("34.50"), Decimal("65.50")]


def test_shares_of_zero_total_are_zero():
    assert shares_pct([0, 0]) == [Decimal("0.00"), Decimal("0.00")]
    assert shares_pct([]) == []


def test_shares_reject_negative_values():
    with pytest.raises(ValueError):
        shares_pct([5, -1])
