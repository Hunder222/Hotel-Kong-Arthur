"""Domain models of the business layer (data-model.md §4). No HTTP, no SQL.

Season and year are derived here and never stored (research R8).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class Season(str, Enum):
    LOW = "low"
    MID = "mid"
    HIGH = "high"


class DrinkCategory(str, Enum):
    COCKTAIL = "Cocktail"
    COFFEE = "Coffee"


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

