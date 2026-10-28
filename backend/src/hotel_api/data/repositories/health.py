"""MySQL health repository executing a lightweight `SELECT 1` ping (T025)."""

from __future__ import annotations

from typing import Any

from pymysql.connections import Connection

from hotel_api.data.connection import db_cursor


class MySqlHealthRepository:
    """Checks database reachability with `SELECT 1`."""

    def __init__(self, conn: Connection[Any]) -> None:
        self._conn = conn

    def ping(self) -> None:
        """Execute `SELECT 1`; raises `StorageUnavailable` if the database cannot be reached."""
        with db_cursor(self._conn) as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()


HealthRepo = MySqlHealthRepository

