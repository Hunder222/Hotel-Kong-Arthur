"""Use case: bar sales and bar KPIs (B1-B3, price-tier demand). Loads one year through the port (every year when
`year` is None, FR-021) and calls the pure functions in `business/kpis/bar.py`; it contains no formulas itself
(Constitution VII). Bar data is read-only here."""

from __future__ import annotations

from hotel_api.business.domain.models import (
    BarCategoryKpi,
    BarPriceTierKpi,
    BarSummary,
    DrinkCategory,
    RankedDrinkSale,
)
from hotel_api.business.kpis import bar
from hotel_api.business.ports import BarSalesRepository


class BarService:
    def __init__(self, bar_sales: BarSalesRepository) -> None:
        self._bar_sales = bar_sales

    def drink_sales(self, year: int | None, category: DrinkCategory | None = None) -> list[RankedDrinkSale]:
        """The drinks ordered by revenue rank. Ranks are among all drinks of a year; `category` only selects rows.

        `year=None` (all-time) lists every year: one row per drink and year, each year ranked on its own.
        """
        sales = self._bar_sales.list(year)
        ranked = bar.ranked_drink_sales(sales) if year is not None else bar.ranked_drink_sales_by_year(sales)
        if category is None:
            return ranked
        return [r for r in ranked if r.sale.category is category]

    def summary(self, year: int | None) ->BarSummary:
        return bar.bar_summary(self._bar_sales.list(year), year)

    def by_category(self, year: int | None) ->list[BarCategoryKpi]:
        return bar.bar_by_category(self._bar_sales.list(year), year)

    def by_price_tier(self, year: int | None) ->list[BarPriceTierKpi]:
        return bar.bar_by_price_tier(self._bar_sales.list(year), year)
