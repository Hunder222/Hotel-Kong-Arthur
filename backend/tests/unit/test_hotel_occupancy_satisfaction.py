"""Occupancy (K1) and satisfaction (K3) functions (T063): pure, no database."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from hotel_api.business.domain.models import Booking, GuestReview, Season
from hotel_api.business.kpis import hotel
from hotel_api.business.rules.seasons import available_room_nights, days_in_year, season_days

pytestmark = pytest.mark.unit

D = Decimal


def booking(i, room_type, check_in, nights):
    return Booking(i, "F", "L", "Germany", room_type, check_in, nights, D("1000"))


def review(i, room_type, stay, rating):
    return GuestReview(i, None, room_type, stay, rating)


# Suite 3 nights (low), Standard Single 2 nights (high): 5 nights in 2026
BOOKINGS = [booking(1, "Suite", date(2026, 1, 10), 3), booking(2, "Standard Single", date(2026, 7, 14), 2)]
# 4 reviews in 2026 (ratings 5, 4, 3, 1) and one in 2025 that must not count
REVIEWS = [
    review(1, "Suite", date(2026, 1, 10), 5),            # low
    review(2, "Suite", date(2026, 7, 14), 4),            # high
    review(3, "Grand Lit", date(2026, 4, 1), 3),         # mid
    review(4, "Standard Single", date(2026, 11, 30), 1), # low
    review(5, "Suite", date(2025, 12, 31), 5),           # 2025: ignored
]


# ---------------- occupancy (K1) ----------------

def test_available_room_nights_use_214_rooms_and_the_calendar(room_types):
    assert sum(r.room_count for r in room_types) == 214
    assert available_room_nights(214, days_in_year(2026)) == 78110
    assert [available_room_nights(214, d) for d in season_days(2026).values()] == [19046, 32742, 26322]
    assert available_room_nights(26, 365) == 9490 and available_room_nights(27, 365) == 9855


def test_occupancy_formula_with_the_sample_numbers():
    assert hotel.occupancy_rate_pct(5379, 78110) == D("6.89")
    assert [hotel.occupancy_rate_pct(n, a) for n, a in ((1779, 19046), (1837, 32742), (1763, 26322))] == [
        D("9.34"), D("5.61"), D("6.70")]
    assert [hotel.occupancy_rate_pct(n, a) for n, a in ((706, 9490), (628, 9855), (487, 9490))] == [
        D("7.44"), D("6.37"), D("5.13")]


def test_occupancy_with_no_capacity_is_zero_not_an_error():
    assert hotel.occupancy_rate_pct(5, 0) == D("0.00")


def test_summary_occupancy_uses_all_rooms_for_the_whole_year(room_types):
    s = hotel.hotel_summary(BOOKINGS, REVIEWS, room_types, 2026)
    assert (s.available_room_nights, s.nights_sold, s.occupancy_rate_pct) == (78110, 5, D("0.01"))


def test_a_leap_year_has_more_available_room_nights(room_types):
    assert hotel.hotel_summary([], [], room_types, 2028).available_room_nights == 214 * 366


def test_season_occupancy_uses_the_days_of_the_season(room_types):
    low, mid, high = hotel.kpis_by_season(BOOKINGS, REVIEWS, room_types, 2026)
    assert [r.available_room_nights for r in (low, mid, high)] == [19046, 32742, 26322]
    assert [r.occupancy_rate_pct for r in (low, mid, high)] == [D("0.02"), D("0.00"), D("0.01")]


def test_room_type_occupancy_uses_the_rooms_of_that_type(room_types):
    rows = {r.room_type: r for r in hotel.kpis_by_room_type(BOOKINGS, REVIEWS, room_types, 2026)}
    assert (rows["Suite"].available_room_nights, rows["Suite"].occupancy_rate_pct) == (9490, D("0.03"))
    assert (rows["Standard Single"].available_room_nights, rows["Standard Single"].occupancy_rate_pct) == (
        9855, D("0.02"))
    assert rows["Grand Lit"].occupancy_rate_pct == D("0.00")


# ---------------- satisfaction (K3) ----------------

def test_mean_rating_and_satisfied_share():
    count, mean, satisfied = hotel.satisfaction_figures(REVIEWS[:4])
    assert (count, mean, satisfied) == (4, D("3.25"), D("50.00"))


def test_rating_4_counts_as_satisfied_and_3_does_not():
    assert hotel.satisfaction_figures([review(1, "Suite", date(2026, 1, 1), 4)])[2] == D("100.00")
    assert hotel.satisfaction_figures([review(1, "Suite", date(2026, 1, 1), 3)])[2] == D("0.00")


def test_mean_is_rounded_half_up_to_two_decimals():
    ratings = lambda *rs: [review(i, "Suite", date(2026, 1, 1), r) for i, r in enumerate(rs)]
    assert hotel.satisfaction_figures(ratings(5, 4, 4))[1] == D("4.33")
    assert hotel.satisfaction_figures(ratings(1, 2))[1] == D("1.50")
    assert hotel.satisfaction_figures(ratings(5, 5, 4, 4, 4, 4, 4, 4))[1] == D("4.25")


def test_no_reviews_gives_zero_not_an_error():
    assert hotel.satisfaction_figures([]) == (0, D("0.00"), D("0.00"))


def test_summary_satisfaction_counts_only_the_reporting_year(room_types):
    s = hotel.hotel_summary(BOOKINGS, REVIEWS, room_types, 2026)
    assert (s.review_count, s.average_satisfaction, s.satisfied_share_pct) == (4, D("3.25"), D("50.00"))
    assert hotel.hotel_summary(BOOKINGS, REVIEWS, room_types, 2025).review_count == 1


def test_a_review_belongs_to_the_season_and_year_of_its_stay_date(room_types):
    low, mid, high = hotel.kpis_by_season(BOOKINGS, REVIEWS, room_types, 2026)
    assert [(r.review_count, r.average_satisfaction, r.satisfied_share_pct) for r in (low, mid, high)] == [
        (2, D("3.00"), D("50.00")), (1, D("3.00"), D("0.00")), (1, D("4.00"), D("100.00"))]
    assert REVIEWS[3].season is Season.LOW  # stay 2026-11-30


def test_by_room_type_uses_the_reviews_own_room_type(room_types):
    rows = {r.room_type: r for r in hotel.kpis_by_room_type(BOOKINGS, REVIEWS, room_types, 2026)}
    assert (rows["Suite"].review_count, rows["Suite"].average_satisfaction, rows["Suite"].satisfied_share_pct) == (
        2, D("4.50"), D("100.00"))
    assert (rows["Grand Lit"].review_count, rows["Grand Lit"].average_satisfaction) == (1, D("3.00"))
    assert (rows["Standard Single"].average_satisfaction, rows["Standard Single"].satisfied_share_pct) == (
        D("1.00"), D("0.00"))
    empty = rows["LOFT Suite"]
    assert (empty.review_count, empty.average_satisfaction, empty.satisfied_share_pct) == (0, D("0.00"), D("0.00"))


def test_an_empty_dataset_has_zero_rates_but_keeps_the_capacity(room_types):
    s = hotel.hotel_summary([], [], room_types, 2026)
    assert (s.occupancy_rate_pct, s.review_count, s.average_satisfaction, s.satisfied_share_pct) == (
        D("0.00"), 0, D("0.00"), D("0.00"))
    assert s.available_room_nights == 78110
