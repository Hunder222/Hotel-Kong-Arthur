"""Cocktail bar KPI calculations (data-model §7): total sales, per-drink revenue & ranks, and category split (B1-B3).

Pure functions over already-loaded drink sales. The caller filters the records to the requested scope with
`filter_drink_sales` and passes the categories in scope.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Iterable, Sequence

from hotel_api.business.domain.models import (
    BarCategoryKpi,
    BarDrinkSale,
    BarFilters,
    BarSummary,
    DrinkCategory,
    RankedDrinkSale,
    ReportYear,
)
from hotel_api.business.rules.numbers import largest_remainder_shares, round_half_up
from hotel_api.business.rules.ranking import competition_ranks

ZERO = Decimal("0.00")

CATEGORY_ORDER: tuple[DrinkCategory, ...] = (
    DrinkCategory.COCKTAIL,
    DrinkCategory.COFFEE,
)


def filter_drink_sales(sales: Iterable[BarDrinkSale], filters: BarFilters) -> list[BarDrinkSale]:
    return [
        s
        for s in sales
        if (filters.year == "all" or s.sales_year == filters.year)
        and (filters.category is None or s.category is filters.category)
        and (filters.price_tier is None or s.price_tier is filters.price_tier)
    ]


def _drink_count(sales: Iterable[BarDrinkSale]) -> int:
    """Distinct drink names: a drink sold across multiple years is counted once in all-time totals."""
    return len({s.drink_name for s in sales})


def total_revenue(sales: Iterable[BarDrinkSale]) -> Decimal:
    """B1 / B2: sum of `unit_price_dkk * units_sold` across the sales in scope."""
    return sum((s.revenue_dkk for s in sales), ZERO)


def bar_summary(sales: Sequence[BarDrinkSale], year: ReportYear) -> BarSummary:
    """B1: Helene Christine's total lobby bar sales for the requested filter scope."""
    return BarSummary(
        year=year,
        drink_count=_drink_count(sales),
        units_sold=sum(s.units_sold for s in sales),
        total_revenue_dkk=round_half_up(total_revenue(sales)),
    )


def _rank_single_year(sales: Sequence[BarDrinkSale]) -> list[RankedDrinkSale]:
    revenue_ranks = {
        s.id: rank
        for rank, s in competition_ranks(sales, key=lambda s: s.revenue_dkk, tie_key=lambda s: s.drink_name)
    }
    units_ranks = {
        s.id: rank
        for rank, s in competition_ranks(sales, key=lambda s: s.units_sold, tie_key=lambda s: s.drink_name)
    }
    ordered = sorted(sales, key=lambda s: (revenue_ranks[s.id], s.drink_name))
    return [
        RankedDrinkSale(
            sale=s,
            revenue_rank=revenue_ranks[s.id],
            units_rank=units_ranks[s.id],
        )
        for s in ordered
    ]


def ranked_drink_sales(sales: Sequence[BarDrinkSale]) -> list[RankedDrinkSale]:
    """B2: revenue and competition ranks (`revenue_rank`, `units_rank`) per drink.

    Ordered by `revenue_rank` ascending (ties alphabetical by `drink_name`). When `sales` spans multiple
    years (`year=all`), years are ordered ascending and each year's drinks are ranked within that year.
    """
    by_year: dict[int, list[BarDrinkSale]] = defaultdict(list)
    for s in sales:
        by_year[s.sales_year].append(s)
    return [ranked for yr in sorted(by_year) for ranked in _rank_single_year(by_year[yr])]


def category_kpis(
    sales: Sequence[BarDrinkSale],
    year: ReportYear = "all",
    categories: Sequence[DrinkCategory] = CATEGORY_ORDER,
) -> list[BarCategoryKpi]:
    """B3: percentage split between Cocktail and Coffee by unit volume and by revenue."""
    ordered = [c for c in CATEGORY_ORDER if c in categories]
    groups = [[s for s in sales if s.category is c] for c in ordered]
    units = [sum(s.units_sold for s in g) for g in groups]
    revenues = [round_half_up(total_revenue(g)) for g in groups]
    unit_shares = largest_remainder_shares(units)
    revenue_shares = largest_remainder_shares(revenues)
    return [
        BarCategoryKpi(
            year=year,
            category=category,
            drink_count=_drink_count(group),
            units_sold=units[i],
            unit_share_pct=unit_shares[i],
            revenue_dkk=revenues[i],
            revenue_share_pct=revenue_shares[i],
        )
        for i, (category, group) in enumerate(zip(ordered, groups))
    ]

