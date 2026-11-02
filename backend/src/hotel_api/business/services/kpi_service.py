"""Use case: hotel KPIs for the `Hotel Analytics` endpoints. Loads the records of the requested scope
through the repository ports and hands them to the pure calculators in `business/kpis/hotel.py`."""

from __future__ import annotations

from dataclasses import dataclass

from hotel_api.business.domain.models import (
    Booking,
    CountryKpi,
    GuestReview,
    HotelFilters,
    HotelSummary,
    RoomType,
    RoomTypeKpi,
    RoomTypeSeasonKpi,
    Season,
    SeasonKpi,
)
from hotel_api.business.kpis import hotel
from hotel_api.business.ports import BookingRepository, ReviewRepository, RoomTypeRepository
from hotel_api.business.rules.seasons import SEASON_ORDER


@dataclass(frozen=True)
class _HotelScope:
    bookings: list[Booking]
    reviews: list[GuestReview]
    room_types: list[RoomType]
    seasons: list[Season]
    years: list[int]


class KpiService:
    def __init__(
        self,
        bookings: BookingRepository,
        reviews: ReviewRepository,
        room_types: RoomTypeRepository,
    ) -> None:
        self._bookings = bookings
        self._reviews = reviews
        self._room_types = room_types

    def summary(self, filters: HotelFilters) -> HotelSummary:
        scope = self._scope(filters)
        return hotel.hotel_summary(
            scope.bookings, scope.reviews, scope.room_types, scope.seasons, scope.years, filters.year
        )

    def by_room_type(self, filters: HotelFilters) -> list[RoomTypeKpi]:
        scope = self._scope(filters)
        return hotel.room_type_kpis(
            scope.bookings, scope.reviews, scope.room_types, scope.seasons, scope.years, filters.year
        )

    def by_season(self, filters: HotelFilters) -> list[SeasonKpi]:
        scope = self._scope(filters)
        return hotel.season_kpis(
            scope.bookings, scope.reviews, scope.room_types, scope.seasons, scope.years, filters.year
        )

    def by_room_type_and_season(self, filters: HotelFilters) -> list[RoomTypeSeasonKpi]:
        scope = self._scope(filters)
        return hotel.room_type_season_kpis(
            scope.bookings, scope.room_types, scope.seasons, scope.years, filters.year
        )

    def by_country(self, filters: HotelFilters) -> list[CountryKpi]:
        return hotel.country_kpis(self._scope(filters).bookings, filters.year)

    def _scope(self, filters: HotelFilters) -> _HotelScope:
        recorded = self._bookings.list()
        country_booking_ids = (
            frozenset(b.id for b in recorded if b.country == filters.country) if filters.country is not None else None
        )
        return _HotelScope(
            bookings=hotel.filter_bookings(recorded, filters),
            reviews=hotel.filter_reviews(self._reviews.list(), filters, country_booking_ids),
            room_types=[
                rt for rt in self._room_types.list_all() if filters.room_type is None or rt.name == filters.room_type
            ],
            seasons=[filters.season] if filters.season is not None else list(SEASON_ORDER),
            years=hotel.years_in_scope(filters.year, (b.year for b in recorded)),
        )
