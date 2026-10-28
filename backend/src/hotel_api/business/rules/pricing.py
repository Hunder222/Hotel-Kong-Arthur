"""Seasonal pricing rule (research R9, data-model §4.2). The single definition."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from hotel_api.business.domain.models import RoomType, SeasonRate
from hotel_api.business.rules.numbers import round_half_up
from hotel_api.business.rules.seasons import season_of


def rate_for(room_type: RoomType, day: date) -> SeasonRate:
    return room_type.rates[season_of(day)]


def standard_price(room_type: RoomType, check_in_date: date, days_rented: int) -> Decimal:
    """Standard nightly rate for the check-in season x nights."""
    return round_half_up(rate_for(room_type, check_in_date).standard_nightly_dkk * days_rented)


def _dkk(amount: Decimal) -> str:
    return f"{round_half_up(amount):,.2f}"


def price_error(
    room_type: RoomType, check_in_date: date, days_rented: int, price_dkk: Decimal
) -> str | None:
    """None if price/nights lies inside the room type's band for the season, else the error text."""
    rate = rate_for(room_type, check_in_date)
    nightly = price_dkk / days_rented
    if rate.min_nightly_dkk <= nightly <= rate.max_nightly_dkk:
        return None
    nights = f"{days_rented} night" + ("" if days_rented == 1 else "s")
    return (
        f"{_dkk(price_dkk)} DKK for {nights} is {_dkk(nightly)} DKK per night, outside "
        f"{_dkk(rate.min_nightly_dkk)}–{_dkk(rate.max_nightly_dkk)} DKK per night for "
        f"{room_type.name} in {season_of(check_in_date).value} season."
    )
