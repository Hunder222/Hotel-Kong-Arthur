"""Bar KPIs (B1-B3; FR-012-FR-014; data-model §7). Pure functions, no I/O.

Revenue per drink is `BarDrinkSale.revenue_dkk` (unit price x units sold, exact Decimal). Shares follow
`rules/numbers.py` (each column sums to exactly 100.00) and ranks follow `rules/ranking.py`.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from decimal import Decimal

from hotel_api.business.domain.models import (
    BarCategoryKpi,
    BarDrinkSale,
    BarPriceTierKpi,
    BarSummary,
    DrinkCategory,
    RankedDrinkSale,
)
from hotel_api.business.rules.numbers import round_half_up, shares_pct
from hotel_api.business.rules.price_tiers import TIER_ORDER, tier_bounds, tier_for_price
from hotel_api.business.rules.ranking import rank_descending

CATEGORY_ORDER: tuple[DrinkCategory, ...] = (DrinkCategory.COCKTAIL, DrinkCategory.COFFEE)


def bar_sales_of_year(sales: Iterable[BarDrinkSale], year: int) -> list[BarDrinkSale]:
    return [s for s in sales if s.sales_year == year]


def ranked_drink_sales(sales: Sequence[BarDrinkSale]) -> list[RankedDrinkSale]:
    """Every given drink with its rank by revenue (B2) and by units sold, ordered by revenue rank, then name.

    Equal values share a rank. The caller passes the drinks of one year; ranks are among all of them.
    """
    revenue_ranks = {s.id: rank for rank, s in rank_descending(sales, lambda s: s.revenue_dkk, lambda s: s.drink_name)}
    units_ranks = {s.id: rank for rank, s in rank_descending(sales, lambda s: s.units_sold, lambda s: s.drink_name)}
    ordered = sorted(sales, key=lambda s: (revenue_ranks[s.id], s.drink_name))
    return [RankedDrinkSale(s, revenue_ranks[s.id], units_ranks[s.id]) for s in ordered]


def bar_summary(sales: Iterable[BarDrinkSale], year: int) -> BarSummary:
    """Helene Christine's total bar sales for the year (B1): revenue, units and number of drinks."""
    in_year = bar_sales_of_year(sales, year)
    revenue = round_half_up(sum((s.revenue_dkk for s in in_year), Decimal("0.00")))
    return BarSummary(year, len(in_year), sum(s.units_sold for s in in_year), revenue)


def bar_by_category(sales: Iterable[BarDrinkSale], year: int) -> list[BarCategoryKpi]:
    """Cocktail vs coffee (B3): always both rows, split by revenue and by units, each share column = 100.00."""
    in_year = bar_sales_of_year(sales, year)
    groups = [[s for s in in_year if s.category is category] for category in CATEGORY_ORDER]
    revenues = [round_half_up(sum((s.revenue_dkk for s in g), Decimal("0.00"))) for g in groups]
    units = [sum(s.units_sold for s in g) for g in groups]
    revenue_shares = shares_pct(revenues)
    unit_shares = shares_pct(units)
    return [
        BarCategoryKpi(
            year=year,
            category=category,
            drink_count=len(group),
            units_sold=units[i],
            unit_share_pct=unit_shares[i],
            revenue_dkk=revenues[i],
            revenue_share_pct=revenue_shares[i],
        )
        for i, (category, group) in enumerate(zip(CATEGORY_ORDER, groups))
    ]


def bar_by_price_tier(sales: Iterable[BarDrinkSale], year: int) -> list[BarPriceTierKpi]:
    """Demand per price tier (FR-016, US4/A7): always budget, standard, premium, with units, revenue and shares
    (each share column = 100.00), so the CFO can see whether guests buy cheaper or dearer drinks."""
    in_year = bar_sales_of_year(sales, year)
    groups = [[s for s in in_year if tier_for_price(s.unit_price_dkk) is tier] for tier in TIER_ORDER]
    revenues = [round_half_up(sum((s.revenue_dkk for s in g), Decimal("0.00"))) for g in groups]
    units = [sum(s.units_sold for s in g) for g in groups]
    revenue_shares = shares_pct(revenues)
    unit_shares = shares_pct(units)
    rows = []
    for i, (tier, group) in enumerate(zip(TIER_ORDER, groups)):
        price_from, price_to = tier_bounds(tier)
        rows.append(
            BarPriceTierKpi(
                year=year,
                price_tier=tier,
                price_from_dkk=price_from,
                price_to_dkk=price_to,
                drink_count=len(group),
                units_sold=units[i],
                unit_share_pct=unit_shares[i],
                revenue_dkk=revenues[i],
                revenue_share_pct=revenue_shares[i],
            )
        )
    return rows
