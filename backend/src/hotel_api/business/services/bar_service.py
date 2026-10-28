"""Use case: bar sales and bar KPIs (B1-B3). Loads one year through the port and calls the pure functions
in `business/kpis/bar.py`; it contains no formulas itself (Constitution VII). Bar data is read-only here."""

from __future__ import annotations

from hotel_api.business.domain.models import BarCategoryKpi, BarSummary, DrinkCategory, RankedDrinkSale
from hotel_api.business.kpis import bar
from hotel_api.business.ports import BarSalesRepository


class BarService:
    def __init__(self, bar_sales: BarSalesRepository) -> None:
        self._bar_sales = bar_sales

    def drink_sales(self, year: int, category: DrinkCategory | None = None) -> list[RankedDrinkSale]:
        """The year's drinks ordered by revenue rank. Ranks are among all drinks; `category` only selects rows."""
        ranked = bar.ranked_drink_sales(self._bar_sales.list(year))
        if category is None:
            return ranked
        return [r for r in ranked if r.sale.category is category]

    def summary(self, year: int) -> BarSummary:
        return bar.bar_summary(self._bar_sales.list(year), year)

    def by_category(self, year: int) -> list[BarCategoryKpi]:
        return bar.bar_by_category(self._bar_sales.list(year), year)
