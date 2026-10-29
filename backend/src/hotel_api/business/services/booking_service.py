"""Use case: manage bookings (F1, FR-001-FR-005, data-model §5.1).

Validation, season derivation and pricing live in `business/rules`; this service only orchestrates
them with the repositories. Clients pass raw JSON-like values so that every client (frontend,
the hotel's booking system) gets the same rules and the same messages.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from hotel_api.business.domain.models import Booking, NewBooking
from hotel_api.business.errors import NotFound, ValidationFailed
from hotel_api.business.ports import BookingRepository, RoomTypeRepository
from hotel_api.business.rules import pricing
from hotel_api.business.rules.booking_validation import validate_booking


class BookingService:
    def __init__(self, bookings: BookingRepository, room_types: RoomTypeRepository) -> None:
        self._bookings = bookings
        self._room_types = room_types

    def list(self) -> list[Booking]:
        return self._bookings.list()

    def get(self, booking_id: int) -> Booking:
        booking = self._bookings.get(booking_id)
        if booking is None:
            raise _not_found(booking_id)
        return booking

    def create(self, raw: Mapping[str, Any]) -> Booking:
        return self._bookings.add(self._validated_and_priced(raw))

    def replace(self, booking_id: int, raw: Mapping[str, Any]) -> Booking:
        self.get(booking_id)  # an unknown id is a 404 whatever the body says
        updated = self._bookings.replace(booking_id, self._validated_and_priced(raw))
        if updated is None:  # deleted by someone else since the lookup
            raise _not_found(booking_id)
        return updated

    def delete(self, booking_id: int) -> None:
        if not self._bookings.delete(booking_id):
            raise _not_found(booking_id)

    def _validated_and_priced(self, raw: Mapping[str, Any]) -> NewBooking:
        room_types = self._room_types.list_all()
        booking, errors = validate_booking(raw, room_types)
        if booking is None:
            raise ValidationFailed(errors)
        if booking.price_dkk is not None:  # a manual price already passed the band check
            return booking
        room_type = next(r for r in room_types if r.name == booking.room_type)
        price = pricing.standard_price(room_type, booking.check_in_date, booking.days_rented)
        return replace(booking, price_dkk=price)


def _not_found(booking_id: int) -> NotFound:
    return NotFound(f"Booking {booking_id} does not exist.")
