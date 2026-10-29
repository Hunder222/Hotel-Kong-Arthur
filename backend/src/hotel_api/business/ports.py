"""Repository interfaces owned by the business layer and implemented by the data layer (R3).

Services depend only on these Protocols, so replacing MySQL touches `data/` and nothing above it.
"""

from __future__ import annotations

from typing import Protocol, Sequence

from hotel_api.business.domain.models import (
    BarDrinkSale,
    Booking,
    GuestReview,
    NewBooking,
    NewReview,
    RoomType,
)


class RoomTypeRepository(Protocol):
    def list_all(self) -> list[RoomType]:
        """All room types in canonical (T1) order, each with rates ordered low, mid, high."""

    def get_by_name(self, name: str) -> RoomType | None: ...


class BookingRepository(Protocol):
    def list(self) -> list[Booking]:
        """All bookings ordered by id, newest (highest id) first."""

    def get(self, booking_id: int) -> Booking | None: ...

    def add(self, booking: NewBooking) -> Booking:
        """Store a booking whose price is already set; returns it with id and timestamps."""

    def replace(self, booking_id: int, booking: NewBooking) -> Booking | None:
        """Replace the editable fields; None if the id does not exist."""

    def delete(self, booking_id: int) -> bool:
        """True if a booking was removed."""

    def delete_all(self) -> None: ...

    def insert_many(self, bookings: Sequence[Booking]) -> None:
        """Bulk insert with explicit ids (seed)."""


class ReviewRepository(Protocol):
    def list(self) -> list[GuestReview]:
        """All reviews, newest first."""

    def get(self, review_id: int) -> GuestReview | None: ...

    def add(self, review: NewReview) -> GuestReview: ...

    def delete_all(self) -> None: ...

    def insert_many(self, reviews: Sequence[GuestReview]) -> None:
        """Bulk insert with explicit ids (seed)."""


class BarSalesRepository(Protocol):
    def list(self) -> list[BarDrinkSale]:
        """All drink sales ordered by id ascending."""

    def delete_all(self) -> None: ...

    def insert_many(self, sales: Sequence[BarDrinkSale]) -> None:
        """Bulk insert with explicit ids (seed)."""


class HealthRepository(Protocol):
    def ping(self) -> None:
        """Raises StorageUnavailable if the database cannot be reached."""


__all__ = [
    "BarSalesRepository",
    "BookingRepository",
    "HealthRepository",
    "ReviewRepository",
    "RoomTypeRepository",
]

