from decimal import Decimal

import pytest

from hotel_api.business.rules.numbers import round_half_up

pytestmark = pytest.mark.unit


def test_round_half_up_rounds_ties_away_from_zero():
    assert round_half_up(Decimal("2.345")) == Decimal("2.35")
    assert round_half_up(Decimal("2.344")) == Decimal("2.34")
    assert round_half_up(Decimal("0.005")) == Decimal("0.01")
    assert round_half_up(5) == Decimal("5.00")

