"""Use case: bar drink sales (`GET /api/v1/bar/drink-sales`). Read-only."""

from __future__ import annotations

from hotel_api.business.domain.models import BarDrinkSale
from hotel_api.business.ports import BarSalesRepository


class BarService:
    def __init__(self, bar_sales: BarSalesRepository) -> None:
        self._bar_sales = bar_sales

    def drink_sales(self) -> list[BarDrinkSale]:
        """All bar drink sales ordered by id ascending."""
        return self._bar_sales.list()

