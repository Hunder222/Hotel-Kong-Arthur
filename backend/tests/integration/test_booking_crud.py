"""BookingService over the real repositories and MySQL (T044, F1, FR-005).

Each `connection_scope` block stands for one request: one connection and one transaction that is
committed on success and rolled back on error. A later block therefore sees only committed data.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from hotel_api.business.domain.models import NewReview
from hotel_api.business.errors import NotFound, ValidationFailed
from hotel_api.business.services.booking_service import BookingService
from hotel_api.data.connection import connection_scope
from hotel_api.data.repositories.bookings import MySqlBookingRepository
from hotel_api.data.repositories.reviews import MySqlReviewRepository
from hotel_api.data.repositories.room_types import MySqlRoomTypeRepository

pytestmark = pytest.mark.integration

ELENA = {
    "first_name": "Elena",
    "family_name": "Müller",
    "country": "Germany",
    "room_type": "Superior Double",
    "check_in_date": "2026-07-14",
    "days_rented": 3,
}


def service(conn) -> BookingService:
    return BookingService(MySqlBookingRepository(conn), MySqlRoomTypeRepository(conn))


def count(conn, table: str) -> int:
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) AS n FROM {table}")
        return cursor.fetchone()["n"]


def test_a_created_booking_is_visible_on_the_next_request(test_settings, clean_db):
    with connection_scope(test_settings) as conn:
        created = service(conn).create(ELENA)
    assert created.price_dkk == Decimal("6000.00") and created.id >= 1

    with connection_scope(test_settings) as conn:
        fetched = service(conn).get(created.id)
        listed = service(conn).list(year=2026)
    assert fetched.family_name == "Müller"
    assert (fetched.season.value, fetched.year) == ("high", 2026)
    assert [b.id for b in listed] == [created.id]


def test_an_edit_is_persisted_with_the_recalculated_price(test_settings, clean_db):
    with connection_scope(test_settings) as conn:
        created = service(conn).create(ELENA)
    with connection_scope(test_settings) as conn:
        service(conn).replace(created.id, {**ELENA, "days_rented": 5})
    with connection_scope(test_settings) as conn:
        edited = service(conn).get(created.id)
    assert (edited.days_rented, edited.price_dkk) == (5, Decimal("10000.00"))
    assert edited.updated_at >= edited.created_at


def test_an_invalid_create_leaves_the_table_unchanged(test_settings, clean_db):
    with connection_scope(test_settings) as conn:
        service(conn).create(ELENA)
    for bad in ({**ELENA, "room_type": "Penthouse", "days_rented": 0}, {**ELENA, "price_dkk": 1000}):
        with pytest.raises(ValidationFailed):
            with connection_scope(test_settings) as conn:
                service(conn).create(bad)
    assert count(clean_db, "bookings") == 1


def test_an_unknown_id_is_not_found_and_changes_nothing(test_settings, clean_db):
    with connection_scope(test_settings) as conn:
        service(conn).create(ELENA)
    for action in (lambda s: s.get(999), lambda s: s.replace(999, ELENA), lambda s: s.delete(999)):
        with pytest.raises(NotFound):
            with connection_scope(test_settings) as conn:
                action(service(conn))
    assert count(clean_db, "bookings") == 1


def test_an_error_after_a_write_rolls_the_whole_request_back(test_settings, clean_db):
    with pytest.raises(RuntimeError):
        with connection_scope(test_settings) as conn:
            service(conn).create(ELENA)
            raise RuntimeError("boom after the insert")
    assert count(clean_db, "bookings") == 0


def test_deleting_a_booking_keeps_its_review_with_a_null_booking_id(test_settings, clean_db):
    with connection_scope(test_settings) as conn:
        booking = service(conn).create(ELENA)
        review = MySqlReviewRepository(conn).add(
            NewReview(rating=5, room_type=booking.room_type, stay_date=booking.check_in_date, booking_id=booking.id)
        )
    assert review.booking_id == booking.id

    with connection_scope(test_settings) as conn:
        service(conn).delete(booking.id)

    with connection_scope(test_settings) as conn:
        assert MySqlBookingRepository(conn).get(booking.id) is None
        kept = MySqlReviewRepository(conn).get(review.id)
    assert kept is not None and kept.booking_id is None
    assert (kept.room_type, kept.stay_date, kept.rating) == ("Superior Double", booking.check_in_date, 5)
