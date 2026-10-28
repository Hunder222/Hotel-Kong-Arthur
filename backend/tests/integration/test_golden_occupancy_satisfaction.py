"""Golden occupancy, satisfaction and guest-origin values from the sample data (T066, SC-003).

Occupancy numbers are in specs/001-hotel-analytics-platform/quickstart.md §5 and were computed from the
CSV independently of the application. Satisfaction values are synthetic, so they are checked against the
reviews the API lists instead of against fixed numbers.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

import pytest

from hotel_api.business.domain.models import Season
from hotel_api.business.services.kpi_service import KpiService
from hotel_api.business.services.review_service import ReviewService
from hotel_api.data.connection import connection_scope
from hotel_api.data.repositories.bookings import MySqlBookingRepository
from hotel_api.data.repositories.reviews import MySqlReviewRepository
from hotel_api.data.repositories.room_types import MySqlRoomTypeRepository
from hotel_api.presentation.cli.seed import main as seed_main

pytestmark = pytest.mark.integration

D = Decimal


def half_up(x) -> Decimal:
    return Decimal(x).quantize(D("0.01"), rounding=ROUND_HALF_UP)


@pytest.fixture()
def services(test_settings, clean_db, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()
    with connection_scope(test_settings) as conn:
        bookings, room_types, reviews = (
            MySqlBookingRepository(conn), MySqlRoomTypeRepository(conn), MySqlReviewRepository(conn))
        yield KpiService(bookings, room_types, reviews), ReviewService(reviews, bookings, room_types)


def test_overall_occupancy_k1(services):
    kpi, _ = services
    s = kpi.summary(2026)
    assert (s.available_room_nights, s.nights_sold, s.occupancy_rate_pct) == (78110, 5379, D("6.89"))


def test_occupancy_per_season_k1(services):
    kpi, _ = services
    low, mid, high = kpi.by_season(2026)
    assert [(r.season_days, r.available_room_nights, r.nights_sold, r.occupancy_rate_pct) for r in (low, mid, high)] == [
        (89, 19046, 1779, D("9.34")), (153, 32742, 1837, D("5.61")), (123, 26322, 1763, D("6.70"))]


def test_occupancy_per_room_type_k1(services):
    kpi, _ = services
    rows = {r.room_type: r for r in kpi.by_room_type(2026)}
    assert (rows["Suite"].available_room_nights, rows["Suite"].nights_sold, rows["Suite"].occupancy_rate_pct) == (
        9490, 706, D("7.44"))
    assert (rows["Standard Single"].available_room_nights, rows["Standard Single"].nights_sold,
            rows["Standard Single"].occupancy_rate_pct) == (9855, 628, D("6.37"))
    assert (rows["LOFT Suite"].available_room_nights, rows["LOFT Suite"].nights_sold,
            rows["LOFT Suite"].occupancy_rate_pct) == (9490, 487, D("5.13"))


def test_satisfaction_k3_matches_the_listed_reviews(services):
    kpi, reviews = services
    listed = reviews.list(year=2026)
    assert len(listed) == 500

    def expected(rows):
        n = len(rows)
        return (n, half_up(D(sum(r.rating for r in rows)) / n),
                half_up(D(sum(1 for r in rows if r.rating >= 4)) * 100 / n))

    s = kpi.summary(2026)
    assert (s.review_count, s.average_satisfaction, s.satisfied_share_pct) == expected(listed)
    for row in kpi.by_room_type(2026):
        subset = reviews.list(year=2026, room_type=row.room_type)
        assert (row.review_count, row.average_satisfaction, row.satisfied_share_pct) == (
            expected(subset) if subset else (0, D("0.00"), D("0.00")))
    for row in kpi.by_season(2026):
        subset = reviews.list(year=2026, season=row.season)
        assert (row.review_count, row.average_satisfaction, row.satisfied_share_pct) == expected(subset)
    assert sum(r.review_count for r in kpi.by_season(2026)) == 500
    assert sum(r.review_count for r in kpi.by_room_type(2026)) == 500
    assert 1 <= float(s.average_satisfaction) <= 5


def test_guest_origin_a1_sums_to_all_bookings(services):
    kpi, _ = services
    rows = kpi.by_country(2026)
    assert sum(r.booking_count for r in rows) == 1000
    assert sum(r.booking_share_pct for r in rows) == D("100.00")


def test_a_year_without_data_has_zero_rates_but_full_capacity(services):
    kpi, _ = services
    s = kpi.summary(2030)
    assert (s.available_room_nights, s.occupancy_rate_pct, s.review_count, s.average_satisfaction,
            s.satisfied_share_pct) == (78110, D("0.00"), 0, D("0.00"), D("0.00"))
    assert all(r.occupancy_rate_pct == 0 and r.available_room_nights > 0 for r in kpi.by_season(2030))


def test_a_new_review_is_counted_at_once(services):
    kpi, reviews = services
    created = reviews.create({"booking_id": 2, "rating": 5})
    assert (created.room_type, created.season) == ("Grand Lit", Season.LOW)
    assert kpi.summary(2026).review_count == 501
