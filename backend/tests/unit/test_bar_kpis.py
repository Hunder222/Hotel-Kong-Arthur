"""Bar KPI functions (T075, B1-B3, FR-012-FR-014): pure, no database.

Skipped until `kpis/bar.py` exists (T079); remove the guard then and mark T075 done. The tests define its API:

    ranked_drink_sales(sales)       -> list[RankedDrinkSale] ordered by revenue_rank, then name
    bar_summary(sales, year)        -> BarSummary
    bar_by_category(sales, year)    -> [BarCategoryKpi(Cocktail), BarCategoryKpi(Coffee)]  (always both)
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from hotel_api.business.domain.models import BarDrinkSale, DrinkCategory

bar = pytest.importorskip("hotel_api.business.kpis.bar", reason="kpis/bar.py not written yet (T079)")

pytestmark = pytest.mark.unit

D = Decimal
COCKTAIL, COFFEE = DrinkCategory.COCKTAIL, DrinkCategory.COFFEE


def sale(i, name, category, price, units, year=2026):
    return BarDrinkSale(i, year, name, category, D(price), units)


# real sample rows; 2025 row must not count
SALES = [
    sale(1, "Mojito", COCKTAIL, "142.38", 3350),      # 476973.00
    sale(2, "Espresso", COFFEE, "69.10", 14656),      # 1012729.60
    sale(3, "Americano", COFFEE, "40.84", 13833),     # 564939.72
    sale(4, "Margarita", COCKTAIL, "72.47", 2361),    # 171101.67
    sale(5, "Old row", COFFEE, "50.00", 99999, year=2025),
]


def test_revenue_per_drink_is_exact_decimal_price_times_units():
    assert SALES[3].revenue_dkk == D("171101.67")  # 72.47 x 2361, no float drift
    assert SALES[0].revenue_dkk == D("476973.00")
    assert SALES[1].revenue_dkk == D("1012729.60")


def test_bar_summary_b1():
    s = bar.bar_summary(SALES, 2026)
    assert (s.year, s.drink_count, s.units_sold, s.total_revenue_dkk) == (2026, 4, 34200, D("2225743.99"))


def test_summary_counts_only_the_requested_year():
    assert bar.bar_summary(SALES, 2025).total_revenue_dkk == D("4999950.00")
    assert bar.bar_summary(SALES, 2025).drink_count == 1


def test_zero_sales_return_zeros_not_an_error():
    s = bar.bar_summary([], 2026)
    assert (s.drink_count, s.units_sold, s.total_revenue_dkk) == (0, 0, D("0.00"))
    assert bar.ranked_drink_sales([]) == []
    rows = bar.bar_by_category([], 2026)
    assert [r.category for r in rows] == [COCKTAIL, COFFEE]
    assert all(
        (r.drink_count, r.units_sold, r.revenue_dkk, r.unit_share_pct, r.revenue_share_pct) == (0, 0, D("0.00"), D("0.00"), D("0.00"))
        for r in rows
    )


def test_a_drink_with_zero_units_sold_is_allowed():
    s = bar.bar_summary([sale(1, "Nothing", COCKTAIL, "100.00", 0)], 2026)
    assert (s.drink_count, s.units_sold, s.total_revenue_dkk) == (1, 0, D("0.00"))


def test_category_split_b3_by_revenue_and_by_units():
    cocktail, coffee = bar.bar_by_category(SALES, 2026)
    assert [cocktail.category, coffee.category] == [COCKTAIL, COFFEE]
    assert (cocktail.drink_count, cocktail.units_sold, cocktail.revenue_dkk) == (2, 5711, D("648074.67"))
    assert (coffee.drink_count, coffee.units_sold, coffee.revenue_dkk) == (2, 28489, D("1577669.32"))
    assert (cocktail.revenue_share_pct, coffee.revenue_share_pct) == (D("29.12"), D("70.88"))
    assert (cocktail.unit_share_pct, coffee.unit_share_pct) == (D("16.70"), D("83.30"))


def test_each_share_column_sums_to_exactly_100():
    rows = bar.bar_by_category(SALES, 2026)
    assert sum(r.revenue_share_pct for r in rows) == D("100.00")
    assert sum(r.unit_share_pct for r in rows) == D("100.00")


def test_both_categories_are_always_listed_even_if_one_has_no_sales():
    only_cocktails = [s for s in SALES if s.category is COCKTAIL]
    cocktail, coffee = bar.bar_by_category(only_cocktails, 2026)
    assert (cocktail.revenue_share_pct, cocktail.unit_share_pct) == (D("100.00"), D("100.00"))
    assert (coffee.drink_count, coffee.revenue_dkk, coffee.revenue_share_pct) == (0, D("0.00"), D("0.00"))


def test_ranks_by_revenue_and_by_units():
    ranked = bar.ranked_drink_sales([s for s in SALES if s.sales_year == 2026])
    assert [(r.revenue_rank, r.sale.drink_name) for r in ranked] == [
        (1, "Espresso"), (2, "Americano"), (3, "Mojito"), (4, "Margarita")]
    assert {r.sale.drink_name: r.units_rank for r in ranked} == {"Espresso": 1, "Americano": 2, "Mojito": 3, "Margarita": 4}


def test_revenue_rank_and_units_rank_can_differ():
    pricey_few = sale(1, "Pricey", COCKTAIL, "100.00", 10)    # revenue 1000, 10 units
    cheap_many = sale(2, "Cheap", COFFEE, "1.00", 100)        # revenue 100, 100 units
    ranked = {r.sale.drink_name: r for r in bar.ranked_drink_sales([pricey_few, cheap_many])}
    assert (ranked["Pricey"].revenue_rank, ranked["Pricey"].units_rank) == (1, 2)
    assert (ranked["Cheap"].revenue_rank, ranked["Cheap"].units_rank) == (2, 1)


def test_equal_values_share_a_rank_and_are_listed_by_name():
    a, b, c = (sale(1, "Zed", COFFEE, "10.00", 10), sale(2, "Alpha", COFFEE, "10.00", 10), sale(3, "Low", COFFEE, "1.00", 1))
    ranked = bar.ranked_drink_sales([a, b, c])
    assert [(r.revenue_rank, r.units_rank, r.sale.drink_name) for r in ranked] == [
        (1, 1, "Alpha"), (1, 1, "Zed"), (3, 3, "Low")]


def test_ranking_ignores_nothing_it_is_given():
    # filtering by year is the caller's job for ranking; the summary and split filter by `year` themselves
    assert len(bar.ranked_drink_sales(SALES)) == 5
