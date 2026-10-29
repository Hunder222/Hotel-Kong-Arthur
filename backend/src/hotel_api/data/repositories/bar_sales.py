"""MySQL repository for lobby bar drink sales (T024, data-model.md §3.3)."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from pymysql.connections import Connection

from hotel_api.business.domain.models import BarDrinkSale, DrinkCategory
from hotel_api.data.connection import db_cursor


def _row_to_bar_sale(row: dict[str, Any]) -> BarDrinkSale:
    return BarDrinkSale(
        id=int(row["id"]),
        sales_year=int(row["sales_year"]),
        drink_name=str(row["drink_name"]),
        category=DrinkCategory(row["category"]),
        unit_price_dkk=Decimal(row["unit_price_dkk"]),
        units_sold=int(row["units_sold"]),
    )


class MySqlBarSalesRepository:
    """Stores and queries `bar_drink_sales` using parameterised SQL."""

    def __init__(self, conn: Connection[Any]) -> None:
        self._conn = conn

    def list(self, sales_year: int | None, category: DrinkCategory | None = None) -> list[BarDrinkSale]:
        """Return drink sales for `sales_year` (every year when None) and optional `category`, ordered by `id ASC`."""
        clauses: list[str] = []
        params: list[Any] = []

        if sales_year is not None:
            clauses.append("sales_year = %s")
            params.append(sales_year)

        if category is not None:
            cat_val = category.value if isinstance(category, DrinkCategory) else str(category)
            clauses.append("category = %s")
            params.append(cat_val)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT id, sales_year, drink_name, category, unit_price_dkk, units_sold
            FROM bar_drink_sales
            {where}
            ORDER BY id ASC
        """
        with db_cursor(self._conn) as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
        return [_row_to_bar_sale(row) for row in rows]

    def delete_all(self) -> None:
        """Delete all bar drink sales."""
        with db_cursor(self._conn) as cursor:
            cursor.execute("DELETE FROM bar_drink_sales")

    def insert_many(self, sales: Sequence[BarDrinkSale]) -> None:
        """Bulk insert bar drink sales with explicit IDs (used by the seed command)."""
        if not sales:
            return
        params = [
            (
                s.id,
                s.sales_year,
                s.drink_name,
                s.category.value if isinstance(s.category, DrinkCategory) else str(s.category),
                s.unit_price_dkk,
                s.units_sold,
            )
            for s in sales
        ]
        with db_cursor(self._conn) as cursor:
            cursor.executemany(
                """
                INSERT INTO bar_drink_sales (
                    id,
                    sales_year,
                    drink_name,
                    category,
                    unit_price_dkk,
                    units_sold
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                params,
            )


BarSalesRepo = MySqlBarSalesRepository

