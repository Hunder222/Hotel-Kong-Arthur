"""Pure hotel stay KPI unit tests (T053, A7, FR-015): ALOS, ADR and revenue per booking, no database."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from hotel_api.business.domain.models import Booking, Season
from hotel_api.business.kpis import hotel

pytestmark = pytest.mark.unit

D = Decimal

LOW = date(2026, 1, 15)
MID = date(2026, 4, 15)
HIGH = date(2026, 7, 15)


def booking(
    id_: int,
    room_type: str,
    check_in: date,
    nights: int,
    price: str,
    country: str = "Germany",
) -> Booking:
    return Booking(id_, "Anna", "Jensen", country, room_type, check_in, nights, D(price))


BOOKINGS = [
    booking(1, "Suite", HIGH, 3, "9750.00"),
    booking(2, "Suite", LOW, 2, "5500.00"),
    booking(3, "Standard Single", LOW, 4, "4200.00"),
    booking(4, "LOFT Suite", MID, 1, "3500.00"),
]


def test_stay_metrics_alos_adr_and_revenue_per_booking():
    metrics = hotel.stay_metrics(BOOKINGS)
    assert metrics.booking_count == 4
    assert metrics.nights_sold == 10
    assert metrics.revenue_dkk == D("22950.00")
    assert metrics.average_length_of_stay_nights == D("2.50")       # 10 / 4
    assert metrics.average_daily_rate_dkk == D("2295.00")           # 22950 / 10
    assert metrics.average_revenue_per_booking_dkk == D("5737.50")  # 22950 / 4


def test_stay_metrics_rounds_half_up_to_two_decimals():
    rows = [
        booking(1, "Suite", HIGH, 2, "1000.00"),
        booking(2, "Suite", HIGH, 2, "1000.00"),
        booking(3, "Suite", HIGH, 3, "1000.00"),
    ]
    metrics = hotel.stay_metrics(rows)
    assert metrics.average_length_of_stay_nights == D("2.33")       # 7 / 3 = 2.333... -> 2.33
    assert metrics.average_daily_rate_dkk == D("428.57")            # 3000 / 7 = 428.571... -> 428.57
    assert metrics.average_revenue_per_booking_dkk == D("1000.00")  # 3000 / 3


def test_stay_metrics_with_zero_bookings_returns_zeros_safely():
    empty = hotel.stay_metrics([])
    assert empty.booking_count == 0
    assert empty.nights_sold == 0
    assert empty.revenue_dkk == D("0.00")
    assert empty.average_length_of_stay_nights == D("0.00")
    assert empty.average_daily_rate_dkk == D("0.00")
    assert empty.average_revenue_per_booking_dkk == D("0.00")


def test_summary_exposes_a7_stay_metrics_and_handles_empty_scope(room_types):
    summary = hotel.hotel_summary(BOOKINGS, [], room_types, list(Season), [2026], 2026)
    assert summary.average_length_of_stay_nights == D("2.50")
    assert summary.average_daily_rate_dkk == D("2295.00")
    assert summary.average_revenue_per_booking_dkk == D("5737.50")

    empty = hotel.hotel_summary([], [], room_types, list(Season), [2026], 2026)
    assert empty.average_length_of_stay_nights == D("0.00")
    assert empty.average_daily_rate_dkk == D("0.00")
    assert empty.average_revenue_per_booking_dkk == D("0.00")


def test_room_type_kpis_include_a7_stay_metrics_and_zeros_for_unbooked_types(room_types):
    by_type = {
        r.room_type: r.stay
        for r in hotel.room_type_kpis(BOOKINGS, [], room_types, list(Season), [2026], 2026)
    }
    suite = by_type["Suite"]
    assert (suite.booking_count, suite.nights_sold, suite.revenue_dkk) == (2, 5, D("15250.00"))
    assert suite.average_length_of_stay_nights == D("2.50")        # 5 / 2
    assert suite.average_daily_rate_dkk == D("3050.00")            # 15250 / 5
    assert suite.average_revenue_per_booking_dkk == D("7625.00")   # 15250 / 2

    single = by_type["Standard Single"]
    assert (
        single.average_length_of_stay_nights,
        single.average_daily_rate_dkk,
        single.average_revenue_per_booking_dkk,
    ) == (D("4.00"), D("1050.00"), D("4200.00"))

    grand_lit = by_type["Grand Lit"]
    assert (
        grand_lit.booking_count,
        grand_lit.average_length_of_stay_nights,
        grand_lit.average_daily_rate_dkk,
        grand_lit.average_revenue_per_booking_dkk,
    ) == (0, D("0.00"), D("0.00"), D("0.00"))


def test_season_and_room_type_season_kpis_include_a7_stay_metrics(room_types):
    by_season = {
        r.season: r.stay
        for r in hotel.season_kpis(BOOKINGS, [], room_types, list(Season), [2026], 2026)
    }
    low = by_season[Season.LOW]
    assert (low.booking_count, low.nights_sold, low.revenue_dkk) == (2, 6, D("9700.00"))
    assert low.average_length_of_stay_nights == D("3.00")        # 6 / 2
    assert low.average_daily_rate_dkk == D("1616.67")            # 9700 / 6
    assert low.average_revenue_per_booking_dkk == D("4850.00")   # 9700 / 2

    cells = {
        (r.room_type, r.season): r.stay
        for r in hotel.room_type_season_kpis(BOOKINGS, room_types, list(Season), [2026], 2026)
    }
    assert (
        cells[("Suite", Season.HIGH)].average_length_of_stay_nights,
        cells[("Suite", Season.HIGH)].average_daily_rate_dkk,
        cells[("Suite", Season.HIGH)].average_revenue_per_booking_dkk,
    ) == (D("3.00"), D("3250.00"), D("9750.00"))
    assert (
        cells[("Grand Lit", Season.MID)].average_length_of_stay_nights,
        cells[("Grand Lit", Season.MID)].average_daily_rate_dkk,
        cells[("Grand Lit", Season.MID)].average_revenue_per_booking_dkk,
    ) == (D("0.00"), D("0.00"), D("0.00"))

