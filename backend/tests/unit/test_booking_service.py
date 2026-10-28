"""BookingService with in-memory fake ports (T042): US1 scenarios 1-4, no database."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal

import pytest

from hotel_api.business.domain.models import Booking, NewBooking, Season
from hotel_api.business.errors import NotFound, ValidationFailed
from hotel_api.business.services.booking_service import BookingService

pytestmark = pytest.mark.unit

NOW = datetime(2026, 10, 28, 12, 0)

QUICKSTART = {
    "first_name": "Elena",
    "family_name": "Müller",
    "country": "Germany",
    "room_type": "Superior Double",
    "check_in_date": "2026-07-14",
    "days_rented": 3,
}


class FakeRoomTypes:
    def __init__(self, room_types):
        self._room_types = room_types

    def list_all(self):
        return list(self._room_types)

    def get_by_name(self, name):
        return next((r for r in self._room_types if r.name == name), None)


class FakeBookings:
    def __init__(self):
        self.rows: dict[int, Booking] = {}
        self.calls: list[str] = []
        self._next_id = 1

    def list(self, year=None, season=None, room_type=None, country=None):
        self.calls.append("list")
        self.last_filters = (year, season, room_type, country)
        return sorted(self.rows.values(), key=lambda b: -b.id)

    def get(self, booking_id):
        self.calls.append("get")
        return self.rows.get(booking_id)

    def add(self, booking: NewBooking) -> Booking:
        self.calls.append("add")
        stored = self._store(self._next_id, booking)
        self._next_id += 1
        return stored

    def replace(self, booking_id, booking: NewBooking):
        self.calls.append("replace")
        if booking_id not in self.rows:
            return None
        return self._store(booking_id, booking)

    def delete(self, booking_id) -> bool:
        self.calls.append("delete")
        return self.rows.pop(booking_id, None) is not None

    def _store(self, booking_id: int, b: NewBooking) -> Booking:
        stored = Booking(booking_id, b.first_name, b.family_name, b.country, b.room_type,
                         b.check_in_date, b.days_rented, b.price_dkk, NOW, NOW)
        self.rows[booking_id] = stored
        return stored


@pytest.fixture()
def repo():
    return FakeBookings()


@pytest.fixture()
def service(repo, room_types):
    return BookingService(repo, FakeRoomTypes(room_types))


def test_create_without_price_uses_the_standard_price(service):
    booking = service.create(QUICKSTART)
    assert booking.price_dkk == Decimal("6000.00")  # high-season standard 2000 x 3
    assert booking.season is Season.HIGH and booking.year == 2026
    assert booking.id == 1 and booking.family_name == "Müller"


def test_create_with_null_price_uses_the_standard_price(service):
    assert service.create({**QUICKSTART, "price_dkk": None}).price_dkk == Decimal("6000.00")


def test_create_with_manual_price_inside_the_band_keeps_it(service):
    booking = service.create({**QUICKSTART, "price_dkk": 5700})
    assert booking.price_dkk == Decimal("5700.00")


def test_manual_price_outside_the_band_is_rejected_and_nothing_is_stored(service, repo):
    with pytest.raises(ValidationFailed) as caught:
        service.create({**QUICKSTART, "price_dkk": 1000})
    assert [e.field for e in caught.value.field_errors] == ["price_dkk"]
    assert "outside" in caught.value.field_errors[0].message
    assert "add" not in repo.calls and repo.rows == {}


def test_failed_validation_lists_every_field_and_does_not_touch_the_repository(service, repo):
    bad = {**QUICKSTART, "room_type": "Penthouse", "days_rented": 0, "first_name": " "}
    with pytest.raises(ValidationFailed) as caught:
        service.create(bad)
    assert [e.field for e in caught.value.field_errors] == ["first_name", "room_type", "days_rented"]
    assert repo.calls == []


def test_replace_recalculates_the_price_when_it_is_omitted(service):
    created = service.create(QUICKSTART)
    updated = service.replace(created.id, {**QUICKSTART, "days_rented": 5})
    assert updated.price_dkk == Decimal("10000.00") and updated.days_rented == 5


def test_replace_follows_a_changed_room_type_and_season(service):
    created = service.create(QUICKSTART)
    updated = service.replace(created.id, {**QUICKSTART, "room_type": "Suite", "check_in_date": "2026-01-10"})
    assert updated.price_dkk == Decimal("8250.00")  # low-season Suite 2750 x 3
    assert updated.season is Season.LOW


def test_replace_keeps_a_valid_manual_price(service):
    created = service.create(QUICKSTART)
    assert service.replace(created.id, {**QUICKSTART, "price_dkk": 5700}).price_dkk == Decimal("5700.00")


def test_replace_with_invalid_data_changes_nothing(service, repo):
    created = service.create(QUICKSTART)
    with pytest.raises(ValidationFailed):
        service.replace(created.id, {**QUICKSTART, "days_rented": -1})
    assert "replace" not in repo.calls
    assert repo.rows[created.id] == created


def test_unknown_id_is_not_found_for_get_replace_and_delete(service, repo):
    for action in (lambda: service.get(42), lambda: service.replace(42, QUICKSTART), lambda: service.delete(42)):
        with pytest.raises(NotFound) as caught:
            action()
        assert caught.value.message == "Booking 42 does not exist."
    assert "add" not in repo.calls


def test_replace_of_an_unknown_id_is_not_found_even_if_the_body_is_invalid(service):
    with pytest.raises(NotFound):
        service.replace(42, {"first_name": ""})


def test_replace_when_the_row_vanishes_between_lookup_and_write(service, repo):
    created = service.create(QUICKSTART)
    original_replace = repo.replace
    repo.replace = lambda i, b: (repo.rows.pop(i), original_replace(i, b))[1]
    with pytest.raises(NotFound):
        service.replace(created.id, QUICKSTART)


def test_delete_removes_the_booking(service, repo):
    created = service.create(QUICKSTART)
    service.delete(created.id)
    assert repo.rows == {}
    with pytest.raises(NotFound):
        service.get(created.id)


def test_list_passes_the_filters_to_the_repository(service, repo):
    service.create(QUICKSTART)
    result = service.list(year=2026, season=Season.HIGH, room_type="Suite", country="Germany")
    assert repo.last_filters == (2026, Season.HIGH, "Suite", "Germany")
    assert len(result) == 1
    assert service.list() and repo.last_filters == (None, None, None, None)
