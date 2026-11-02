"""Use case: hotel and bar KPIs for the `Hotel Analytics` endpoints. Loads the records of the requested scope
through the repository ports and hands them to the pure calculators in `business/kpis/hotel.py` and `bar.py`."""

from __future__ import annotations

from dataclasses import dataclass

from hotel_api.business.domain.models import (
    BarCategoryKpi,
    BarDrinkSale,
    BarFilters,
    BarPriceTierKpi,
    BarSummary,
    Booking,
    CountryKpi,
    DrinkCategory,
    GuestReview,
    HotelFilters,
    HotelSummary,
    PriceTier,
    RankedDrinkSale,
    RoomType,
    RoomTypeKpi,
    RoomTypeSeasonKpi,
    Season,
    SeasonKpi,
)
from hotel_api.business.kpis import bar, hotel
from hotel_api.business.ports import (
    BarSalesRepository,
    BookingRepository,
    ReviewRepository,
    RoomTypeRepository,
)
from hotel_api.business.rules.price_tiers import PRICE_TIER_ORDER
from hotel_api.business.rules.seasons import SEASON_ORDER


@dataclass(frozen=True)
class _HotelScope:
    bookings: list[Booking]
    reviews: list[GuestReview]
    room_types: list[RoomType]
    seasons: list[Season]
    years: list[int]


@dataclass(frozen=True)
class _BarScope:
    sales: list[BarDrinkSale]
    categories: list[DrinkCategory]
    price_tiers: list[PriceTier]


class KpiService:
    def __init__(
        self,
        bookings: BookingRepository | None = None,
        reviews: ReviewRepository | None = None,
        room_types: RoomTypeRepository | None = None,
        bar_sales: BarSalesRepository | None = None,
    ) -> None:
        self._bookings = bookings
        self._reviews = reviews
        self._room_types = room_types
        self._bar_sales = bar_sales

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

    def bar_summary(self, filters: BarFilters) -> BarSummary:
        scope = self._bar_scope(filters)
        return bar.bar_summary(scope.sales, filters.year)

    def bar_by_drink(self, filters: BarFilters) -> list[RankedDrinkSale]:
        scope = self._bar_scope(filters)
        return bar.ranked_drink_sales(scope.sales)

    def bar_by_category(self, filters: BarFilters) -> list[BarCategoryKpi]:
        scope = self._bar_scope(filters)
        return bar.category_kpis(scope.sales, filters.year, scope.categories)

    def bar_by_price_tier(self, filters: BarFilters) -> list[BarPriceTierKpi]:
        scope = self._bar_scope(filters)
        return bar.price_tier_kpis(scope.sales, filters.year, scope.price_tiers)

    def _scope(self, filters: HotelFilters) -> _HotelScope:
        assert self._bookings is not None and self._reviews is not None and self._room_types is not None
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

    def _bar_scope(self, filters: BarFilters) -> _BarScope:
        assert self._bar_sales is not None
        recorded = self._bar_sales.list()
        return _BarScope(
            sales=bar.filter_drink_sales(recorded, filters),
            categories=[filters.category] if filters.category is not None else list(bar.CATEGORY_ORDER),
            price_tiers=[filters.price_tier] if filters.price_tier is not None else list(PRICE_TIER_ORDER),
        )
