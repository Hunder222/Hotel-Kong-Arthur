"""Stay KPIs ALOS, ADR and revenue per booking (T084, A7, FR-015): pure, no database."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from hotel_api.business.domain.models import Booking, Season
from hotel_api.business.kpis import hotel

pytestmark = pytest.mark.unit

D = Decimal


def booking(i, room_type, check_in, nights, price):
    return Booking(i, "F", "L", "Germany", room_type, check_in, nights, D(str(price)))


# 2026: 4 bookings, 10 nights, 21850.50 DKK; the 2025 booking must not count
BOOKINGS = [
    booking(1, "Suite", date(2026, 1, 10), 2, 5500),            # low
    booking(2, "Suite", date(2026, 7, 14), 3, 9750),            # high
    booking(3, "Grand Lit", date(2026, 4, 1), 4, 5600),         # mid
    booking(4, "Standard Single", date(2026, 11, 30), 1, 1000.5),  # low
    booking(5, "Suite", date(2025, 12, 31), 9, 99999),          # 2025: ignored
]


def test_formulas():
    alos, adr, per_booking = hotel.stay_figures(4, 10, D("21850.50"))
    assert alos == D("2.50")                # 10 nights / 4 bookings
    assert adr == D("2185.05")              # 21850.50 / 10 nights
    assert per_booking == D("5462.63")      # 21850.50 / 4 = 5462.625, rounded half-up


def test_each_value_is_rounded_half_up_to_two_decimals():
    assert hotel.stay_figures(3, 7, D("100.00"))[0] == D("2.33")    # 7 / 3 = 2.3333
    assert hotel.stay_figures(3, 8, D("100.00"))[0] == D("2.67")    # 8 / 3 = 2.6667
    assert hotel.stay_figures(8, 1, D("0.01"))[2] == D("0.00")      # 0.00125
    assert hotel.stay_figures(2, 1, D("0.05"))[2] == D("0.03")      # 0.025 rounds up


def test_an_empty_scope_gives_zero_for_each_value():
    assert hotel.stay_figures(0, 0, D("0.00")) == (D("0.00"), D("0.00"), D("0.00"))
    assert hotel.stay_figures(3, 0, D("0.00"))[1] == D("0.00")      # no nights: no division by zero


def test_summary_has_alos_adr_and_revenue_per_booking(room_types):
    s = hotel.hotel_summary(BOOKINGS, [], room_types, 2026)
    assert (s.average_length_of_stay_nights, s.average_daily_rate_dkk, s.average_revenue_per_booking_dkk) == (
        D("2.50"), D("2185.05"), D("5462.63"))


def test_summary_of_an_empty_year_is_zero(room_types):
    s = hotel.hotel_summary(BOOKINGS, [], room_types, 2030)
    assert (s.average_length_of_stay_nights, s.average_daily_rate_dkk, s.average_revenue_per_booking_dkk) == (
        D("0.00"), D("0.00"), D("0.00"))


def test_per_room_type(room_types):
    rows = {r.room_type: r for r in hotel.kpis_by_room_type(BOOKINGS, [], room_types, 2026)}
    assert (rows["Suite"].average_length_of_stay_nights, rows["Suite"].average_daily_rate_dkk,
            rows["Suite"].average_revenue_per_booking_dkk) == (D("2.50"), D("3050.00"), D("7625.00"))
    assert (rows["Grand Lit"].average_length_of_stay_nights, rows["Grand Lit"].average_daily_rate_dkk) == (
        D("4.00"), D("1400.00"))
    assert (rows["Standard Single"].average_daily_rate_dkk, rows["Standard Single"].average_revenue_per_booking_dkk) == (
        D("1000.50"), D("1000.50"))
    empty = rows["LOFT Suite"]
    assert (empty.average_length_of_stay_nights, empty.average_daily_rate_dkk, empty.average_revenue_per_booking_dkk) == (
        D("0.00"), D("0.00"), D("0.00"))


def test_per_season(room_types):
    low, mid, high = hotel.kpis_by_season(BOOKINGS, [], room_types, 2026)
    assert [r.season for r in (low, mid, high)] == [Season.LOW, Season.MID, Season.HIGH]
    assert (low.average_length_of_stay_nights, low.average_daily_rate_dkk, low.average_revenue_per_booking_dkk) == (
        D("1.50"), D("2166.83"), D("3250.25"))
    assert (mid.average_length_of_stay_nights, mid.average_daily_rate_dkk, mid.average_revenue_per_booking_dkk) == (
        D("4.00"), D("1400.00"), D("5600.00"))
    assert (high.average_length_of_stay_nights, high.average_daily_rate_dkk, high.average_revenue_per_booking_dkk) == (
        D("3.00"), D("3250.00"), D("9750.00"))
