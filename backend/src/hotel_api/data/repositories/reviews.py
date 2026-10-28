"""MySQL repository for guest satisfaction reviews (T023, data-model.md §3.2)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any

from pymysql.connections import Connection

from hotel_api.business.domain.models import GuestReview, NewReview, Season
from hotel_api.business.rules.seasons import season_of_month
from hotel_api.data.connection import db_cursor

_SEASON_MONTHS: dict[Season, tuple[int, ...]] = {
    season: tuple(month for month in range(1, 13) if season_of_month(month) is season)
    for season in Season
}


def _row_to_review(row: dict[str, Any]) -> GuestReview:
    return GuestReview(
        id=int(row["id"]),
        booking_id=int(row["booking_id"]) if row["booking_id"] is not None else None,
        room_type=str(row["room_type"]),
        stay_date=row["stay_date"],
        rating=int(row["rating"]),
        created_at=row.get("created_at"),
    )


class MySqlReviewRepository:
    """Stores and queries `reviews` using parameterised SQL."""

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
    ) -> list[GuestReview]:
        """Return matching reviews ordered newest first (`id DESC`)."""
        clauses: list[str] = []
        params: list[Any] = []

        if year is not None:
            clauses.append("r.stay_date >= %s AND r.stay_date < %s")
            params.extend([date(year, 1, 1), date(year + 1, 1, 1)])

        if season is not None:
            months = _SEASON_MONTHS[Season(season)]
            placeholders = ", ".join(["%s"] * len(months))
            clauses.append(f"MONTH(r.stay_date) IN ({placeholders})")
            params.extend(months)

        if room_type is not None:
            clauses.append("rt.name = %s")
            params.append(room_type)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT
                r.id,
                r.booking_id,
                rt.name AS room_type,
                r.stay_date,
                r.rating,
                r.created_at
            FROM reviews r
            JOIN room_types rt ON rt.id = r.room_type_id
            {where_sql}
            ORDER BY r.id DESC
        """
        with db_cursor(self._conn) as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
        return [_row_to_review(row) for row in rows]

    def get(self, review_id: int) -> GuestReview | None:
        """Return the review with `review_id`, or `None` if it does not exist."""
        sql = """
            SELECT
                r.id,
                r.booking_id,
                rt.name AS room_type,
                r.stay_date,
                r.rating,
                r.created_at
            FROM reviews r
            JOIN room_types rt ON rt.id = r.room_type_id
            WHERE r.id = %s
        """
        with db_cursor(self._conn) as cursor:
            cursor.execute(sql, (review_id,))
            row = cursor.fetchone()
        return _row_to_review(row) if row is not None else None

    def add(self, review: NewReview) -> GuestReview:
        """Insert a review (copying room type and `stay_date` from the booking if not already resolved)."""
        with db_cursor(self._conn) as cursor:
            if review.booking_id is not None and (not review.room_type or review.stay_date is None):
                cursor.execute(
                    "SELECT room_type_id, check_in_date FROM bookings WHERE id = %s",
                    (review.booking_id,),
                )
                booking_row = cursor.fetchone()
                if booking_row is None:
                    raise ValueError(f"Unknown booking_id: {review.booking_id!r}")
                room_type_id = int(booking_row["room_type_id"])
                stay_date = booking_row["check_in_date"]
            else:
                room_type_id = self._resolve_room_type_id(cursor, review.room_type)
                stay_date = review.stay_date

            cursor.execute(
                """
                INSERT INTO reviews (booking_id, room_type_id, stay_date, rating)
                VALUES (%s, %s, %s, %s)
                """,
                (review.booking_id, room_type_id, stay_date, review.rating),
            )
            review_id = int(cursor.lastrowid)

        stored = self.get(review_id)
        assert stored is not None
        return stored

    def delete_all(self) -> None:
        """Delete all reviews."""
        with db_cursor(self._conn) as cursor:
            cursor.execute("DELETE FROM reviews")

    def insert_many(self, reviews: Sequence[GuestReview]) -> None:
        """Bulk insert reviews with explicit IDs (used by the seed command)."""
        if not reviews:
            return
        with db_cursor(self._conn) as cursor:
            rt_map = self._room_type_id_map(cursor)
            params = [
                (
                    r.id,
                    r.booking_id,
                    rt_map[r.room_type],
                    r.stay_date,
                    r.rating,
                )
                for r in reviews
            ]
            cursor.executemany(
                """
                INSERT INTO reviews (id, booking_id, room_type_id, stay_date, rating)
                VALUES (%s, %s, %s, %s, %s)
                """,
                params,
            )


ReviewRepo = MySqlReviewRepository

