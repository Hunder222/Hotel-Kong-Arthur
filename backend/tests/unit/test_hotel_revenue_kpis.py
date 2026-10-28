"""Revenue KPI functions (T055): pure, no database."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from hotel_api.business.domain.models import Booking, Season
from hotel_api.business.kpis import hotel
from hotel_api.business.services.kpi_service import KpiService

pytestmark = pytest.mark.unit


def booking(i, room_type, country, check_in, nights, price):
    return Booking(i, "F", "L", country, room_type, check_in, nights, Decimal(str(price)))


# 2026: 4 bookings (Suite x2, Grand Lit, Standard Single) + one in 2025 and one in 2027 that must not count
BOOKINGS = [
    booking(1, "Suite", "Germany", date(2026, 1, 10), 2, 5500),          # low
    booking(2, "Suite", "Germany", date(2026, 7, 14), 3, 9750),          # high
    booking(3, "Grand Lit", "Sweden", date(2026, 4, 1), 4, 5600),        # mid
    booking(4, "Standard Single", "Sweden", date(2026, 11, 30), 1, 1000.5),  # low
    booking(5, "Suite", "Japan", date(2025, 12, 31), 5, 15000),          # 2025: ignored
    booking(6, "Suite", "Japan", date(2027, 1, 1), 5, 15000),            # 2027: ignored
]
TOTAL = Decimal("21850.50")


def test_summary_sums_revenue_bookings_and_nights():
    s = hotel.hotel_revenue_summary(BOOKINGS, 2026)
    assert (s.year, s.booking_count, s.nights_sold, s.total_revenue_dkk) == (2026, 4, 10, TOTAL)


def test_a_booking_belongs_to_the_year_of_its_check_in_date():
    assert hotel.hotel_revenue_summary(BOOKINGS, 2025).total_revenue_dkk == Decimal("15000.00")
    assert hotel.hotel_revenue_summary(BOOKINGS, 2027).booking_count == 1
    # a stay that starts on 31 December and runs into January still counts entirely in 2025
    assert hotel.bookings_of_year(BOOKINGS, 2025)[0].id == 5


def test_empty_dataset_returns_zeros_not_errors(room_types):
    s = hotel.hotel_revenue_summary([], 2026)
    assert (s.booking_count, s.nights_sold, s.total_revenue_dkk) == (0, 0, Decimal("0.00"))
    assert all(r.revenue_share_pct == 0 and r.revenue_dkk == 0 for r in hotel.revenue_by_room_type([], room_types, 2026))
    assert all(r.revenue_share_pct == 0 for r in hotel.revenue_by_season([], 2026))
    assert hotel.revenue_by_country([], 2026) == []
    assert len(hotel.revenue_by_room_type_and_season([], room_types, 2026)) == 24


def test_by_room_type_has_all_eight_rows_ranked_by_revenue(room_types):
    rows = hotel.revenue_by_room_type(BOOKINGS, room_types, 2026)
    assert len(rows) == 8
    top = rows[:3]
    assert [(r.revenue_rank, r.room_type) for r in top] == [(1, "Suite"), (2, "Grand Lit"), (3, "Standard Single")]
    assert (top[0].revenue_dkk, top[0].booking_count, top[0].nights_sold, top[0].room_count) == (
        Decimal("15250.00"), 2, 5, 26)
    # five room types without bookings share rank 4 and are listed by name
    rest = rows[3:]
    assert {r.revenue_rank for r in rest} == {4}
    assert [r.room_type for r in rest] == sorted(r.room_type for r in rest)
    assert all(r.revenue_dkk == 0 and r.booking_count == 0 for r in rest)


def test_room_type_revenue_shares_sum_to_exactly_100(room_types):
    rows = hotel.revenue_by_room_type(BOOKINGS, room_types, 2026)
    assert sum(r.revenue_share_pct for r in rows) == Decimal("100.00")
    assert rows[0].revenue_share_pct == Decimal("69.79")  # 15250 / 21850.5
    assert sum(r.revenue_dkk for r in rows) == TOTAL


def test_by_season_has_three_rows_low_mid_high_with_calendar_days():
    rows = hotel.revenue_by_season(BOOKINGS, 2026)
    assert [r.season for r in rows] == [Season.LOW, Season.MID, Season.HIGH]
    assert [r.season_days for r in rows] == [89, 153, 123]
    assert [r.revenue_dkk for r in rows] == [Decimal("6500.50"), Decimal("5600.00"), Decimal("9750.00")]
    assert [r.booking_count for r in rows] == [2, 1, 1]
    assert [r.nights_sold for r in rows] == [3, 4, 3]
    assert sum(r.revenue_share_pct for r in rows) == Decimal("100.00")


def test_season_is_taken_from_the_check_in_month():
    edge = [booking(1, "Suite", "X", date(2026, 11, 30), 10, 30000), booking(2, "Suite", "X", date(2026, 12, 1), 1, 3000)]
    low, mid, high = hotel.revenue_by_season(edge, 2026)
    assert (low.booking_count, high.booking_count, mid.booking_count) == (1, 1, 0)


def test_by_room_type_and_season_has_24_rows_in_room_type_then_season_order(room_types):
    rows = hotel.revenue_by_room_type_and_season(BOOKINGS, room_types, 2026)
    assert len(rows) == 24
    assert [(r.room_type, r.season) for r in rows[:4]] == [
        ("Standard Single", Season.LOW), ("Standard Single", Season.MID),
        ("Standard Single", Season.HIGH), ("Grand Lit", Season.LOW)]
    assert [r.room_type for r in rows[::3]] == [r.name for r in room_types]
    by_key = {(r.room_type, r.season): r for r in rows}
    assert by_key[("Suite", Season.LOW)].revenue_dkk == Decimal("5500.00")
    assert by_key[("Suite", Season.HIGH)].revenue_dkk == Decimal("9750.00")
    assert by_key[("Suite", Season.HIGH)].nights_sold == 3
    assert sum(r.revenue_dkk for r in rows) == TOTAL


def test_by_country_is_ranked_with_booking_and_revenue_shares():
    rows = hotel.revenue_by_country(BOOKINGS, 2026)
    assert [(r.revenue_rank, r.country) for r in rows] == [(1, "Germany"), (2, "Sweden")]
    germany, sweden = rows
    assert (germany.booking_count, germany.nights_sold, germany.revenue_dkk) == (2, 5, Decimal("15250.00"))
    assert (germany.booking_share_pct, sweden.booking_share_pct) == (Decimal("50.00"), Decimal("50.00"))
    assert (germany.revenue_share_pct, sweden.revenue_share_pct) == (Decimal("69.79"), Decimal("30.21"))
    assert germany.revenue_share_pct + sweden.revenue_share_pct == Decimal("100.00")


def test_equal_country_revenue_shares_a_rank_and_is_listed_by_name():
    tie = [booking(1, "Suite", "Spain", date(2026, 3, 1), 1, 3000), booking(2, "Suite", "Brazil", date(2026, 3, 2), 1, 3000),
           booking(3, "Suite", "Chile", date(2026, 3, 3), 1, 1000)]
    rows = hotel.revenue_by_country(tie, 2026)
    assert [(r.revenue_rank, r.country) for r in rows] == [(1, "Brazil"), (1, "Spain"), (3, "Chile")]


def test_booking_shares_sum_to_100_when_they_do_not_divide_evenly():
    three = [booking(i, "Suite", c, date(2026, 3, 1), 1, 3000) for i, c in enumerate(["A", "B", "C"], 1)]
    assert sum(r.booking_share_pct for r in hotel.revenue_by_country(three, 2026)) == Decimal("100.00")


# ---- KpiService only loads data through the ports and delegates to the functions ----

class FakeBookings:
    def __init__(self, rows):
        self.rows, self.years = rows, []

    def list(self, year=None, season=None, room_type=None, country=None):
        self.years.append(year)
        return [b for b in self.rows if year is None or b.check_in_date.year == year]


class FakeRoomTypes:
    def __init__(self, room_types):
        self._r = room_types

    def list_all(self):
        return list(self._r)


def test_service_loads_one_year_and_delegates(room_types):
    repo = FakeBookings(BOOKINGS)
    service = KpiService(repo, FakeRoomTypes(room_types))
    assert service.summary(2026).total_revenue_dkk == TOTAL
    assert len(service.by_room_type(2026)) == 8
    assert len(service.by_season(2026)) == 3
    assert len(service.by_room_type_and_season(2026)) == 24
    assert service.by_country(2026)[0].country == "Germany"
    assert repo.years == [2026] * 5
    assert service.summary(2030).total_revenue_dkk == Decimal("0.00")
