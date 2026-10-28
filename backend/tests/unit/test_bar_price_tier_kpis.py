"""Bar demand per price tier (T085, FR-016): pure, no database."""

from __future__ import annotations

from decimal import Decimal

import pytest

from hotel_api.business.domain.models import BarDrinkSale, DrinkCategory, PriceTier
from hotel_api.business.kpis import bar
from hotel_api.business.rules import price_tiers

pytestmark = pytest.mark.unit

D = Decimal
COCKTAIL, COFFEE = DrinkCategory.COCKTAIL, DrinkCategory.COFFEE


def sale(i, name, category, price, units, year=2026):
    return BarDrinkSale(i, year, name, category, D(price), units)


SALES = [
    sale(1, "Flat White", COFFEE, "33.43", 10249),    # budget      342,624.07
    sale(2, "Espresso", COFFEE, "69.10", 14656),      # budget    1,012,729.60
    sale(3, "Margarita", COCKTAIL, "72.47", 2361),    # standard    171,101.67
    sale(4, "At seventy", COCKTAIL, "70.00", 100),    # standard (boundary)  7,000.00
    sale(5, "Mojito", COCKTAIL, "142.38", 3350),      # premium     476,973.00
    sale(6, "Negroni", COCKTAIL, "149.48", 2691),     # premium     402,250.68
    sale(7, "At one-ten", COCKTAIL, "110.00", 50),    # premium (boundary)   5,500.00
    sale(8, "Old", COFFEE, "10.00", 99999, year=2025),
]


def test_there_are_always_three_tiers_in_order():
    rows = bar.bar_by_price_tier(SALES, 2026)
    assert [r.price_tier for r in rows] == [PriceTier.BUDGET, PriceTier.STANDARD, PriceTier.PREMIUM]
    assert all(r.year == 2026 for r in rows)


def test_units_revenue_and_drink_count_per_tier():
    budget, standard, premium = bar.bar_by_price_tier(SALES, 2026)
    assert (budget.drink_count, budget.units_sold, budget.revenue_dkk) == (2, 24905, D("1355353.67"))
    assert (standard.drink_count, standard.units_sold, standard.revenue_dkk) == (2, 2461, D("178101.67"))
    assert (premium.drink_count, premium.units_sold, premium.revenue_dkk) == (3, 6091, D("884723.68"))


def test_boundary_prices_70_and_110_belong_to_the_higher_tier():
    budget, standard, premium = bar.bar_by_price_tier(SALES, 2026)
    assert "At seventy" not in str(budget) and standard.drink_count == 2 and premium.drink_count == 3


def test_shares_per_tier_sum_to_exactly_100():
    rows = bar.bar_by_price_tier(SALES, 2026)
    assert [r.unit_share_pct for r in rows] == [D("74.44"), D("7.36"), D("18.20")]
    assert [r.revenue_share_pct for r in rows] == [D("56.05"), D("7.36"), D("36.59")]
    assert sum(r.unit_share_pct for r in rows) == D("100.00")
    assert sum(r.revenue_share_pct for r in rows) == D("100.00")


def test_only_the_requested_year_counts():
    old = bar.bar_by_price_tier(SALES, 2025)
    assert (old[0].drink_count, old[0].units_sold) == (1, 99999)
    assert old[1].drink_count == 0 and old[2].drink_count == 0


def test_the_price_bounds_of_each_tier_are_reported():
    budget, standard, premium = bar.bar_by_price_tier(SALES, 2026)
    assert (budget.price_from_dkk, budget.price_to_dkk) == (D("0"), D("70"))
    assert (standard.price_from_dkk, standard.price_to_dkk) == (D("70"), D("110"))
    assert (premium.price_from_dkk, premium.price_to_dkk) == (D("110"), None)
    assert price_tiers.tier_bounds(PriceTier.PREMIUM) == (D("110"), None)


def test_an_empty_year_returns_three_rows_with_zeros():
    rows = bar.bar_by_price_tier([], 2026)
    assert len(rows) == 3
    assert all(
        (r.drink_count, r.units_sold, r.revenue_dkk, r.unit_share_pct, r.revenue_share_pct)
        == (0, 0, D("0.00"), D("0.00"), D("0.00"))
        for r in rows
    )
    assert rows[2].price_to_dkk is None
