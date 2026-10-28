"""DTOs for the review endpoints (contract: `ReviewInput`, `Review`, `ReviewList`).

As for bookings, `ReviewInput` checks only the JSON shape; the rules (rating 1-5, booking_id xor
room type + stay date, existing booking) live in the business layer.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from hotel_api.business.domain.models import GuestReview, Season
from hotel_api.presentation.api.schemas.common import with_zone


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: Any = Field(...)
    booking_id: Any = None
    room_type: Any = None
    stay_date: Any = None


class Review(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    booking_id: int | None
    room_type: str
    stay_date: date
    season: Season
    year: int
    rating: int
    created_at: datetime

    @classmethod
    def from_model(cls, review: GuestReview) -> Review:
        return cls(
            id=review.id,
            booking_id=review.booking_id,
            room_type=review.room_type,
            stay_date=review.stay_date,
            season=review.season,
            year=review.year,
            rating=review.rating,
            created_at=with_zone(review.created_at),
        )


class ReviewList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[Review]
