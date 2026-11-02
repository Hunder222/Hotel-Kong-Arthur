"""Pure bar KPI calculations (T044, B1-B3, FR-012-FR-014, FR-021): no database, no HTTP."""

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
    sale(1, "Mojito", COCKTAIL, "142.38", 3350),      # 476973.00 (premium)
    sale(2, "Espresso", COFFEE, "69.10", 14656),      # 1012729.60 (budget)
    sale(3, "Americano", COFFEE, "40.84", 13833),     # 564939.72 (budget)
    sale(4, "Margarita", COCKTAIL, "72.47", 2361),    # 171101.67 (standard)
]

SALES_MULTI_YEAR = SALES_2026 + [
    sale(5, "Old row", COFFEE, "50.00", 99999, year=2025),  # 4999950.00 (budget)
]


def test_revenue_per_drink_is_exact_decimal_price_times_units():
    assert SALES_2026[3].revenue_dkk == D("171101.67")  # 72.47 x 2361, no float drift
    assert SALES_2026[0].revenue_dkk == D("476973.00")
    assert SALES_2026[1].revenue_dkk == D("1012729.60")
    assert bar.total_revenue(SALES_2026) == D("2225743.99")
    assert bar.total_revenue([]) == D("0.00")


def test_bar_summary_b1_totals_and_zero_state():
    s = bar.bar_summary(SALES_2026, 2026)
    assert (s.year, s.drink_count, s.units_sold, s.total_revenue_dkk) == (2026, 4, 34200, D("2225743.99"))

    empty = bar.bar_summary([], 2026)
    assert (empty.year, empty.drink_count, empty.units_sold, empty.total_revenue_dkk) == (2026, 0, 0, D("0.00"))

    empty_all = bar.bar_summary([], "all")
    assert (empty_all.year, empty_all.drink_count, empty_all.units_sold, empty_all.total_revenue_dkk) == (
        "all",
        0,
        0,
        D("0.00"),
    )


def test_a_drink_with_zero_units_sold_is_allowed():
    s = bar.bar_summary([sale(1, "Nothing", COCKTAIL, "100.00", 0)], 2026)
    assert (s.drink_count, s.units_sold, s.total_revenue_dkk) == (1, 0, D("0.00"))


def test_a_drink_sold_in_several_years_is_counted_as_one_distinct_drink_all_time():
    two_years = [
        sale(1, "Espresso", COFFEE, "70.00", 100, year=2025),
        sale(2, "Espresso", COFFEE, "75.00", 100, year=2026),
    ]
    s = bar.bar_summary(two_years, "all")
    assert (s.year, s.drink_count, s.units_sold, s.total_revenue_dkk) == ("all", 1, 200, D("14500.00"))
    assert bar.category_kpis(two_years, "all")[1].drink_count == 1


def test_ranks_by_revenue_and_by_units_b2():
    ranked = bar.ranked_drink_sales(SALES_2026)
    assert [(r.revenue_rank, r.drink_name) for r in ranked] == [
        (1, "Espresso"),
        (2, "Americano"),
        (3, "Mojito"),
        (4, "Margarita"),
    ]
    assert {r.drink_name: r.units_rank for r in ranked} == {
        "Espresso": 1,
        "Americano": 2,
        "Mojito": 3,
        "Margarita": 4,
    }
    assert {r.drink_name: r.price_tier for r in ranked} == {
        "Espresso": PriceTier.BUDGET,
        "Americano": PriceTier.BUDGET,
        "Margarita": PriceTier.STANDARD,
        "Mojito": PriceTier.PREMIUM,
    }


def test_revenue_rank_and_units_rank_can_differ():
    pricey_few = sale(1, "Pricey", COCKTAIL, "100.00", 10)  # revenue 1000, 10 units
    cheap_many = sale(2, "Cheap", COFFEE, "1.00", 100)      # revenue 100, 100 units
    ranked = {r.drink_name: r for r in bar.ranked_drink_sales([pricey_few, cheap_many])}
    assert (ranked["Pricey"].revenue_rank, ranked["Pricey"].units_rank) == (1, 2)
    assert (ranked["Cheap"].revenue_rank, ranked["Cheap"].units_rank) == (2, 1)


def test_equal_values_share_a_competition_rank_and_are_listed_by_name():
    a = sale(1, "Zed", COFFEE, "10.00", 10)
    b = sale(2, "Alpha", COFFEE, "10.00", 10)
    c = sale(3, "Low", COFFEE, "1.00", 1)
    ranked = bar.ranked_drink_sales([a, b, c])
    assert [(r.revenue_rank, r.units_rank, r.drink_name) for r in ranked] == [
        (1, 1, "Alpha"),
        (1, 1, "Zed"),
        (3, 3, "Low"),
    ]


def test_multi_year_drink_list_ranks_each_year_on_its_own_in_ascending_year_order():
    ranked = bar.ranked_drink_sales(SALES_MULTI_YEAR)
    assert [(r.year, r.revenue_rank, r.units_rank, r.drink_name) for r in ranked] == [
        (2025, 1, 1, "Old row"),
        (2026, 1, 1, "Espresso"),
        (2026, 2, 2, "Americano"),
        (2026, 3, 3, "Mojito"),
        (2026, 4, 4, "Margarita"),
    ]
    assert bar.ranked_drink_sales([]) == []


def test_category_split_b3_by_revenue_and_by_units_with_shares_summing_to_100():
    cocktail, coffee = bar.category_kpis(SALES_2026, 2026)
    assert [cocktail.category, coffee.category] == [COCKTAIL, COFFEE]
    assert (cocktail.drink_count, cocktail.units_sold, cocktail.revenue_dkk) == (2, 5711, D("648074.67"))
    assert (coffee.drink_count, coffee.units_sold, coffee.revenue_dkk) == (2, 28489, D("1577669.32"))
    assert (cocktail.revenue_share_pct, coffee.revenue_share_pct) == (D("29.12"), D("70.88"))
    assert (cocktail.unit_share_pct, coffee.unit_share_pct) == (D("16.70"), D("83.30"))
    assert cocktail.revenue_share_pct + coffee.revenue_share_pct == D("100.00")
    assert cocktail.unit_share_pct + coffee.unit_share_pct == D("100.00")


def test_category_split_handles_empty_sales_and_single_category_data():
    empty_rows = bar.category_kpis([], 2026)
    assert [r.category for r in empty_rows] == [COCKTAIL, COFFEE]
    assert all(
        (r.drink_count, r.units_sold, r.revenue_dkk, r.unit_share_pct, r.revenue_share_pct)
        == (0, 0, D("0.00"), D("0.00"), D("0.00"))
        for r in empty_rows
    )

    only_cocktails = [s for s in SALES_2026 if s.category is COCKTAIL]
    cocktail, coffee = bar.category_kpis(only_cocktails, 2026)
    assert (cocktail.revenue_share_pct, cocktail.unit_share_pct) == (D("100.00"), D("100.00"))
    assert (coffee.drink_count, coffee.revenue_dkk, coffee.revenue_share_pct) == (0, D("0.00"), D("0.00"))

    filtered_category = bar.category_kpis(only_cocktails, 2026, [COCKTAIL])
    assert [(r.category, r.revenue_share_pct, r.unit_share_pct) for r in filtered_category] == [
        (COCKTAIL, D("100.00"), D("100.00"))
    ]


def test_filter_drink_sales_by_year_category_and_price_tier():
    assert len(bar.filter_drink_sales(SALES_MULTI_YEAR, BarFilters())) == 5
    assert len(bar.filter_drink_sales(SALES_MULTI_YEAR, BarFilters(year=2026))) == 4
    assert [s.drink_name for s in bar.filter_drink_sales(SALES_MULTI_YEAR, BarFilters(year=2025))] == ["Old row"]
    assert [s.drink_name for s in bar.filter_drink_sales(SALES_2026, BarFilters(category=COCKTAIL))] == [
        "Mojito",
        "Margarita",
    ]
    assert [s.drink_name for s in bar.filter_drink_sales(SALES_2026, BarFilters(price_tier=PriceTier.PREMIUM))] == [
        "Mojito"
    ]
    assert [
        s.drink_name
        for s in bar.filter_drink_sales(
            SALES_2026, BarFilters(year=2026, category=COCKTAIL, price_tier=PriceTier.STANDARD)
        )
    ] == ["Margarita"]


class _FakeBarSalesRepo:
    def __init__(self, rows: list[BarDrinkSale]) -> None:
        self._rows = list(rows)

    def list(self) -> list[BarDrinkSale]:
        return list(self._rows)


def test_kpi_service_computes_bar_summary_by_drink_and_by_category_for_filter_scope():
    service = KpiService(bar_sales=_FakeBarSalesRepo(SALES_MULTI_YEAR))

    summary_2026 = service.bar_summary(BarFilters(year=2026))
    assert (summary_2026.year, summary_2026.drink_count, summary_2026.total_revenue_dkk) == (
        2026,
        4,
        D("2225743.99"),
    )

    summary_all = service.bar_summary(BarFilters(year="all"))
    assert (summary_all.year, summary_all.drink_count, summary_all.total_revenue_dkk) == (
        "all",
        5,
        D("7225693.99"),
    )

    cocktails = service.bar_by_drink(BarFilters(year=2026, category=COCKTAIL))
    assert [(r.revenue_rank, r.drink_name) for r in cocktails] == [(1, "Mojito"), (2, "Margarita")]

    categories_all = service.bar_by_category(BarFilters(year=2026))
    assert [r.category for r in categories_all] == [COCKTAIL, COFFEE]

    categories_filtered = service.bar_by_category(BarFilters(year=2026, category=COCKTAIL))
    assert [(r.category, r.revenue_share_pct) for r in categories_filtered] == [(COCKTAIL, D("100.00"))]

