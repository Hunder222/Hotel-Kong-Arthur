"""Use case: hotel KPIs. Loads one reporting year of data through the ports and calls the pure KPI
functions in `business/kpis`; it contains no formulas itself (Constitution VII).

Revenue (US2), occupancy and satisfaction (US3), ALOS / ADR / revenue per booking (US5).
"""

from __future__ import annotations

from hotel_api.business.domain.models import (
    CountryKpi,
    HotelSummary,
    RoomTypeKpi,
    RoomTypeSeasonKpi,
    SeasonKpi,
)
from hotel_api.business.kpis import hotel
from hotel_api.business.ports import BookingRepository, ReviewRepository, RoomTypeRepository


class KpiService:
    def __init__(
        self, bookings: BookingRepository, room_types: RoomTypeRepository, reviews: ReviewRepository
    ) -> None:
        self._bookings = bookings
        self._room_types = room_types
        self._reviews = reviews

    def summary(self, year: int) -> HotelSummary:
        return hotel.hotel_summary(
            self._bookings.list(year=year), self._reviews.list(year=year), self._room_types.list_all(), year
        )

    def by_room_type(self, year: int) -> list[RoomTypeKpi]:
        return hotel.kpis_by_room_type(
            self._bookings.list(year=year), self._reviews.list(year=year), self._room_types.list_all(), year
        )

    def by_season(self, year: int) -> list[SeasonKpi]:
        return hotel.kpis_by_season(
            self._bookings.list(year=year), self._reviews.list(year=year), self._room_types.list_all(), year
        )

    def by_room_type_and_season(self, year: int) -> list[RoomTypeSeasonKpi]:
        return hotel.revenue_by_room_type_and_season(
            self._bookings.list(year=year), self._room_types.list_all(), year
        )

    def by_country(self, year: int) -> list[CountryKpi]:
        return hotel.revenue_by_country(self._bookings.list(year=year), year)
