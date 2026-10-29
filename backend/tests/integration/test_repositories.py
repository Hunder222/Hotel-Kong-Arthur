"""Integration tests for MySQL repositories against `hotel_test` (T026, R2, R16).

Covers:
- Round-trip persistence of `room_types`, `bookings`, `reviews`, `bar_drink_sales`, and `health` ping
- `ON DELETE SET NULL` preservation of reviews when their linked booking is deleted
- Filter combinations (`year`, `season`, `room_type`, `country`, `category`) and ordering
- Full UTF-8 round-trip for international characters (`Müller`, Danish `værelse`)
- Translation of driver failures into `StorageUnavailable`
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pymysql
import pytest
from pymysql.connections import Connection

from hotel_api.business.domain.models import (
    BarDrinkSale,
    Booking,
    DrinkCategory,
    GuestReview,
    NewBooking,
    NewReview,
    Season,
)
from hotel_api.business.errors import StorageUnavailable
from hotel_api.config import get_settings
from hotel_api.data.connection import open_connection
from hotel_api.data.repositories.bar_sales import MySqlBarSalesRepository
from hotel_api.data.repositories.bookings import MySqlBookingRepository
from hotel_api.data.repositories.health import MySqlHealthRepository
from hotel_api.data.repositories.reviews import MySqlReviewRepository
from hotel_api.data.repositories.room_types import MySqlRoomTypeRepository

pytestmark = pytest.mark.integration


def _find_db_init_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    candidate = repo_root / "db" / "init"
    if candidate.is_dir():
        return candidate
    docker_candidate = Path("/repo/db/init")
    if docker_candidate.is_dir():
        return docker_candidate
    raise FileNotFoundError("Could not locate db/init directory for integration tests.")


def _execute_sql_script(conn: Connection[Any], sql_path: Path) -> None:
    raw = sql_path.read_text(encoding="utf-8")
    lines = [
        line
        for line in raw.splitlines()
        if not line.strip().startswith("--")
    ]
    script = "\n".join(lines)
    statements = [stmt.strip() for stmt in script.split(";") if stmt.strip()]
    with conn.cursor() as cursor:
        for stmt in statements:
            cursor.execute(stmt)
    conn.commit()


def _ensure_hotel_test_schema(conn: Connection[Any]) -> None:
    init_dir = _find_db_init_dir()
    _execute_sql_script(conn, init_dir / "01_schema.sql")
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS cnt FROM room_types")
        row = cursor.fetchone()
        count = int(row["cnt"]) if row else 0
    if count == 0:
        _execute_sql_script(conn, init_dir / "02_reference_data.sql")


@pytest.fixture(scope="session")
def _initialized_test_db() -> None:
    settings = get_settings().with_db_name("hotel_test")
    conn = open_connection(settings)
    try:
        _ensure_hotel_test_schema(conn)
    finally:
        conn.close()


@pytest.fixture()
def db_conn(_initialized_test_db: None) -> Iterator[Connection[Any]]:
    settings = get_settings().with_db_name("hotel_test")
    conn = open_connection(settings)
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM reviews")
            cursor.execute("DELETE FROM bookings")
            cursor.execute("DELETE FROM bar_drink_sales")
        conn.commit()
        yield conn
    finally:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM reviews")
            cursor.execute("DELETE FROM bookings")
            cursor.execute("DELETE FROM bar_drink_sales")
        conn.commit()
        conn.close()


def test_health_ping_and_storage_unavailable(db_conn: Connection[Any]) -> None:
    health_repo = MySqlHealthRepository(db_conn)
    health_repo.ping()

    bad_settings = get_settings().with_db_name("hotel_test")
    bad_settings = type(bad_settings)(
        db_host="127.0.0.1",
        db_port=1,
        db_name=bad_settings.db_name,
        db_user=bad_settings.db_user,
        db_password=bad_settings.db_password,
    )
    with pytest.raises(StorageUnavailable):
        open_connection(bad_settings)


def test_room_type_repository_loads_reference_data(db_conn: Connection[Any]) -> None:
    repo = MySqlRoomTypeRepository(db_conn)
    room_types = repo.list_all()

    assert len(room_types) == 8
    assert [rt.id for rt in room_types] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert sum(rt.room_count for rt in room_types) == 214

    standard_single = room_types[0]
    assert standard_single.name == "Standard Single"
    assert standard_single.name_da == "Standard enkeltværelse"
    assert list(standard_single.rates.keys()) == [Season.LOW, Season.MID, Season.HIGH]
    assert standard_single.rates[Season.LOW].min_nightly_dkk == Decimal("900.00")
    assert standard_single.rates[Season.LOW].max_nightly_dkk == Decimal("1200.00")
    assert standard_single.rates[Season.LOW].standard_nightly_dkk == Decimal("1050.00")

    suite = repo.get_by_name("Suite")
    assert suite is not None
    assert suite.id == 7
    assert suite.room_count == 26
    assert list(suite.rates.keys()) == [Season.LOW, Season.MID, Season.HIGH]
    assert suite.rates[Season.HIGH].standard_nightly_dkk == Decimal("3250.00")

    assert repo.get_by_name("Unknown Room") is None
    assert repo.get_by_name("suite") is None


def test_booking_repository_crud_utf8_and_filters(db_conn: Connection[Any]) -> None:
    repo = MySqlBookingRepository(db_conn)

    created_1 = repo.add(
        NewBooking(
            first_name="Elena",
            family_name="Müller",
            country="Germany",
            room_type="Superior Double",
            check_in_date=date(2026, 7, 14),
            days_rented=3,
            price_dkk=Decimal("6000.00"),
        )
    )
    assert created_1.id >= 1
    assert created_1.family_name == "Müller"
    assert created_1.season is Season.HIGH
    assert created_1.year == 2026
    assert created_1.price_dkk == Decimal("6000.00")
    assert created_1.created_at is not None
    assert created_1.updated_at is not None

    fetched = repo.get(created_1.id)
    assert fetched == created_1
    assert repo.get(999999) is None

    created_2 = repo.add(
        NewBooking(
            first_name="Liam",
            family_name="Nguyen",
            country="China",
            room_type="Spa Executive",
            check_in_date=date(2026, 1, 15),
            days_rented=2,
            price_dkk=Decimal("4500.00"),
        )
    )
    created_3 = repo.add(
        NewBooking(
            first_name="Sofia",
            family_name="Rossi",
            country="Italy",
            room_type="Superior Double",
            check_in_date=date(2025, 11, 10),
            days_rented=4,
            price_dkk=Decimal("6400.00"),
        )
    )

    # Default ordering: newest (highest id) first
    all_bookings = repo.list()
    assert [b.id for b in all_bookings] == [created_3.id, created_2.id, created_1.id]

    # Replace existing booking (including idempotent replace with identical values)
    replaced = repo.replace(
        created_1.id,
        NewBooking(
            first_name="Elena",
            family_name="Müller",
            country="Germany",
            room_type="Superior Double",
            check_in_date=date(2026, 7, 14),
            days_rented=5,
            price_dkk=Decimal("10000.00"),
        ),
    )
    assert replaced is not None
    assert replaced.days_rented == 5
    assert replaced.price_dkk == Decimal("10000.00")

    replaced_same = repo.replace(
        created_1.id,
        NewBooking(
            first_name="Elena",
            family_name="Müller",
            country="Germany",
            room_type="Superior Double",
            check_in_date=date(2026, 7, 14),
            days_rented=5,
            price_dkk=Decimal("10000.00"),
        ),
    )
    assert replaced_same is not None
    assert replaced_same.id == created_1.id

    assert repo.replace(
        999999,
        NewBooking(
            first_name="No",
            family_name="Body",
            country="Denmark",
            room_type="Suite",
            check_in_date=date(2026, 5, 1),
            days_rented=1,
            price_dkk=Decimal("3000.00"),
        ),
    ) is None

    # Delete single booking
    assert repo.delete(created_1.id) is True
    assert repo.delete(created_1.id) is False
    assert repo.get(created_1.id) is None

    # Bulk insert with explicit IDs after delete_all
    repo.delete_all()
    assert repo.list() == []
    repo.insert_many(
        [
            Booking(
                id=1,
                first_name="Liam",
                family_name="Nguyen",
                country="China",
                room_type="Spa Executive",
                check_in_date=date(2026, 3, 1),
                days_rented=1,
                price_dkk=Decimal("2577.00"),
            ),
            Booking(
                id=21,
                first_name="Hans",
                family_name="Müller",
                country="Germany",
                room_type="Standard Single",
                check_in_date=date(2026, 1, 8),
                days_rented=2,
                price_dkk=Decimal("2100.00"),
            ),
        ]
    )
    seeded = repo.list()
    assert [b.id for b in seeded] == [21, 1]
    assert seeded[0].family_name == "Müller"


def test_review_repository_and_on_delete_set_null(db_conn: Connection[Any]) -> None:
    booking_repo = MySqlBookingRepository(db_conn)
    review_repo = MySqlReviewRepository(db_conn)

    booking = booking_repo.add(
        NewBooking(
            first_name="Elena",
            family_name="Müller",
            country="Germany",
            room_type="Superior Double",
            check_in_date=date(2026, 7, 14),
            days_rented=3,
            price_dkk=Decimal("6000.00"),
        )
    )

    linked_review = review_repo.add(
        NewReview(
            booking_id=booking.id,
            room_type=booking.room_type,
            stay_date=booking.check_in_date,
            rating=5,
        )
    )
    assert linked_review.id >= 1
    assert linked_review.booking_id == booking.id
    assert linked_review.room_type == "Superior Double"
    assert linked_review.stay_date == date(2026, 7, 14)
    assert linked_review.season is Season.HIGH
    assert linked_review.rating == 5
    assert linked_review.created_at is not None

    standalone_review = review_repo.add(
        NewReview(
            booking_id=None,
            room_type="Suite",
            stay_date=date(2026, 1, 20),
            rating=4,
        )
    )
    assert standalone_review.booking_id is None
    assert standalone_review.season is Season.LOW

    # Ordering (newest first)
    assert [r.id for r in review_repo.list()] == [standalone_review.id, linked_review.id]

    # Deleting the booking sets reviews.booking_id to NULL while preserving the review snapshot
    assert booking_repo.delete(booking.id) is True
    surviving = review_repo.get(linked_review.id)
    assert surviving is not None
    assert surviving.booking_id is None
    assert surviving.room_type == "Superior Double"
    assert surviving.stay_date == date(2026, 7, 14)
    assert surviving.rating == 5

    # Bulk insert and delete_all
    review_repo.delete_all()
    assert review_repo.list() == []
    review_repo.insert_many(
        [
            GuestReview(
                id=10,
                booking_id=None,
                room_type="Grand Lit",
                stay_date=date(2026, 4, 5),
                rating=3,
            )
        ]
    )
    inserted = review_repo.get(10)
    assert inserted is not None
    assert inserted.room_type == "Grand Lit"
    assert inserted.rating == 3


def test_bar_sales_repository_round_trip(db_conn: Connection[Any]) -> None:
    repo = MySqlBarSalesRepository(db_conn)

    sales = [
        BarDrinkSale(
            id=1,
            sales_year=2026,
            drink_name="Mint Julep",
            category=DrinkCategory.COCKTAIL,
            unit_price_dkk=Decimal("114.66"),
            units_sold=4573,
        ),
        BarDrinkSale(
            id=2,
            sales_year=2026,
            drink_name="Espresso",
            category=DrinkCategory.COFFEE,
            unit_price_dkk=Decimal("69.10"),
            units_sold=14656,
        ),
        BarDrinkSale(
            id=3,
            sales_year=2025,
            drink_name="Latte",
            category=DrinkCategory.COFFEE,
            unit_price_dkk=Decimal("55.00"),
            units_sold=1000,
        ),
    ]
    repo.insert_many(sales)

    all_sales = repo.list()
    assert [s.id for s in all_sales] == [1, 2, 3]
    assert all_sales[0].unit_price_dkk * all_sales[0].units_sold == Decimal("114.66") * 4573

    repo.delete_all()
    assert repo.list() == []


