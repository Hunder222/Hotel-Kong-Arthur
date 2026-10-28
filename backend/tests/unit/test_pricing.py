from datetime import date
from decimal import Decimal

import pytest

from hotel_api.business.rules.pricing import price_error, standard_price

pytestmark = pytest.mark.unit

LOW_DAY, MID_DAY, HIGH_DAY = date(2026, 1, 10), date(2026, 4, 10), date(2026, 7, 14)


def test_standard_price_uses_the_season_of_the_check_in_date(by_name):
    assert standard_price(by_name["Superior Double"], HIGH_DAY, 3) == Decimal("6000.00")
    assert standard_price(by_name["Superior Double"], HIGH_DAY, 5) == Decimal("10000.00")
    assert standard_price(by_name["Standard Single"], LOW_DAY, 2) == Decimal("2100.00")
    assert standard_price(by_name["Suite"], MID_DAY, 1) == Decimal("3000.00")


def test_band_edges_are_inclusive(by_name):
    single = by_name["Standard Single"]  # low season 900-1200
    assert price_error(single, LOW_DAY, 3, Decimal("2700")) is None  # 900/night
    assert price_error(single, LOW_DAY, 3, Decimal("3600")) is None  # 1200/night
    assert price_error(single, LOW_DAY, 3, Decimal("2699.99")) is not None
    assert price_error(single, LOW_DAY, 3, Decimal("3600.01")) is not None


def test_the_same_price_can_be_valid_in_one_season_and_not_another(by_name):
    single = by_name["Standard Single"]
    assert price_error(single, HIGH_DAY, 1, Decimal("1400")) is None  # high band 1200-1500
    assert price_error(single, LOW_DAY, 1, Decimal("1400")) is not None


def test_error_message_names_the_allowed_range(by_name):
    message = price_error(by_name["Standard Single"], LOW_DAY, 3, Decimal("4500"))
    assert message == (
        "4,500.00 DKK for 3 nights is 1,500.00 DKK per night, outside "
        "900.00–1,200.00 DKK per night for Standard Single in low season."
    )


def test_error_message_for_a_single_night(by_name):
    message = price_error(by_name["Suite"], HIGH_DAY, 1, Decimal("100"))
    assert message.startswith("100.00 DKK for 1 night is 100.00 DKK per night")
