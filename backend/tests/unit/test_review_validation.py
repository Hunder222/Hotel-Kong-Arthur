from datetime import date
from decimal import Decimal

import pytest

from hotel_api.business.domain.models import Booking
from hotel_api.business.rules.review_validation import validate_review

pytestmark = pytest.mark.unit

BOOKING = Booking(2, "Zhang", "Rossi", "Mexico", "Grand Lit", date(2026, 1, 1), 3, Decimal("3360"))


def find(booking_id):
    return BOOKING if booking_id == 2 else None


def run(room_types, raw):
    return validate_review(raw, room_types, find)


def fields(errors):
    return [e.field for e in errors]


def test_review_for_a_booking_copies_room_type_and_stay_date(room_types):
    review, errors = run(room_types, {"booking_id": 2, "rating": 5})
    assert errors == []
    assert (review.booking_id, review.room_type, review.stay_date, review.rating) == (
        2, "Grand Lit", date(2026, 1, 1), 5)


def test_review_without_a_booking_needs_room_type_and_stay_date(room_types):
    review, errors = run(room_types, {"rating": 4, "room_type": "Suite", "stay_date": "2026-07-14"})
    assert errors == []
    assert review.booking_id is None and review.room_type == "Suite" and review.stay_date == date(2026, 7, 14)


@pytest.mark.parametrize("value", [0, 6, -1, 3.5, "4", None, True])
def test_rating_must_be_a_whole_number_from_1_to_5(room_types, value):
    _, errors = run(room_types, {"booking_id": 2, "rating": value})
    assert fields(errors) == ["rating"]


@pytest.mark.parametrize("value", [1, 5, 3.0])
def test_valid_ratings(room_types, value):
    review, errors = run(room_types, {"booking_id": 2, "rating": value})
    assert errors == [] and review.rating == int(value)


def test_unknown_booking_is_a_booking_id_error(room_types):
    _, errors = run(room_types, {"booking_id": 999, "rating": 3})
    assert fields(errors) == ["booking_id"]
    assert errors[0].message == "Booking 999 does not exist."


def test_non_numeric_booking_id(room_types):
    _, errors = run(room_types, {"booking_id": "abc", "rating": 3})
    assert fields(errors) == ["booking_id"]


def test_room_type_and_stay_date_must_be_omitted_with_a_booking(room_types):
    _, errors = run(room_types, {"booking_id": 2, "rating": 3, "room_type": "Suite", "stay_date": "2026-07-14"})
    assert fields(errors) == ["room_type", "stay_date"]
    assert "omitted when booking_id is given" in errors[0].message


def test_without_a_booking_both_fields_are_required(room_types):
    _, errors = run(room_types, {"rating": 3})
    assert fields(errors) == ["room_type", "stay_date"]
    _, errors = run(room_types, {"rating": 3, "room_type": "Suite"})
    assert fields(errors) == ["stay_date"]


def test_same_rules_as_booking_for_room_type_and_date(room_types):
    _, errors = run(room_types, {"rating": 3, "room_type": "Penthouse", "stay_date": "2026-02-30"})
    assert fields(errors) == ["room_type", "stay_date"]


def test_several_errors_at_once(room_types):
    _, errors = run(room_types, {"rating": 9, "booking_id": 999})
    assert fields(errors) == ["rating", "booking_id"]
