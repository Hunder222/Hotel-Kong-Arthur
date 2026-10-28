"""DTOs for the booking endpoints (contract: `BookingInput`, `Booking`, `BookingList`).

`BookingInput` checks only the JSON shape (an object with exactly the contract's fields). Every
value rule (names, room type, dates, nights, price band) lives in the business layer, so all clients
get the same rules and messages (Constitution VII), and a request with several mistakes reports them
all at once instead of stopping at the first type error.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field

from hotel_api.business.domain.models import Booking as BookingModel
from hotel_api.business.domain.models import Season
from hotel_api.presentation.api.schemas.common import AmountDkk

REPORTING_TIME_ZONE = "Europe/Copenhagen"

# Mirrors the contract's `RoomTypeName` enum; used to reject bad query parameters with 400.
RoomTypeName = Literal[
    "Standard Single",
    "Grand Lit",
    "Standard Double",
    "Superior Double",
    "Junior Suite",
    "Spa Executive",
    "Suite",
    "LOFT Suite",
]


class BookingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: Any = Field(...)
    family_name: Any = Field(...)
    country: Any = Field(...)
    room_type: Any = Field(...)
    check_in_date: Any = Field(...)
    days_rented: Any = Field(...)
    price_dkk: Any = None


def _with_zone(value: datetime | None) -> datetime | None:
    """MySQL returns naive timestamps in the database's time zone (Europe/Copenhagen, set by TZ)."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=ZoneInfo(REPORTING_TIME_ZONE))
    return value


class Booking(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    first_name: str
    family_name: str
    country: str
    room_type: str
    check_in_date: date
    days_rented: int
    price_dkk: AmountDkk
    season: Season
    year: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, booking: BookingModel) -> Booking:
        return cls(
            id=booking.id,
            first_name=booking.first_name,
            family_name=booking.family_name,
            country=booking.country,
            room_type=booking.room_type,
            check_in_date=booking.check_in_date,
            days_rented=booking.days_rented,
            price_dkk=booking.price_dkk,
            season=booking.season,
            year=booking.year,
            created_at=_with_zone(booking.created_at),
            updated_at=_with_zone(booking.updated_at),
        )


class BookingList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[Booking]
