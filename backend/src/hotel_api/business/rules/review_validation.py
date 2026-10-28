"""Review validation (FR-011, data-model §5.2)."""

from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

from hotel_api.business.domain.models import Booking, NewReview, RoomType
from hotel_api.business.errors import FieldError
from hotel_api.business.rules import _parsing

_DATE_MESSAGE = "Stay date must be a valid date (YYYY-MM-DD) between 2000-01-01 and 2100-12-31."


def validate_review(
    raw: Mapping[str, Any],
    room_types: Sequence[RoomType],
    find_booking: Callable[[int], Booking | None],
) -> tuple[NewReview | None, list[FieldError]]:
    """Validate a raw review. Returns the resolved review (room type and stay date copied from the
    booking when `booking_id` is given) or the errors."""
    errors: list[FieldError] = []

    rating = _parsing.whole_number(raw.get("rating"))
    if rating is None or not (1 <= rating <= 5):
        errors.append(FieldError("rating", "Rating must be a whole number from 1 to 5."))

    booking_id: int | None = None
    room_type_name: str | None = None
    stay_date = None

    if raw.get("booking_id") is not None:
        booking_id = _parsing.whole_number(raw["booking_id"])
        booking = find_booking(booking_id) if booking_id is not None and booking_id >= 1 else None
        if booking is None:
            shown = booking_id if booking_id is not None else raw["booking_id"]
            errors.append(FieldError("booking_id", f"Booking {shown} does not exist."))
        for field in ("room_type", "stay_date"):
            if raw.get(field) is not None:
                errors.append(
                    FieldError(field, f"{field.replace('_', ' ').capitalize()} must be omitted when booking_id is given.")
                )
        if booking is not None:
            room_type_name, stay_date = booking.room_type, booking.check_in_date
    else:
        known = next((r for r in room_types if r.name == raw.get("room_type")), None)
        if known is None:
            names = ", ".join(r.name for r in room_types)
            errors.append(
                FieldError("room_type", f"Room type must be one of: {names} (required when booking_id is omitted).")
            )
        else:
            room_type_name = known.name
        stay_date = _parsing.iso_date(raw.get("stay_date"))
        if stay_date is None:
            errors.append(FieldError("stay_date", _DATE_MESSAGE))

    if errors:
        return None, errors
    assert rating is not None and room_type_name is not None and stay_date is not None
    return NewReview(rating=rating, room_type=room_type_name, stay_date=stay_date, booking_id=booking_id), []
