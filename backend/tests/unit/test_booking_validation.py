from decimal import Decimal

import pytest

from hotel_api.business.rules.booking_validation import validate_booking

pytestmark = pytest.mark.unit

VALID = {
    "first_name": "Elena",
    "family_name": "Müller",
    "country": "Germany",
    "room_type": "Superior Double",
    "check_in_date": "2026-07-14",
    "days_rented": 3,
}


def run(room_types, **overrides):
    raw = {**VALID, **overrides}
    return validate_booking(raw, room_types)


def fields(errors):
    return [e.field for e in errors]


def test_valid_booking_without_price(room_types):
    booking, errors = run(room_types)
    assert errors == []
    assert booking.price_dkk is None
    assert booking.family_name == "Müller"
    assert booking.days_rented == 3


def test_text_is_trimmed(room_types):
    booking, _ = run(room_types, first_name="  Elena ", country=" Germany")
    assert (booking.first_name, booking.country) == ("Elena", "Germany")


@pytest.mark.parametrize("field", ["first_name", "family_name", "country"])
@pytest.mark.parametrize("value", ["", "   ", None, 5])
def test_names_and_country_must_not_be_empty(room_types, field, value):
    booking, errors = run(room_types, **{field: value})
    assert booking is None
    assert fields(errors) == [field]
    assert "must not be empty" in errors[0].message


def test_text_over_100_characters_is_rejected(room_types):
    _, errors = run(room_types, first_name="x" * 101)
    assert errors[0].message == "First name must be at most 100 characters."
    booking, _ = run(room_types, first_name="x" * 100)
    assert booking is not None


def test_unknown_room_type_lists_the_valid_ones(room_types):
    _, errors = run(room_types, room_type="Penthouse")
    assert fields(errors) == ["room_type"]
    assert "Standard Single" in errors[0].message and "LOFT Suite" in errors[0].message


@pytest.mark.parametrize(
    "value", ["2026-02-30", "14-07-2026", "2026-7-14", "20260714", "2026-07-14T10:00:00", "1999-12-31",
             "2101-01-01", "", None, 20260714],
)
def test_invalid_check_in_dates(room_types, value):
    _, errors = run(room_types, check_in_date=value)
    assert fields(errors) == ["check_in_date"]


def test_check_in_date_boundaries_are_valid(room_types):
    assert run(room_types, check_in_date="2000-01-01")[1] == []
    assert run(room_types, check_in_date="2100-12-31")[1] == []


@pytest.mark.parametrize("value", [0, -1, 366, 2.5, "3", None, True])
def test_invalid_days_rented(room_types, value):
    _, errors = run(room_types, days_rented=value)
    assert fields(errors) == ["days_rented"]
    assert errors[0].message == "Days rented must be a whole number from 1 to 365."


@pytest.mark.parametrize("value", [1, 365, 3.0])
def test_valid_days_rented(room_types, value):
    booking, errors = run(room_types, days_rented=value)
    assert errors == [] and booking.days_rented == int(value)


def test_price_inside_the_band_is_accepted(room_types):
    booking, errors = run(room_types, price_dkk=6000.0)
    assert errors == [] and booking.price_dkk == Decimal("6000.00")


def test_price_outside_the_band_names_the_range(room_types):
    _, errors = run(room_types, room_type="Standard Single", check_in_date="2026-01-10", price_dkk=4500)
    assert fields(errors) == ["price_dkk"]
    assert "900.00–1,200.00 DKK per night for Standard Single in low season" in errors[0].message


@pytest.mark.parametrize("value", [0, -5, 1500.555, "1500", True, float("nan")])
def test_invalid_prices(room_types, value):
    _, errors = run(room_types, price_dkk=value)
    assert fields(errors) == ["price_dkk"]
    assert errors[0].message == "Price must be a positive amount in DKK with at most 2 decimals."


def test_null_price_means_standard_price(room_types):
    booking, errors = run(room_types, price_dkk=None)
    assert errors == [] and booking.price_dkk is None


def test_several_errors_are_reported_at_once(room_types):
    booking, errors = run(
        room_types, room_type="Penthouse", days_rented=0, first_name="", check_in_date="nope", price_dkk=-1
    )
    assert booking is None
    assert fields(errors) == ["first_name", "room_type", "check_in_date", "days_rented", "price_dkk"]


def test_band_check_is_skipped_when_other_fields_are_invalid(room_types):
    _, errors = run(room_types, days_rented=0, price_dkk=100)
    assert fields(errors) == ["days_rented"]


def test_missing_fields_are_errors(room_types):
    _, errors = validate_booking({}, room_types)
    assert fields(errors) == ["first_name", "family_name", "country", "room_type", "check_in_date", "days_rented"]
