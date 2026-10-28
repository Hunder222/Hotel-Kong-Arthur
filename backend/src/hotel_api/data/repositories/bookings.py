"""MySQL repository for room bookings (T022, data-model.md §3.1)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Any

from pymysql.connections import Connection

from hotel_api.business.domain.models import Booking, NewBooking, Season
from hotel_api.business.rules.seasons import season_of_month
from hotel_api.data.connection import db_cursor

_SEASON_MONTHS: dict[Season, tuple[int, ...]] = {
    season: tuple(month for month in range(1, 13) if season_of_month(month) is season)
    for season in Season
}


def _row_to_booking(row: dict[str, Any]) -> Booking:
    return Booking(
        id=int(row["id"]),
        first_name=str(row["first_name"]),
        family_name=str(row["family_name"]),
        country=str(row["country"]),
        room_type=str(row["room_type"]),
        check_in_date=row["check_in_date"],
        days_rented=int(row["days_rented"]),
        price_dkk=Decimal(row["price_dkk"]),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


class MySqlBookingRepository:
    """Stores and queries `bookings` using parameterised SQL."""

    def __init__(self, conn: Connection[Any]) -> None:
        self._conn = conn

    def _resolve_room_type_id(self, cursor: Any, room_type_name: str) -> int:
        cursor.execute(
            "SELECT id, name FROM room_types WHERE name = %s",
            (room_type_name,),
        )
        row = cursor.fetchone()
        if row is None or str(row["name"]) != room_type_name:
            raise ValueError(f"Unknown room type: {room_type_name!r}")
        return int(row["id"])

    def _room_type_id_map(self, cursor: Any) -> dict[str, int]:
        cursor.execute("SELECT id, name FROM room_types")
        return {str(row["name"]): int(row["id"]) for row in cursor.fetchall()}

    def list(
        self,
        year: int | None = None,
        season: Season | None = None,
        room_type: str | None = None,
        country: str | None = None,
    ) -> list[Booking]:
        """Return matching bookings ordered by `id DESC` (newest first)."""
        clauses: list[str] = []
        params: list[Any] = []

        if year is not None:
            clauses.append("b.check_in_date >= %s AND b.check_in_date < %s")
            params.extend([date(year, 1, 1), date(year + 1, 1, 1)])

        if season is not None:
            months = _SEASON_MONTHS[Season(season)]
            placeholders = ", ".join(["%s"] * len(months))
            clauses.append(f"MONTH(b.check_in_date) IN ({placeholders})")
            params.extend(months)

        if room_type is not None:
            clauses.append("rt.name = %s")
            params.append(room_type)

        if country is not None:
            clauses.append("b.country = %s")
            params.append(country)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT
                b.id,
                b.first_name,
                b.family_name,
                b.country,
                rt.name AS room_type,
                b.check_in_date,
                b.days_rented,
                b.price_dkk,
                b.created_at,
                b.updated_at
            FROM bookings b
            JOIN room_types rt ON rt.id = b.room_type_id
            {where_sql}
            ORDER BY b.id DESC
        """
        with db_cursor(self._conn) as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
        return [_row_to_booking(row) for row in rows]

    def get(self, booking_id: int) -> Booking | None:
        """Return the booking with `booking_id`, or `None` if it does not exist."""
        sql = """
            SELECT
                b.id,
                b.first_name,
                b.family_name,
                b.country,
                rt.name AS room_type,
                b.check_in_date,
                b.days_rented,
                b.price_dkk,
                b.created_at,
                b.updated_at
            FROM bookings b
            JOIN room_types rt ON rt.id = b.room_type_id
            WHERE b.id = %s
        """
        with db_cursor(self._conn) as cursor:
            cursor.execute(sql, (booking_id,))
            row = cursor.fetchone()
        return _row_to_booking(row) if row is not None else None

    def add(self, booking: NewBooking) -> Booking:
        """Insert a booking whose `price_dkk` is already set and read the stored row back."""
        if booking.price_dkk is None:
            raise ValueError("NewBooking.price_dkk must be set before calling repository.add().")

        with db_cursor(self._conn) as cursor:
            room_type_id = self._resolve_room_type_id(cursor, booking.room_type)
            cursor.execute(
                """
                INSERT INTO bookings (
                    first_name,
                    family_name,
                    country,
                    room_type_id,
                    check_in_date,
                    days_rented,
                    price_dkk
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    booking.first_name,
                    booking.family_name,
                    booking.country,
                    room_type_id,
                    booking.check_in_date,
                    booking.days_rented,
                    booking.price_dkk,
                ),
            )
            booking_id = int(cursor.lastrowid)

        stored = self.get(booking_id)
        assert stored is not None
        return stored

    def replace(self, booking_id: int, booking: NewBooking) -> Booking | None:
        """Replace editable fields of `booking_id`; return the updated row, or `None` if not found."""
        if booking.price_dkk is None:
            raise ValueError("NewBooking.price_dkk must be set before calling repository.replace().")

        with db_cursor(self._conn) as cursor:
            room_type_id = self._resolve_room_type_id(cursor, booking.room_type)
            cursor.execute(
                """
                UPDATE bookings
                SET
                    first_name = %s,
                    family_name = %s,
                    country = %s,
                    room_type_id = %s,
                    check_in_date = %s,
                    days_rented = %s,
                    price_dkk = %s
                WHERE id = %s
                """,
                (
                    booking.first_name,
                    booking.family_name,
                    booking.country,
                    room_type_id,
                    booking.check_in_date,
                    booking.days_rented,
                    booking.price_dkk,
                    booking_id,
                ),
            )

        return self.get(booking_id)

    def delete(self, booking_id: int) -> bool:
        """Delete `booking_id`; return `True` if a row was removed."""
        with db_cursor(self._conn) as cursor:
            cursor.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
            return cursor.rowcount > 0

    def delete_all(self) -> None:
        """Delete all bookings."""
        with db_cursor(self._conn) as cursor:
            cursor.execute("DELETE FROM bookings")

    def insert_many(self, bookings: Sequence[Booking]) -> None:
        """Bulk insert bookings with explicit IDs (used by the seed command)."""
        if not bookings:
            return
        with db_cursor(self._conn) as cursor:
            rt_map = self._room_type_id_map(cursor)
            params = [
                (
                    b.id,
                    b.first_name,
                    b.family_name,
                    b.country,
                    rt_map[b.room_type],
                    b.check_in_date,
                    b.days_rented,
                    b.price_dkk,
                )
                for b in bookings
            ]
            cursor.executemany(
                """
                INSERT INTO bookings (
                    id,
                    first_name,
                    family_name,
                    country,
                    room_type_id,
                    check_in_date,
                    days_rented,
                    price_dkk
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                params,
            )


BookingRepo = MySqlBookingRepository

