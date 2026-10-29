"""Use case: guest reviews (K3, FR-011). Validation lives in `rules/review_validation.py`."""

from __future__ import annotations

from typing import Any, Mapping

from hotel_api.business.domain.models import GuestReview
from hotel_api.business.errors import NotFound, ValidationFailed
from hotel_api.business.ports import BookingRepository, ReviewRepository, RoomTypeRepository
from hotel_api.business.rules.review_validation import validate_review


class ReviewService:
    def __init__(
        self, reviews: ReviewRepository, bookings: BookingRepository, room_types: RoomTypeRepository
    ) -> None:
        self._reviews = reviews
        self._bookings = bookings
        self._room_types = room_types

    def list(self) -> list[GuestReview]:
        return self._reviews.list()

    def get(self, review_id: int) -> GuestReview:
        review = self._reviews.get(review_id)
        if review is None:
            raise NotFound(f"Review {review_id} does not exist.")
        return review

    def create(self, raw: Mapping[str, Any]) -> GuestReview:
        """Record a review. With `booking_id`, room type and stay date are copied from that booking."""
        review, errors = validate_review(raw, self._room_types.list_all(), self._bookings.get)
        if review is None:
            raise ValidationFailed(errors)
        return self._reviews.add(review)
