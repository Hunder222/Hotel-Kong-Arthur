"""Pure hotel occupancy (K1) and customer satisfaction (K3) KPI unit tests (T036): no database, no HTTP."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from hotel_api.business.domain.models import Booking, GuestReview, HotelFilters, Season
from hotel_api.business.kpis import hotel
from hotel_api.business.rules.seasons import days_in_season, days_in_year

pytestmark = pytest.mark.unit

D = Decimal

LOW = date(2026, 1, 15)
MID = date(2026, 4, 15)
HIGH = date(2026, 7, 15)


def booking(
    id: int,
    room_type: str,
    check_in: date,
    nights: int,
    price: str = "3000.00",
    country: str = "Germany",
) -> Booking:
    return Booking(id, "Anna", "Jensen", country, room_type, check_in, nights, D(price))


def review(
    id: int,
    room_type: str,
    stay: date,
    rating: int,
    booking_id: int | None = None,
) -> GuestReview:
    return GuestReview(id, booking_id, room_type, stay, rating)


BOOKINGS = [
    booking(1, "Suite", HIGH, 3, "9750.00", "Germany"),
    booking(2, "Suite", LOW, 2, "5500.00", "Germany"),
    booking(3, "Standard Single",LOW, 4, "4200.00", "Denmark"),
    booking(4, "LOFT Suite", MID, 1, "3500.00", "Egypt"),
]

REVIEWS = [
    review(1, "Suite", HIGH, 5, booking_id=1),
    review(2, "Suite", LOW, 4, booking_id=2),
    review(3, "Standard Single", LOW, 1, booking_id=3),
    review(4, "Grand Lit", MID, 3, booking_id=None),
    review(5, "Suite", date(2025, 7, 10), 5, booking_id=None),
]


# ---------------- available room-nights & occupancy (K1) ----------------


def test_available_room_nights_for_single_year_and_seasons(room_types):
    total_rooms = sum(rt.room_count for rt in room_types)
    assert total_rooms == 214
    assert days_in_year(2026) == 365
    assert [days_in_season(2026, s) for s in Season] == [89, 153, 123]
    assert hotel.available_room_nights(total_rooms, [2026], list(Season)) == 78110
    assert [hotel.available_room_nights(total_rooms, [2026], [s]) for s in Season] == [19046, 32742, 26322]
    assert hotel.available_room_nights(26, [2026], list(Season)) == 9490
    assert hotel.available_room_nights(27, [2026], list(Season)) == 9855


def test_available_room_nights_for_leap_year_all_time_and_filtered_slices():
    assert days_in_year(2024) == 366
    assert days_in_season(2024, Season.LOW) == 90
    assert hotel.available_room_nights(214, [2024], list(Season)) == 214 * 366
    assert hotel.available_room_nights(214, [2024], [Season.LOW]) == 214 * 90
    # All-time across multiple years (2025 + 2026 = 730 days)
    years = hotel.years_in_scope("all", [2025, 2026])
    assert years == [2025, 2026]
    assert hotel.available_room_nights(214, years, list(Season)) == 214 * 730
    # Filtered slice: Suite (26 rooms) in high season (123 days)
    assert hotel.available_room_nights(26, [2026], [Season.HIGH]) == 26 * 123
    # Empty years list (all-time on empty database)
    assert hotel.available_room_nights(214, [], list(Season)) == 0


def test_occupancy_rate_pct_formula_and_golden_numbers():
    assert hotel.occupancy_rate_pct(5379, 78110) == D("6.89")
    assert [hotel.occupancy_rate_pct(n, a) for n, a in ((1779, 19046), (1837, 32742), (1763, 26322))] == [
        D("9.34"),
        D("5.61"),
        D("6.70"),
    ]
    assert [hotel.occupancy_rate_pct(n, a) for n, a in ((706, 9490), (628, 9855), (487, 9490))] == [
        D("7.44"),
        D("6.37"),
        D("5.13"),
    ]


def test_occupancy_rate_pct_handles_zero_denominator_and_zero_nights_safely():
    assert hotel.occupancy_rate_pct(0, 78110) == D("0.00")
    assert hotel.occupancy_rate_pct(10, 0) == D("0.00")
    assert hotel.occupancy_rate_pct(0, 0) == D("0.00")


def test_summary_and_breakdown_occupancy_across_scopes(room_types):
    summary = hotel.hotel_summary(BOOKINGS, REVIEWS[:4], room_types, list(Season), [2026], 2026)
    assert summary.available_room_nights == 78110
    assert summary.stay.nights_sold == 10
    assert summary.occupancy_rate_pct == D("0.01")

    leap_summary = hotel.hotel_summary([], [], room_types, list(Season), [2028], 2028)
    assert leap_summary.available_room_nights == 214 * 366
    assert leap_summary.occupancy_rate_pct == D("0.00")

    seasons = {r.season: r for r in hotel.season_kpis(BOOKINGS, REVIEWS[:4], room_types, list(Season), [2026], 2026)}
    assert seasons[Season.LOW].available_room_nights == 19046
    assert seasons[Season.LOW].stay.nights_sold == 6
    assert seasons[Season.LOW].occupancy_rate_pct == D("0.03")
    assert seasons[Season.MID].available_room_nights == 32742
    assert seasons[Season.HIGH].available_room_nights == 26322

    by_type = {r.room_type: r for r in hotel.room_type_kpis(BOOKINGS, REVIEWS[:4], room_types, list(Season), [2026], 2026)}
    assert (by_type["Suite"].available_room_nights, by_type["Suite"].stay.nights_sold, by_type["Suite"].occupancy_rate_pct) == (
        9490,
        5,
        D("0.05"),
    )
    assert (
        by_type["Standard Single"].available_room_nights,
        by_type["Standard Single"].stay.nights_sold,
        by_type["Standard Single"].occupancy_rate_pct,
    ) == (9855, 4, D("0.04"))
    assert by_type["Grand Lit"].occupancy_rate_pct == D("0.00")


# ---------------- customer satisfaction (K3) ----------------


def test_satisfaction_metrics_mean_and_satisfied_share():
    metrics = hotel.satisfaction_metrics(REVIEWS[:4])
    assert metrics.review_count == 4
    assert metrics.average_satisfaction == D("3.25")
    assert metrics.satisfied_share_pct == D("50.00")


def test_rating_4_counts_as_satisfied_and_rating_3_does_not():
    assert hotel.satisfaction_metrics([review(1, "Suite", LOW, 4)]).satisfied_share_pct == D("100.00")
    assert hotel.satisfaction_metrics([review(1, "Suite", LOW, 5)]).satisfied_share_pct == D("100.00")
    assert hotel.satisfaction_metrics([review(1, "Suite", LOW, 3)]).satisfied_share_pct == D("0.00")


def test_satisfaction_metrics_rounds_half_up_and_handles_zero_reviews():
    empty = hotel.satisfaction_metrics([])
    assert (empty.review_count, empty.average_satisfaction, empty.satisfied_share_pct) == (0, D("0.00"), D("0.00"))

    three = [review(1, "Suite", LOW, 5), review(2, "Suite", LOW, 4), review(3, "Suite", LOW, 4)]
    metrics = hotel.satisfaction_metrics(three)
    assert metrics.average_satisfaction == D("4.33")
    assert metrics.satisfied_share_pct == D("100.00")


def test_satisfaction_in_summary_room_types_and_seasons(room_types):
    reviews_2026 = hotel.filter_reviews(REVIEWS, HotelFilters(year=2026))
    assert len(reviews_2026) == 4
    summary = hotel.hotel_summary(BOOKINGS, reviews_2026, room_types, list(Season), [2026], 2026)
    assert (
        summary.satisfaction.review_count,
        summary.satisfaction.average_satisfaction,
        summary.satisfaction.satisfied_share_pct,
    ) == (4, D("3.25"), D("50.00"))

    by_season = {r.season: r.satisfaction for r in hotel.season_kpis(BOOKINGS, reviews_2026, room_types, list(Season), [2026], 2026)}
    assert (by_season[Season.LOW].review_count, by_season[Season.LOW].average_satisfaction, by_season[Season.LOW].satisfied_share_pct) == (
        2,
        D("2.50"),
        D("50.00"),
    )
    assert (by_season[Season.MID].review_count, by_season[Season.MID].average_satisfaction, by_season[Season.MID].satisfied_share_pct) == (
        1,
        D("3.00"),
        D("0.00"),
    )
    assert (by_season[Season.HIGH].review_count, by_season[Season.HIGH].average_satisfaction, by_season[Season.HIGH].satisfied_share_pct) == (
        1,
        D("5.00"),
        D("100.00"),
    )

    by_type = {r.room_type: r.satisfaction for r in hotel.room_type_kpis(BOOKINGS, reviews_2026, room_types, list(Season), [2026], 2026)}
    assert (by_type["Suite"].review_count, by_type["Suite"].average_satisfaction, by_type["Suite"].satisfied_share_pct) == (
        2,
        D("4.50"),
        D("100.00"),
    )
    assert (by_type["LOFT Suite"].review_count, by_type["LOFT Suite"].average_satisfaction, by_type["LOFT Suite"].satisfied_share_pct) == (
        0,
        D("0.00"),
        D("0.00"),
    )

