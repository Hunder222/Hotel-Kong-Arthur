"""Keeps PostgreSQL identity sequences in step with rows inserted with explicit ids (the seed command).

Without this, a booking created after the seed would get id 1 from the untouched sequence and collide with
the seeded row. After the sync, the next generated id is MAX(id) + 1 (1001 after the sample data).
"""

from __future__ import annotations

from typing import Any

# Only these tables have identity ids; a fixed list also keeps the table name out of reach of any input.
_IDENTITY_TABLES = frozenset({"bookings", "reviews", "bar_drink_sales"})


def sync_identity_sequence(cursor: Any, table: str) -> None:
    """Set the identity sequence of `table` so the next generated id follows the highest existing id."""
    if table not in _IDENTITY_TABLES:
        raise ValueError(f"No identity sequence to sync for table {table!r}")
    cursor.execute(
        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) "
        f"FROM {table}"
    )
    cursor.fetchone()
