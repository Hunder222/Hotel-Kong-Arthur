"""Pure hotel revenue KPI calculations (A1-A6, K2): no database, no HTTP."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from hotel_api.business.domain.models import Booking, GuestReview, HotelFilters, Season
from hotel_api.business.kpis import hotel

pytestmark = pytest.mark.unit


def booking(id, room_type, check_in, nights, price, country="Germany") -> Booking:
    return Booking(id, "A", "B", country, room_type, check_in, nights, Decimal(price))


def review(id, room_type, stay, rating, booking_id=None) -> GuestReview:
    return GuestReview(id, booking_id, room_type, stay, rating)


LOW = date(2026, 1, 10)
MID = date(2026, 4, 10)
HIGH = date(2026, 7, 10)

BOOKINGS = [
    booking(1, "Suite", HIGH, 3, "9000.00", "Germany"),
    booking(2, "Suite", LOW, 2, "5400.00", "Germany"),
    booking(3, "Standard Single", MID, 4, "4000.00", "Denmark"),
    booking(4, "Standard Single", HIGH, 1, "1500.00", "Egypt"),
    booking(5, "LOFT Suite", HIGH, 2, "7000.00", "Denmark"),
]


def test_total_revenue_sums_prices_and_is_zero_for_no_bookings():
    assert hotel.total_revenue(BOOKINGS) == Decimal("26900.00")
    assert hotel.total_revenue([]) == Decimal("0.00")


def test_room_type_kpis_rank_by_revenue_with_shares_summing_to_100(room_types):
    rows = hotel.room_type_kpis(BOOKINGS, [], room_types, list(Season), [2026], 2026)
    assert len(rows) == 8
    top = rows[0]
    assert (top.revenue_rank, top.room_type, top.stay.revenue_dkk) == (1, "Suite", Decimal("14400.00"))
    assert top.revenue_share_pct == Decimal("53.53")
    assert [r.revenue_rank for r in rows[:3]] == [1, 2, 3]
    assert [r.room_type for r in rows[:3]] == ["Suite", "LOFT Suite", "Standard Single"]
    assert sum(r.revenue_share_pct for r in rows) == Decimal("100.00")


def test_room_type_ties_share_a_rank_and_are_ordered_alphabetically(room_types):
    tied = [booking(1, "Suite", HIGH, 1, "100.00"), booking(2, "Grand Lit", HIGH, 1, "100.00")]
    rows = hotel.room_type_kpis(tied, [], room_types, list(Season), [2026], 2026)
    assert [(r.revenue_rank, r.room_type) for r in rows[:2]] == [(1, "Grand Lit"), (1, "Suite")]
    assert rows[2].revenue_rank == 3  # "1224": the next rank skips


def test_room_type_kpis_for_empty_data_are_zero_but_keep_all_rows(room_types):
    rows = hotel.room_type_kpis([], [], room_types, list(Season), [2026], 2026)
    assert len(rows) == 8
    assert {r.revenue_rank for r in rows} == {1}
    assert all(r.stay.revenue_dkk == 0 and r.revenue_share_pct == 0 and r.occupancy_rate_pct == 0 for r in rows)
    assert all(r.available_room_nights > 0 for r in rows)


def test_country_kpis_rank_by_revenue_with_booking_and_revenue_shares():
    rows = hotel.country_kpis(BOOKINGS, 2026)
    assert [(r.revenue_rank, r.country) for r in rows] == [(1, "Germany"), (2, "Denmark"), (3, "Egypt")]
    germany = rows[0]
    assert (germany.booking_count, germany.nights_sold, germany.revenue_dkk) == (2, 5, Decimal("14400.00"))
    assert germany.booking_share_pct == Decimal("40.00")
    assert germany.revenue_share_pct == Decimal("53.53")
    assert sum(r.booking_share_pct for r in rows) == Decimal("100.00")
    assert sum(r.revenue_share_pct for r in rows) == Decimal("100.00")


def test_country_kpis_for_empty_data_is_empty():
    assert hotel.country_kpis([], "all") == []


def test_country_ties_are_ordered_alphabetically():
    tied = [booking(1, "Suite", HIGH, 1, "100.00", "Spain"), booking(2, "Suite", HIGH, 1, "100.00", "Italy")]
    assert [(r.revenue_rank, r.country) for r in hotel.country_kpis(tied, 2026)] == [(1, "Italy"), (1, "Spain")]


def test_room_type_and_season_kpis_cover_every_cell_in_canonical_order(room_types):
    rows = hotel.room_type_season_kpis(BOOKINGS, room_types, list(Season), [2026], 2026)
    assert len(rows) == 24
    assert [(r.room_type, r.season) for r in rows[:4]] == [
        ("Standard Single", Season.LOW),
        ("Standard Single", Season.MID),
        ("Standard Single", Season.HIGH),
        ("Grand Lit", Season.LOW),
    ]
    by_cell = {(r.room_type, r.season): r for r in rows}
    assert by_cell[("LOFT Suite", Season.HIGH)].stay.revenue_dkk == Decimal("7000.00")
    assert by_cell[("Suite", Season.LOW)].stay.revenue_dkk == Decimal("5400.00")
    assert by_cell[("Suite", Season.MID)].stay.revenue_dkk == Decimal("0.00")
    assert sum(r.stay.revenue_dkk for r in rows) == hotel.total_revenue(BOOKINGS)


def test_season_kpis_give_revenue_and_share_per_season(room_types):
    rows = hotel.season_kpis(BOOKINGS, [], room_types, list(Season), [2026], 2026)
    assert [r.season for r in rows] == [Season.LOW, Season.MID, Season.HIGH]
    assert [r.stay.revenue_dkk for r in rows] == [Decimal("5400.00"), Decimal("4000.00"), Decimal("17500.00")]
    assert [r.season_days for r in rows] == [89, 153, 123]
    assert sum(r.revenue_share_pct for r in rows) == Decimal("100.00")
    assert sum(r.stay.revenue_dkk for r in rows) == hotel.total_revenue(BOOKINGS)


def test_a_season_filter_leaves_one_season_row_and_a_room_type_filter_one_room_type_row(room_types):
    suite_only = [rt for rt in room_types if rt.name == "Suite"]
    high_only = [b for b in BOOKINGS if b.season is Season.HIGH]
    seasons = hotel.season_kpis(high_only, [], room_types, [Season.HIGH], [2026], 2026)
    assert [(r.season, r.revenue_share_pct) for r in seasons] == [(Season.HIGH, Decimal("100.00"))]
    types = hotel.room_type_kpis(BOOKINGS, [], suite_only, list(Season), [2026], 2026)
    assert [(r.room_type, r.revenue_rank, r.revenue_share_pct) for r in types] == [("Suite", 1, Decimal("100.00"))]


def test_available_room_nights_count_calendar_days_of_the_seasons_and_years_in_scope():
    assert hotel.available_room_nights(214, [2026], list(Season)) == 78110
    assert hotel.available_room_nights(214, [2026], [Season.LOW]) == 19046
    assert hotel.available_room_nights(214, [2024], [Season.LOW]) == 214 * 90  # leap year
    assert hotel.available_room_nights(214, [2024], list(Season)) == 214 * 366
    assert hotel.available_room_nights(10, [2025, 2026], list(Season)) == 10 * 730
    assert hotel.available_room_nights(10, [], list(Season)) == 0


def test_years_in_scope_spans_first_to_last_recorded_year_for_all():
    assert hotel.years_in_scope(2026, [2024]) == [2026]
    assert hotel.years_in_scope("all", [2026, 2024, 2024]) == [2024, 2025, 2026]
    assert hotel.years_in_scope("all", []) == []


def test_filters_select_bookings_by_year_season_room_type_and_country():
    mixed = BOOKINGS + [booking(6, "Suite", date(2025, 7, 1), 2, "3000.00", "Germany")]
    assert len(hotel.filter_bookings(mixed, HotelFilters())) == 6
    assert len(hotel.filter_bookings(mixed, HotelFilters(year=2026))) == 5
    assert [b.id for b in hotel.filter_bookings(mixed, HotelFilters(year=2025))] == [6]
    assert [b.id for b in hotel.filter_bookings(mixed, HotelFilters(season=Season.LOW))] == [2]
    assert [b.id for b in hotel.filter_bookings(mixed, HotelFilters(room_type="LOFT Suite"))] == [5]
    assert [b.id for b in hotel.filter_bookings(mixed, HotelFilters(country="Egypt"))] == [4]
    assert [b.id for b in hotel.filter_bookings(mixed, HotelFilters(year=2026, season=Season.HIGH, country="Germany"))] == [1]


def test_country_filter_keeps_only_the_reviews_of_that_countrys_bookings():
    reviews = [review(1, "Suite", HIGH, 5, booking_id=1), review(2, "Suite", HIGH, 3, booking_id=4), review(3, "Suite", HIGH, 4)]
    kept = hotel.filter_reviews(reviews, HotelFilters(country="Germany"), frozenset({1, 2}))
    assert [r.id for r in kept] == [1]
    assert len(hotel.filter_reviews(reviews, HotelFilters())) == 3
