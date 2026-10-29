"""Booking validation (FR-003, data-model §5.1): one {field, message} per broken rule."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from hotel_api.business.domain.models import NewBooking, RoomType
from hotel_api.business.errors import FieldError
from hotel_api.business.rules import _parsing, pricing

_DATE_RANGE = "between 2000-01-01 and 2100-12-31"


def validate_booking(
    raw: Mapping[str, Any], room_types: Sequence[RoomType]
) -> tuple[NewBooking | None, list[FieldError]]:
    """Validate raw client values. Returns (booking, []) or (None, errors).

    `price_dkk` stays None when neither price field is given; the service then applies the standard
    price. A fixed `price_per_night_dkk` (FR-019) is checked against the band and turned into the
    total here, so everything after validation only sees `price_dkk`. Giving both is an error.
    """
    errors: list[FieldError] = []

    def text(field: str, label: str) -> str | None:
        value = raw.get(field)
        cleaned = _parsing.clean_text(value)
        if cleaned is None:
            if isinstance(value, str) and len(value.strip()) > 100:
                errors.append(FieldError(field, f"{label} must be at most 100 characters."))
            else:
                errors.append(FieldError(field, f"{label} must not be empty."))
        return cleaned

    first_name = text("first_name", "First name")
    family_name = text("family_name", "Family name")
    country = text("country", "Country")

    room_type = next((r for r in room_types if r.name == raw.get("room_type")), None)
    if room_type is None:
        names = ", ".join(r.name for r in room_types)
        errors.append(FieldError("room_type", f"Room type must be one of: {names}."))

    check_in_date = _parsing.iso_date(raw.get("check_in_date"))
    if check_in_date is None:
        errors.append(
            FieldError(
                "check_in_date",
                f"Check-in date must be a valid date (YYYY-MM-DD) {_DATE_RANGE}.",
            )
        )

    days_rented = _parsing.whole_number(raw.get("days_rented"))
    if days_rented is None or not (1 <= days_rented <= 365):
        days_rented = None
        errors.append(FieldError("days_rented", "Days rented must be a whole number from 1 to 365."))

    price_dkk = None
    nightly_dkk = None
    total_given = raw.get("price_dkk") is not None
    nightly_given = raw.get("price_per_night_dkk") is not None
    if total_given and nightly_given:
        errors.append(
            FieldError("price_per_night_dkk", "Give either the total price or the price per night, not both.")
        )
    elif total_given:
        price_dkk = _parsing.money(raw["price_dkk"])
        if price_dkk is None:
            errors.append(
                FieldError("price_dkk", "Price must be a positive amount in DKK with at most 2 decimals.")
            )
        elif room_type is not None and check_in_date is not None and days_rented is not None:
            message = pricing.price_error(room_type, check_in_date, days_rented, price_dkk)
            if message is not None:
                errors.append(FieldError("price_dkk", message))
    elif nightly_given:
        nightly_dkk = _parsing.money(raw["price_per_night_dkk"])
        if nightly_dkk is None:
            errors.append(
                FieldError(
                    "price_per_night_dkk",
                    "Price per night must be a positive amount in DKK with at most 2 decimals.",
                )
            )
        elif room_type is not None and check_in_date is not None:  # the band needs no number of nights
            message = pricing.nightly_price_error(room_type, check_in_date, nightly_dkk)
            if message is not None:
                errors.append(FieldError("price_per_night_dkk", message))

    if errors:
        return None, errors
    assert first_name and family_name and country and room_type and check_in_date and days_rented
    if nightly_dkk is not None:
        price_dkk = pricing.total_for_nightly_price(nightly_dkk, days_rented)
    return (
        NewBooking(
            first_name=first_name,
            family_name=family_name,
            country=country,
            room_type=room_type.name,
            check_in_date=check_in_date,
            days_rented=days_rented,
            price_dkk=price_dkk,
        ),
        [],
    )
