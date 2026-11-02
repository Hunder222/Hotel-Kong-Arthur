"""Domain models of the business layer (data-model.md §4). No HTTP, no SQL.

Season and year are derived here and never stored (research R8).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal, Union


# A calendar year (2000-2100) or "all" for the all-time scope (FR-021).
ReportYear = Union[int, Literal["all"]]

# The 8 room types in canonical (T1) order; the valid values of the `room_type` filter.
ROOM_TYPE_NAMES: tuple[str, ...] = (
    "Standard Single",
    "Grand Lit",
    "Standard Double",
    "Superior Double",
    "Junior Suite",
    "Spa Executive",
    "Suite",
    "LOFT Suite",
)


class Season(str, Enum):
    LOW = "low"
    MID = "mid"
    HIGH = "high"


class DrinkCategory(str, Enum):
    COCKTAIL = "Cocktail"
    COFFEE = "Coffee"


class PriceTier(str, Enum):
    BUDGET = "budget"
    STANDARD = "standard"
    PREMIUM = "premium"


@dataclass(frozen=True)
class SeasonRate:
    season: Season
    min_nightly_dkk: Decimal
    max_nightly_dkk: Decimal
    standard_nightly_dkk: Decimal


@dataclass(frozen=True)
class RoomType:
    id: int
    name: str
    name_da: str
    room_count: int
    max_guests: int
    rates: dict[Season, SeasonRate] = field(default_factory=dict)


@dataclass(frozen=True)
class NewBooking:
    """Client-editable booking fields. `price_dkk` is None until the standard price is applied."""

    first_name: str
    family_name: str
    country: str
    room_type: str
    check_in_date: date
    days_rented: int
    price_dkk: Decimal | None = None


@dataclass(frozen=True)
class Booking:
    id: int
    first_name: str
    family_name: str
    country: str
    room_type: str
    check_in_date: date
    days_rented: int
    price_dkk: Decimal
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def season(self) -> Season:
        from hotel_api.business.rules.seasons import season_of  # deferred: rules import this module

        return season_of(self.check_in_date)

    @property
    def year(self) -> int:
        return self.check_in_date.year


@dataclass(frozen=True)
class NewReview:
    """A resolved review: room type and stay date are already copied from the booking, if any."""

    rating: int
    room_type: str
    stay_date: date
    booking_id: int | None = None


@dataclass(frozen=True)
class GuestReview:
    id: int
    booking_id: int | None
    room_type: str
    stay_date: date
    rating: int
    created_at: datetime | None = None

    @property
    def season(self) -> Season:
        from hotel_api.business.rules.seasons import season_of  # deferred: rules import this module

        return season_of(self.stay_date)

    @property
    def year(self) -> int:
        return self.stay_date.year


@dataclass(frozen=True)
class BarDrinkSale:
    id: int
    sales_year: int
    drink_name: str
    category: DrinkCategory
    unit_price_dkk: Decimal
    units_sold: int

    @property
    def revenue_dkk(self) -> Decimal:
        return self.unit_price_dkk * self.units_sold

    @property
    def price_tier(self) -> PriceTier:
        from hotel_api.business.rules.price_tiers import classify_price_tier

        return classify_price_tier(self.unit_price_dkk)


@dataclass(frozen=True)
class HotelFilters:
    """The optional filter attributes of the `Hotel Analytics` hotel endpoints."""

    year: ReportYear = "all"
    season: Season | None = None
    room_type: str | None = None
    country: str | None = None


@dataclass(frozen=True)
class BarFilters:
    """The optional filter attributes of the `Hotel Analytics` bar endpoints."""

    year: ReportYear = "all"
    category: DrinkCategory | None = None
    price_tier: PriceTier | None = None


@dataclass(frozen=True)
class StayMetrics:
    """Booking figures shared by every hotel KPI row (K2, A7)."""

    booking_count: int
    nights_sold: int
    revenue_dkk: Decimal
    average_length_of_stay_nights: Decimal
    average_daily_rate_dkk: Decimal
    average_revenue_per_booking_dkk: Decimal


@dataclass(frozen=True)
class SatisfactionMetrics:
    """Review figures shared by the summary, room type and season KPI rows (K3)."""

    review_count: int
    average_satisfaction: Decimal
    satisfied_share_pct: Decimal


@dataclass(frozen=True)
class HotelSummary:
    """Overall hotel KPI summary for the requested filter scope (A6, K1, K2, K3, A7)."""

    year: ReportYear
    stay: StayMetrics
    available_room_nights: int
    occupancy_rate_pct: Decimal
    satisfaction: SatisfactionMetrics

    @property
    def booking_count(self) -> int:
        return self.stay.booking_count

    @property
    def nights_sold(self) -> int:
        return self.stay.nights_sold

    @property
    def total_revenue_dkk(self) -> Decimal:
        return self.stay.revenue_dkk

    @property
    def review_count(self) -> int:
        return self.satisfaction.review_count

    @property
    def average_satisfaction(self) -> Decimal:
        return self.satisfaction.average_satisfaction

    @property
    def satisfied_share_pct(self) -> Decimal:
        return self.satisfaction.satisfied_share_pct

    @property
    def average_length_of_stay_nights(self) -> Decimal:
        return self.stay.average_length_of_stay_nights

    @property
    def average_daily_rate_dkk(self) -> Decimal:
        return self.stay.average_daily_rate_dkk

    @property
    def average_revenue_per_booking_dkk(self) -> Decimal:
        return self.stay.average_revenue_per_booking_dkk


@dataclass(frozen=True)
class RoomTypeKpi:
    year: ReportYear
    revenue_rank: int
    room_type: str
    room_count: int
    stay: StayMetrics
    revenue_share_pct: Decimal
    available_room_nights: int
    occupancy_rate_pct: Decimal
    satisfaction: SatisfactionMetrics


@dataclass(frozen=True)
class SeasonKpi:
    year: ReportYear
    season: Season
    season_days: int
    stay: StayMetrics
    revenue_share_pct: Decimal
    available_room_nights: int
    occupancy_rate_pct: Decimal
    satisfaction: SatisfactionMetrics


@dataclass(frozen=True)
class RoomTypeSeasonKpi:
    year: ReportYear
    room_type: str
    season: Season
    room_count: int
    season_days: int
    stay: StayMetrics
    available_room_nights: int
    occupancy_rate_pct: Decimal


@dataclass(frozen=True)
class CountryKpi:
    year: ReportYear
    revenue_rank: int
    country: str
    booking_count: int
    booking_share_pct: Decimal
    nights_sold: int
    revenue_dkk: Decimal
    revenue_share_pct: Decimal


@dataclass(frozen=True)
class BarSummary:
    """Helene Christine's total lobby bar sales for the requested filter scope (B1)."""

    year: ReportYear
    drink_count: int
    units_sold: int
    total_revenue_dkk: Decimal


@dataclass(frozen=True)
class RankedDrinkSale:
    """A bar drink sale enriched with calculated revenue, popularity ranks and price tier (B2, FR-016)."""

    sale: BarDrinkSale
    revenue_rank: int
    units_rank: int

    @property
    def id(self) -> int:
        return self.sale.id

    @property
    def year(self) -> int:
        return self.sale.sales_year

    @property
    def drink_name(self) -> str:
        return self.sale.drink_name

    @property
    def category(self) -> DrinkCategory:
        return self.sale.category

    @property
    def unit_price_dkk(self) -> Decimal:
        return self.sale.unit_price_dkk

    @property
    def units_sold(self) -> int:
        return self.sale.units_sold

    @property
    def revenue_dkk(self) -> Decimal:
        return self.sale.revenue_dkk

    @property
    def price_tier(self) -> PriceTier:
        return self.sale.price_tier


@dataclass(frozen=True)
class BarCategoryKpi:
    """Category-level bar sales and percentage split for Cocktail vs. Coffee (B3)."""

    year: ReportYear
    category: DrinkCategory
    drink_count: int
    units_sold: int
    unit_share_pct: Decimal
    revenue_dkk: Decimal
    revenue_share_pct: Decimal


@dataclass(frozen=True)
class BarPriceTierKpi:
    """Price-tier bar demand for budget, standard and premium drinks (A7 / US4, FR-016)."""

    year: ReportYear
    price_tier: PriceTier
    price_from_dkk: Decimal
    price_to_dkk: Decimal | None
    drink_count: int
    units_sold: int
    unit_share_pct: Decimal
    revenue_dkk: Decimal
    revenue_share_pct: Decimal
