"""Domain models of the business layer (data-model.md §4). No HTTP, no SQL.

Season, year, revenue and price tier are derived here and never stored (research R8).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Final, Literal


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
        # Needs rules/price_tiers.py (task T078); not importable before then.
        from hotel_api.business.rules.price_tiers import tier_for_price

        return tier_for_price(self.unit_price_dkk)


# The `year` a KPI row reports: a calendar year, or "all" for the all-time scope (FR-021).
ALL_YEARS: Final = "all"
ReportingYear = int | Literal["all"]


def year_label(year: int | None) -> ReportingYear:
    """What a KPI row reports as its `year`: the year itself, or "all" when no year was asked for (all-time)."""
    return ALL_YEARS if year is None else year


# ---------------------------------------------------------------------------
# KPI value objects. Field names match the API contract so the DTO mapping is 1:1.
# Money is Decimal; percentages are in percent units (0-100), rounded by rules/numbers.py.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HotelSummary:
    year: ReportingYear
    booking_count: int
    nights_sold: int
    total_revenue_dkk: Decimal
    available_room_nights: int
    occupancy_rate_pct: Decimal
    review_count: int
    average_satisfaction: Decimal
    satisfied_share_pct: Decimal
    average_length_of_stay_nights: Decimal
    average_daily_rate_dkk: Decimal
    average_revenue_per_booking_dkk: Decimal


@dataclass(frozen=True)
class RoomTypeKpi:
    year: ReportingYear
    revenue_rank: int
    room_type: str
    room_count: int
    booking_count: int
    nights_sold: int
    revenue_dkk: Decimal
    revenue_share_pct: Decimal
    available_room_nights: int
    occupancy_rate_pct: Decimal
    review_count: int
    average_satisfaction: Decimal
    satisfied_share_pct: Decimal
    average_length_of_stay_nights: Decimal
    average_daily_rate_dkk: Decimal
    average_revenue_per_booking_dkk: Decimal


@dataclass(frozen=True)
class SeasonKpi:
    year: ReportingYear
    season: Season
    season_days: int
    booking_count: int
    nights_sold: int
    revenue_dkk: Decimal
    revenue_share_pct: Decimal
    available_room_nights: int
    occupancy_rate_pct: Decimal
    review_count: int
    average_satisfaction: Decimal
    satisfied_share_pct: Decimal
    average_length_of_stay_nights: Decimal
    average_daily_rate_dkk: Decimal
    average_revenue_per_booking_dkk: Decimal


@dataclass(frozen=True)
class RoomTypeSeasonKpi:
    year: ReportingYear
    room_type: str
    season: Season
    booking_count: int
    nights_sold: int
    revenue_dkk: Decimal


@dataclass(frozen=True)
class CountryKpi:
    year: ReportingYear
    revenue_rank: int
    country: str
    booking_count: int
    booking_share_pct: Decimal
    nights_sold: int
    revenue_dkk: Decimal
    revenue_share_pct: Decimal


@dataclass(frozen=True)
class BarSummary:
    year: ReportingYear
    drink_count: int
    units_sold: int
    total_revenue_dkk: Decimal


@dataclass(frozen=True)
class BarCategoryKpi:
    year: ReportingYear
    category: DrinkCategory
    drink_count: int
    units_sold: int
    unit_share_pct: Decimal
    revenue_dkk: Decimal
    revenue_share_pct: Decimal


@dataclass(frozen=True)
class BarPriceTierKpi:
    year: ReportingYear
    price_tier: PriceTier
    price_from_dkk: Decimal
    price_to_dkk: Decimal | None
    drink_count: int
    units_sold: int
    unit_share_pct: Decimal
    revenue_dkk: Decimal
    revenue_share_pct: Decimal


@dataclass(frozen=True)
class RankedDrinkSale:
    sale: BarDrinkSale
    revenue_rank: int
    units_rank: int
