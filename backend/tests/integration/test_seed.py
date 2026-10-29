"""Integration tests for the sample data seed command against `hotel_test` (T041, R13, FR-004).

Verifies:
- Running the seed twice produces identical counts (1000 bookings, 500 reviews, 30 drink sales),
  explicit IDs (1..1000, 1..500, 1..30), and totals.
- Booking 1 is Liam Nguyen, China, Spa Executive, 2026-03-01, `mid`, 1 night, 2577.00 DKK.
- Booking 21 has `family_name == "Müller"` and `check_in_date == date(2026, 1, 8)`.
- A failing seed (bad CSV or mid-transaction failure after `DELETE`) rolls back and leaves existing
  rows in `hotel_test` intact.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from pymysql.connections import Connection

from hotel_api.business.domain.models import BarDrinkSale, DrinkCategory, Season
from hotel_api.business.errors import StorageUnavailable, ValidationFailed
from hotel_api.business.services.sample_data_service import SampleDataService
from hotel_api.config import Settings
from hotel_api.data.connection import connection_scope, open_connection
from hotel_api.data.repositories.bar_sales import MySqlBarSalesRepository
from hotel_api.data.repositories.bookings import MySqlBookingRepository
from hotel_api.data.repositories.reviews import MySqlReviewRepository
from hotel_api.data.repositories.room_types import MySqlRoomTypeRepository
from hotel_api.presentation.cli.seed import main as seed_main, parse_bookings_csv, parse_drinks_csv, run_seed

pytestmark = pytest.mark.integration


def _snapshot(settings: Settings) -> dict[str, Any]:
    conn = open_connection(settings)
    try:
        bookings = MySqlBookingRepository(conn).list()
        reviews = MySqlReviewRepository(conn).list()
        drinks = MySqlBarSalesRepository(conn).list()
    finally:
        conn.close()

    return {
        "booking_count": len(bookings),
        "booking_ids": [b.id for b in bookings],
        "booking_revenue": sum((b.price_dkk for b in bookings), Decimal("0.00")),
        "booking_nights": sum(b.days_rented for b in bookings),
        "review_count": len(reviews),
        "review_ids": [r.id for r in reviews],
        "review_ratings": [(r.id, r.booking_id, r.room_type, r.stay_date, r.rating) for r in reviews],
        "drink_count": len(drinks),
        "drink_ids": [d.id for d in drinks],
        "drink_units": sum(d.units_sold for d in drinks),
        "drink_revenue": sum((d.unit_price_dkk * d.units_sold for d in drinks), Decimal("0.00")),
    }


def test_seed_is_idempotent_and_matches_golden_records(
    test_settings: Settings,
    clean_db: Connection[Any],
    capsys: pytest.CaptureFixture[str],
) -> None:
    seed_main(settings=test_settings)
    first_out = capsys.readouterr().out.strip()
    assert first_out == "1000 bookings, 500 reviews, 30 drink sales"
    first_state = _snapshot(test_settings)

    seed_main(settings=test_settings)
    second_out = capsys.readouterr().out.strip()
    assert second_out == "1000 bookings, 500 reviews, 30 drink sales"
    second_state = _snapshot(test_settings)

    assert first_state == second_state
    assert first_state["booking_count"] == 1000
    assert first_state["review_count"] == 500
    assert first_state["drink_count"] == 30

    assert first_state["booking_ids"] == list(range(1000, 0, -1))
    assert first_state["review_ids"] == list(range(500, 0, -1))
    assert first_state["drink_ids"] == list(range(1, 31))

    assert first_state["booking_revenue"] == Decimal("11234034.00")
    assert first_state["booking_nights"] == 5379
    assert first_state["drink_units"] == 179958
    assert first_state["drink_revenue"] == Decimal("13448640.34")

    conn = open_connection(test_settings)
    try:
        bookings_repo = MySqlBookingRepository(conn)
        b1 = bookings_repo.get(1)
        b21 = bookings_repo.get(21)
    finally:
        conn.close()

    assert b1 is not None
    assert b1.id == 1
    assert b1.first_name == "Liam"
    assert b1.family_name == "Nguyen"
    assert b1.country == "China"
    assert b1.room_type == "Spa Executive"
    assert b1.check_in_date == date(2026, 3, 1)
    assert b1.season is Season.MID
    assert b1.days_rented == 1
    assert b1.price_dkk == Decimal("2577.00")

    assert b21 is not None
    assert b21.id == 21
    assert b21.first_name == "Elena"
    assert b21.family_name == "Müller"
    assert b21.country == "India"
    assert b21.room_type == "Superior Double"
    assert b21.check_in_date == date(2026, 1, 8)
    assert b21.season is Season.LOW
    assert b21.days_rented == 3
    assert b21.price_dkk == Decimal("4389.00")


def test_failing_seed_leaves_existing_rows_intact(
    test_settings: Settings,
    clean_db: Connection[Any],
    tmp_path: Path,
) -> None:
    # Seed valid initial data first
    run_seed(settings=test_settings)
    baseline = _snapshot(test_settings)
    assert baseline["booking_count"] == 1000

    # 1. Failing seed due to an invalid price in a CSV file leaves existing DB rows untouched
    bad_bookings_csv = tmp_path / "bad_bookings.csv"
    bad_bookings_csv.write_text(
        "First Name,Family Name,Country,Room Type,Days Rented,Season,Price\n"
        "Ann,Lee,Japan,Standard Single,3,low,4500\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationFailed):
        run_seed(settings=test_settings, bookings_csv=bad_bookings_csv)

    assert _snapshot(test_settings) == baseline

    # 2. Failing seed mid-transaction (after DELETE FROM reviews and DELETE FROM bookings)
    # rolls back the MySQL transaction so all 1000 bookings, 500 reviews, and 30 drinks remain intact.
    class FailingBarSalesRepository(MySqlBarSalesRepository):
        def insert_many(self, sales: Any) -> None:
            raise StorageUnavailable("Simulated database failure after deleting old rows.")

    from hotel_api.presentation.cli.seed import BOOKINGS_FILENAME, DRINKS_FILENAME, default_sample_data_dir

    data_dir = default_sample_data_dir()
    booking_rows = parse_bookings_csv(data_dir / BOOKINGS_FILENAME)
    drink_rows = parse_drinks_csv(data_dir / DRINKS_FILENAME)

    with pytest.raises(StorageUnavailable):
        with connection_scope(test_settings) as conn:
            svc = SampleDataService(
                room_types=MySqlRoomTypeRepository(conn),
                bookings=MySqlBookingRepository(conn),
                reviews=MySqlReviewRepository(conn),
                bar_sales=FailingBarSalesRepository(conn),
            )
            svc.replace_with_sample_data(booking_rows, None, drink_rows)

    assert _snapshot(test_settings) == baseline
    conn = open_connection(test_settings)
    try:
        b21 = MySqlBookingRepository(conn).get(21)
        drinks = [d for d in MySqlBarSalesRepository(conn).list() if d.category is DrinkCategory.COFFEE]
    finally:
        conn.close()
    assert b21 is not None and b21.family_name == "Müller"
    assert len(drinks) == 10

