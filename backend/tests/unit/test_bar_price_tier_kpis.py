"""Unit tests for bar price-tier KPI aggregation and share rounding (T054, A7, FR-016)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from hotel_api.business.domain.models import (
    BarDrinkSale,
    BarFilters,
    DrinkCategory,
    PriceTier,
)
from hotel_api.business.kpis import bar
from hotel_api.business.services.kpi_service import KpiService

pytestmark = pytest.mark.unit

D = Decimal
COCKTAIL, COFFEE = DrinkCategory.COCKTAIL, DrinkCategory.COFFEE


def sale(id_: int, name: str, category: DrinkCategory, price: str, units: int, year: int = 2026) -> BarDrinkSale:
    return BarDrinkSale(id_, year, name, category, D(price), units)


SALES_2026 = [
    sale(1, "Mojito", COCKTAIL, "142.38", 3350),      # 476973.00 (premium >= 110)
    sale(2, "Espresso", COFFEE, "69.10", 14656),      # 1012729.60 (budget < 70)
    sale(3, "Americano", COFFEE, "40.84", 13833),     # 564939.72 (budget < 70)
    sale(4, "Margarita", COCKTAIL, "72.47", 2361),    # 171101.67 (standard 70..<110)
]


def test_price_tier_kpis_aggregates_units_revenue_bounds_and_shares():
    rows = bar.price_tier_kpis(SALES_2026, 2026)
    assert [r.price_tier for r in rows] == [PriceTier.BUDGET, PriceTier.STANDARD, PriceTier.PREMIUM]
    budget, standard, premium = rows

    assert (budget.year, budget.price_from_dkk, budget.price_to_dkk) == (2026, D("0.00"), D("70.00"))
    assert (budget.drink_count, budget.units_sold, budget.revenue_dkk) == (2, 28489, D("1577669.32"))

    assert (standard.year, standard.price_from_dkk, standard.price_to_dkk) == (2026, D("70.00"), D("110.00"))
    assert (standard.drink_count, standard.units_sold, standard.revenue_dkk) == (1, 2361, D("171101.67"))

    assert (premium.year, premium.price_from_dkk, premium.price_to_dkk) == (2026, D("110.00"), None)
    assert (premium.drink_count, premium.units_sold, premium.revenue_dkk) == (1, 3350, D("476973.00"))

    assert (budget.unit_share_pct, standard.unit_share_pct, premium.unit_share_pct) == (
        D("83.30"),
        D("6.90"),
        D("9.80"),
    )
    assert (budget.revenue_share_pct, standard.revenue_share_pct, premium.revenue_share_pct) == (
        D("70.88"),
        D("7.69"),
        D("21.43"),
    )
    assert sum((r.unit_share_pct for r in rows), D("0.00")) == D("100.00")
    assert sum((r.revenue_share_pct for r in rows), D("0.00")) == D("100.00")


def test_price_tier_kpis_largest_remainder_rounding_sums_to_100():
    three_equal = [
        sale(1, "A", COFFEE, "50.00", 1),
        sale(2, "B", COCKTAIL, "90.00", 1),
        sale(3, "C", COCKTAIL, "150.00", 1),
    ]
    rows = bar.price_tier_kpis(three_equal, 2026)
    assert [r.unit_share_pct for r in rows] == [D("33.34"), D("33.33"), D("33.33")]
    assert sum((r.unit_share_pct for r in rows), D("0.00")) == D("100.00")
    assert sum((r.revenue_share_pct for r in rows), D("0.00")) == D("100.00")


def test_price_tier_kpis_handles_empty_sales_and_single_tier_filter():
    empty_rows = bar.price_tier_kpis([], 2026)
    assert [r.price_tier for r in empty_rows] == [PriceTier.BUDGET, PriceTier.STANDARD, PriceTier.PREMIUM]
    assert all(
        (r.drink_count, r.units_sold, r.unit_share_pct, r.revenue_dkk, r.revenue_share_pct)
        == (0, 0, D("0.00"), D("0.00"), D("0.00"))
        for r in empty_rows
    )

    only_premium = [s for s in SALES_2026 if s.price_tier is PriceTier.PREMIUM]
    sliced = bar.price_tier_kpis(only_premium, 2026, [PriceTier.PREMIUM])
    assert len(sliced) == 1
    assert sliced[0].price_tier is PriceTier.PREMIUM
    assert (sliced[0].unit_share_pct, sliced[0].revenue_share_pct) == (D("100.00"), D("100.00"))


class _FakeBarSalesRepo:
    def __init__(self, rows: list[BarDrinkSale]) -> None:
        self._rows = list(rows)

    def list(self) -> list[BarDrinkSale]:
        return list(self._rows)


def test_kpi_service_bar_by_price_tier_respects_filters():
    service = KpiService(bar_sales=_FakeBarSalesRepo(SALES_2026))

    all_tiers = service.bar_by_price_tier(BarFilters(year=2026))
    assert [r.price_tier for r in all_tiers] == [PriceTier.BUDGET, PriceTier.STANDARD, PriceTier.PREMIUM]

    cocktails_only = service.bar_by_price_tier(BarFilters(year=2026, category=COCKTAIL))
    assert [r.drink_count for r in cocktails_only] == [0, 1, 1]

    premium_only = service.bar_by_price_tier(BarFilters(year=2026, price_tier=PriceTier.PREMIUM))
    assert len(premium_only) == 1
    assert premium_only[0].price_tier is PriceTier.PREMIUM
    assert premium_only[0].revenue_dkk == D("476973.00")

