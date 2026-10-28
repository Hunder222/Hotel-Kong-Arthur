"""Golden revenue values from the sample data, through the real repositories (T057, SC-003).

The expected numbers are in specs/001-hotel-analytics-platform/quickstart.md §4 and were computed
independently of the application from the CSV file.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from hotel_api.business.domain.models import Season
from hotel_api.business.services.kpi_service import KpiService
from hotel_api.data.connection import connection_scope
from hotel_api.data.repositories.bookings import MySqlBookingRepository
from hotel_api.data.repositories.reviews import MySqlReviewRepository
from hotel_api.data.repositories.room_types import MySqlRoomTypeRepository
from hotel_api.presentation.cli.seed import main as seed_main

pytestmark = pytest.mark.integration

D = Decimal


@pytest.fixture()
def kpi(test_settings, clean_db, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()
    with connection_scope(test_settings) as conn:
        yield KpiService(MySqlBookingRepository(conn), MySqlRoomTypeRepository(conn), MySqlReviewRepository(conn))


def test_annual_revenue_a6_k2(kpi):
    s = kpi.summary(2026)
    assert (s.total_revenue_dkk, s.booking_count, s.nights_sold) == (D("11234034.00"), 1000, 5379)


def test_revenue_per_room_type_a4(kpi):
    rows = {r.room_type: r for r in kpi.by_room_type(2026)}
    ranked = kpi.by_room_type(2026)
    assert len(ranked) == 8 and [r.revenue_rank for r in ranked] == list(range(1, 9))
    assert (ranked[0].room_type, ranked[0].revenue_dkk, ranked[0].revenue_share_pct) == ("Suite", D("2119671.00"), D("18.87"))
    assert rows["Spa Executive"].revenue_dkk == D("1722396.00") and rows["Spa Executive"].revenue_rank == 2
    assert (ranked[7].room_type, ranked[7].revenue_dkk, ranked[7].revenue_share_pct) == (
        "Standard Single", D("730444.00"), D("6.50"))
    assert sum(r.revenue_share_pct for r in ranked) == D("100.00")
    assert sum(r.revenue_dkk for r in ranked) == D("11234034.00")


def test_revenue_per_country_a3_a5(kpi):
    rows = kpi.by_country(2026)
    assert len(rows) == 20
    assert (rows[0].country, rows[0].revenue_dkk, rows[0].booking_count, rows[0].booking_share_pct) == (
        "South Korea", D("767699.00"), 63, D("6.30"))
    assert (rows[1].country, rows[1].revenue_dkk) == ("China", D("722928.00"))
    assert (rows[19].revenue_rank, rows[19].country, rows[19].revenue_dkk) == (20, "Egypt", D("335786.00"))
    assert sum(r.revenue_share_pct for r in rows) == D("100.00")
    assert sum(r.booking_share_pct for r in rows) == D("100.00")
    assert sum(r.booking_count for r in rows) == 1000


def test_revenue_per_room_type_and_season_a2(kpi):
    rows = kpi.by_room_type_and_season(2026)
    assert len(rows) == 24
    by_key = {(r.room_type, r.season): r.revenue_dkk for r in rows}
    assert by_key[("LOFT Suite", Season.HIGH)] == D("683198.00")
    assert by_key[("Standard Single", Season.LOW)] == D("239940.00")
    assert sum(by_key.values()) == D("11234034.00")


def test_revenue_per_season(kpi):
    rows = kpi.by_season(2026)
    assert [r.season for r in rows] == [Season.LOW, Season.MID, Season.HIGH]
    assert [r.revenue_dkk for r in rows] == [D("3354077.00"), D("3809387.00"), D("4070570.00")]
    assert [r.revenue_share_pct for r in rows] == [D("29.86"), D("33.91"), D("36.23")]
    assert [r.season_days for r in rows] == [89, 153, 123]


def test_a_year_without_bookings_returns_zeros(kpi):
    assert kpi.summary(2030).total_revenue_dkk == D("0.00")
    assert kpi.by_country(2030) == []
    assert all(r.revenue_dkk == 0 for r in kpi.by_room_type_and_season(2030))
