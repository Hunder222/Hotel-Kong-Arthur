"""Golden A7 values from the sample data, through the real repositories (T087, SC-003).

Expected numbers are in specs/001-hotel-analytics-platform/quickstart.md §7, computed from the CSV files
independently of the application.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from hotel_api.business.domain.models import PriceTier, Season
from hotel_api.business.services.bar_service import BarService
from hotel_api.business.services.kpi_service import KpiService
from hotel_api.data.connection import connection_scope
from hotel_api.data.repositories.bar_sales import MySqlBarSalesRepository
from hotel_api.data.repositories.bookings import MySqlBookingRepository
from hotel_api.data.repositories.reviews import MySqlReviewRepository
from hotel_api.data.repositories.room_types import MySqlRoomTypeRepository
from hotel_api.presentation.cli.seed import main as seed_main

pytestmark = pytest.mark.integration

D = Decimal


@pytest.fixture()
def services(test_settings, clean_db, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()
    with connection_scope(test_settings) as conn:
        kpi = KpiService(MySqlBookingRepository(conn), MySqlRoomTypeRepository(conn), MySqlReviewRepository(conn))
        yield kpi, BarService(MySqlBarSalesRepository(conn))


def test_hotel_summary_a7(services):
    kpi, _ = services
    s = kpi.summary(2026)
    assert (s.average_length_of_stay_nights, s.average_daily_rate_dkk, s.average_revenue_per_booking_dkk) == (
        D("5.38"), D("2088.50"), D("11234.03"))


def test_by_season_a7(services):
    kpi, _ = services
    rows = kpi.by_season(2026)
    assert [r.season for r in rows] == [Season.LOW, Season.MID, Season.HIGH]
    assert [(r.average_length_of_stay_nights, r.average_daily_rate_dkk, r.average_revenue_per_booking_dkk) for r in rows] == [
        (D("5.36"), D("1885.37"), D("10102.64")),
        (D("5.48"), D("2073.70"), D("11371.30")),
        (D("5.29"), D("2308.89"), D("12223.93")),
    ]


def test_by_room_type_a7_is_consistent_with_the_totals(services):
    kpi, _ = services
    for row in kpi.by_room_type(2026):
        if row.booking_count:
            assert row.average_length_of_stay_nights == (D(row.nights_sold) / row.booking_count).quantize(D("0.01"), "ROUND_HALF_UP")
            assert row.average_daily_rate_dkk == (row.revenue_dkk / row.nights_sold).quantize(D("0.01"), "ROUND_HALF_UP")


def test_price_tier_demand(services):
    _, bar = services
    budget, standard, premium = bar.by_price_tier(2026)
    assert [r.price_tier for r in (budget, standard, premium)] == [PriceTier.BUDGET, PriceTier.STANDARD, PriceTier.PREMIUM]
    assert (budget.drink_count, budget.units_sold, budget.revenue_dkk, budget.revenue_share_pct) == (
        10, 117881, D("6343884.91"), D("47.17"))
    assert (standard.drink_count, standard.units_sold, standard.revenue_dkk, standard.revenue_share_pct) == (
        10, 29306, D("2739242.59"), D("20.37"))
    assert (premium.drink_count, premium.units_sold, premium.revenue_dkk, premium.revenue_share_pct) == (
        10, 32771, D("4365512.84"), D("32.46"))
    assert [r.unit_share_pct for r in (budget, standard, premium)] == [D("65.50"), D("16.29"), D("18.21")]


def test_a_year_without_data_is_zero_everywhere_but_capacity(services):
    kpi, bar = services
    s = kpi.summary(2030)
    assert (s.booking_count, s.nights_sold, s.total_revenue_dkk, s.occupancy_rate_pct, s.review_count,
            s.average_satisfaction, s.satisfied_share_pct) == (0, 0, D("0.00"), D("0.00"), 0, D("0.00"), D("0.00"))
    assert (s.average_length_of_stay_nights, s.average_daily_rate_dkk, s.average_revenue_per_booking_dkk) == (
        D("0.00"), D("0.00"), D("0.00"))
    assert s.available_room_nights == 78110
    assert all(r.units_sold == 0 and r.revenue_dkk == 0 for r in bar.by_price_tier(2030))
