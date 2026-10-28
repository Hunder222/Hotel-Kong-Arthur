"""Use case: hotel KPIs. Loads one reporting year of data through the ports and calls the pure KPI
functions in `business/kpis`; it contains no formulas itself (Constitution VII).

Revenue part (US2). The occupancy / satisfaction (US3) and ALOS / ADR (US5) figures extend it.
"""

from __future__ import annotations

from hotel_api.business.domain.models import (
    CountryKpi,
    HotelRevenueSummary,
    RoomTypeRevenue,
    RoomTypeSeasonKpi,
    SeasonRevenue,
)
from hotel_api.business.kpis import hotel
from hotel_api.business.ports import BookingRepository, RoomTypeRepository


class KpiService:
    def __init__(self, bookings: BookingRepository, room_types: RoomTypeRepository) -> None:
        self._bookings = bookings
        self._room_types = room_types

    def summary(self, year: int) -> HotelRevenueSummary:
        return hotel.hotel_revenue_summary(self._bookings.list(year=year), year)

    def by_room_type(self, year: int) -> list[RoomTypeRevenue]:
        return hotel.revenue_by_room_type(self._bookings.list(year=year), self._room_types.list_all(), year)

    def by_season(self, year: int) -> list[SeasonRevenue]:
        return hotel.revenue_by_season(self._bookings.list(year=year), year)

    def by_room_type_and_season(self, year: int) -> list[RoomTypeSeasonKpi]:
        return hotel.revenue_by_room_type_and_season(
            self._bookings.list(year=year), self._room_types.list_all(), year
        )

    def by_country(self, year: int) -> list[CountryKpi]:
        return hotel.revenue_by_country(self._bookings.list(year=year), year)
