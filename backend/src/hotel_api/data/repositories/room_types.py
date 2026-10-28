"""MySQL repository for room types and their seasonal rate bands (T021, data-model.md §2)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pymysql.connections import Connection

from hotel_api.business.domain.models import RoomType, Season, SeasonRate
from hotel_api.business.rules.seasons import SEASON_ORDER
from hotel_api.data.connection import db_cursor


class MySqlRoomTypeRepository:
    """Reads `room_types` and `room_type_rates` using parameterised SQL."""

    def __init__(self, conn: Connection[Any]) -> None:
        self._conn = conn

    def list_all(self) -> list[RoomType]:
        """Return all room types in canonical (T1) id order, each with rates ordered low, mid, high."""
        with db_cursor(self._conn) as cursor:
            cursor.execute(
                """
                SELECT id, name, name_da, room_count, max_guests
                FROM room_types
                ORDER BY id ASC
                """
            )
            type_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT room_type_id, season, min_nightly_dkk, max_nightly_dkk, standard_nightly_dkk
                FROM room_type_rates
                ORDER BY room_type_id ASC, FIELD(season, 'low', 'mid', 'high')
                """
            )
            rate_rows = cursor.fetchall()

        rates_by_type: dict[int, dict[Season, SeasonRate]] = {}
        for row in rate_rows:
            rt_id = int(row["room_type_id"])
            season = Season(row["season"])
            rates_by_type.setdefault(rt_id, {})[season] = SeasonRate(
                season=season,
                min_nightly_dkk=Decimal(row["min_nightly_dkk"]),
                max_nightly_dkk=Decimal(row["max_nightly_dkk"]),
                standard_nightly_dkk=Decimal(row["standard_nightly_dkk"]),
            )

        result: list[RoomType] = []
        for row in type_rows:
            rt_id = int(row["id"])
            raw_rates = rates_by_type.get(rt_id, {})
            ordered_rates = {
                season: raw_rates[season]
                for season in SEASON_ORDER
                if season in raw_rates
            }
            result.append(
                RoomType(
                    id=rt_id,
                    name=str(row["name"]),
                    name_da=str(row["name_da"]),
                    room_count=int(row["room_count"]),
                    max_guests=int(row["max_guests"]),
                    rates=ordered_rates,
                )
            )
        return result

    def get_by_name(self, name: str) -> RoomType | None:
        """Return the room type matching `name` (with rates ordered low, mid, high), or `None`."""
        with db_cursor(self._conn) as cursor:
            cursor.execute(
                """
                SELECT id, name, name_da, room_count, max_guests
                FROM room_types
                WHERE name = %s
                """,
                (name,),
            )
            row = cursor.fetchone()
            if row is None or str(row["name"]) != name:
                return None

            rt_id = int(row["id"])
            cursor.execute(
                """
                SELECT season, min_nightly_dkk, max_nightly_dkk, standard_nightly_dkk
                FROM room_type_rates
                WHERE room_type_id = %s
                ORDER BY FIELD(season, 'low', 'mid', 'high')
                """,
                (rt_id,),
            )
            rate_rows = cursor.fetchall()

        raw_rates = {
            Season(r["season"]): SeasonRate(
                season=Season(r["season"]),
                min_nightly_dkk=Decimal(r["min_nightly_dkk"]),
                max_nightly_dkk=Decimal(r["max_nightly_dkk"]),
                standard_nightly_dkk=Decimal(r["standard_nightly_dkk"]),
            )
            for r in rate_rows
        }
        ordered_rates = {
            season: raw_rates[season]
            for season in SEASON_ORDER
            if season in raw_rates
        }
        return RoomType(
            id=rt_id,
            name=str(row["name"]),
            name_da=str(row["name_da"]),
            room_count=int(row["room_count"]),
            max_guests=int(row["max_guests"]),
            rates=ordered_rates,
        )


RoomTypeRepo = MySqlRoomTypeRepository

