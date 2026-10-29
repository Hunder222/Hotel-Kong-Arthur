"""ReviewService with in-memory fake ports (T064): no database."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from hotel_api.business.domain.models import Booking, GuestReview, NewReview, Season
from hotel_api.business.errors import NotFound, ValidationFailed
from hotel_api.business.services.review_service import ReviewService

pytestmark = pytest.mark.unit

NOW = datetime(2026, 10, 28, 12, 0)
BOOKING = Booking(2, "Zhang", "Rossi", "Mexico", "Grand Lit", date(2026, 1, 1), 3, Decimal("3360"))


class FakeRoomTypes:
    def __init__(self, room_types):
        self._r = room_types

    def list_all(self):
        return list(self._r)


class FakeBookings:
    def get(self, booking_id):
        return BOOKING if booking_id == BOOKING.id else None


class FakeReviews:
    def __init__(self):
        self.rows, self.calls, self.next_id = {}, [], 1

    def list(self):
        self.calls.append("list")
        return list(self.rows.values())

    def get(self, review_id):
        return self.rows.get(review_id)

    def add(self, review: NewReview):
        self.calls.append("add")
        stored = GuestReview(self.next_id, review.booking_id, review.room_type, review.stay_date, review.rating, NOW)
        self.rows[self.next_id] = stored
        self.next_id += 1
        return stored


@pytest.fixture()
def repo():
    return FakeReviews()


@pytest.fixture()
def service(repo, room_types):
    return ReviewService(repo, FakeBookings(), FakeRoomTypes(room_types))


def test_a_review_for_a_booking_copies_room_type_and_stay_date(service):
    review = service.create({"booking_id": 2, "rating": 5})
    assert (review.booking_id, review.room_type, review.stay_date, review.rating) == (
        2, "Grand Lit", date(2026, 1, 1), 5)
    assert review.season is Season.LOW and review.year == 2026


def test_a_review_without_a_booking_uses_the_given_room_type_and_date(service):
    review = service.create({"rating": 3, "room_type": "Suite", "stay_date": "2026-07-14"})
    assert (review.booking_id, review.room_type, review.season) == (None, "Suite", Season.HIGH)


def test_an_unknown_booking_is_a_booking_id_error(service, repo):
    with pytest.raises(ValidationFailed) as caught:
        service.create({"booking_id": 999, "rating": 4})
    assert [e.field for e in caught.value.field_errors] == ["booking_id"]
    assert "add" not in repo.calls


def test_booking_id_together_with_room_type_is_rejected(service, repo):
    with pytest.raises(ValidationFailed) as caught:
        service.create({"booking_id": 2, "room_type": "Suite", "rating": 4})
    assert [e.field for e in caught.value.field_errors] == ["room_type"]
    assert repo.rows == {}


@pytest.mark.parametrize("rating", [0, 6, -1, 2.5, "5", None])
def test_a_rating_outside_1_to_5_is_rejected(service, repo, rating):
    with pytest.raises(ValidationFailed) as caught:
        service.create({"booking_id": 2, "rating": rating})
    assert [e.field for e in caught.value.field_errors] == ["rating"]
    assert repo.calls == []


def test_get_returns_the_review_or_not_found(service):
    created = service.create({"booking_id": 2, "rating": 5})
    assert service.get(created.id) == created
    with pytest.raises(NotFound) as caught:
        service.get(42)
    assert caught.value.message == "Review 42 does not exist."


def test_list_returns_all_reviews(service, repo):
    created = service.create({"booking_id": 2, "rating": 5})
    assert service.list() == [created]
    assert "list" in repo.calls

