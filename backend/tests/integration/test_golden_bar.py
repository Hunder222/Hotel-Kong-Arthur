"""Golden bar values from the sample data, through the real repository (T077, SC-003).

Expected numbers are in specs/001-hotel-analytics-platform/quickstart.md §6, computed from the CSV
independently of the application.

The API of `services/bar_service.py` (ranks are over all drinks of the year; `category` only selects rows):

    BarService(bar_sales_repository)
      .drink_sales(year, category=None) -> list[RankedDrinkSale]   ordered by revenue_rank, then name
      .summary(year)                    -> BarSummary
      .by_category(year)                -> [BarCategoryKpi(Cocktail), BarCategoryKpi(Coffee)]
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from hotel_api.business.domain.models import DrinkCategory
from hotel_api.data.connection import connection_scope
from hotel_api.data.repositories.bar_sales import MySqlBarSalesRepository
from hotel_api.presentation.cli.seed import main as seed_main

from hotel_api.business.services import bar_service

pytestmark = pytest.mark.integration

D = Decimal


@pytest.fixture()
def service(test_settings, clean_db, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()
    with connection_scope(test_settings) as conn:
        yield bar_service.BarService(MySqlBarSalesRepository(conn))


def test_total_bar_sales_b1(service):
    s = service.summary(2026)
    assert (s.drink_count, s.units_sold, s.total_revenue_dkk) == (30, 179958, D("13448640.34"))


def test_revenue_per_drink_b2(service):
    rows = service.drink_sales(2026)
    assert len(rows) == 30
    assert [r.revenue_rank for r in rows] == sorted(r.revenue_rank for r in rows)
    by_name = {r.sale.drink_name: r for r in rows}
    espresso = by_name["Espresso"]
    assert (espresso.sale.revenue_dkk, espresso.sale.units_sold, espresso.revenue_rank, espresso.units_rank) == (
        D("1012729.60"), 14656, 1, 1)
    assert (by_name["Margarita"].revenue_rank, by_name["Margarita"].sale.revenue_dkk) == (30, D("171101.67"))
    assert sum(r.sale.revenue_dkk for r in rows) == D("13448640.34")


def test_top_cocktail(service):
    cocktails = service.drink_sales(2026, category=DrinkCategory.COCKTAIL)
    assert len(cocktails) == 20
    assert (cocktails[0].sale.drink_name, cocktails[0].sale.revenue_dkk) == ("Mint Julep", D("524351.62"))
    # ranks are among all 30 drinks, not among the cocktails
    assert cocktails[0].revenue_rank > 1


def test_cocktail_vs_coffee_split_b3(service):
    cocktail, coffee = service.by_category(2026)
    assert (cocktail.category, cocktail.drink_count, cocktail.units_sold, cocktail.unit_share_pct,
            cocktail.revenue_dkk, cocktail.revenue_share_pct) == (
        DrinkCategory.COCKTAIL, 20, 62077, D("34.50"), D("7104755.43"), D("52.83"))
    assert (coffee.category, coffee.drink_count, coffee.units_sold, coffee.unit_share_pct,
            coffee.revenue_dkk, coffee.revenue_share_pct) == (
        DrinkCategory.COFFEE, 10, 117881, D("65.50"), D("6343884.91"), D("47.17"))
    assert cocktail.revenue_share_pct + coffee.revenue_share_pct == D("100.00")
    assert cocktail.unit_share_pct + coffee.unit_share_pct == D("100.00")


def test_a_year_without_sales_returns_both_categories_with_zeros(service):
    s = service.summary(2030)
    assert (s.drink_count, s.units_sold, s.total_revenue_dkk) == (0, 0, D("0.00"))
    assert service.drink_sales(2030) == []
    rows = service.by_category(2030)
    assert [r.category for r in rows] == [DrinkCategory.COCKTAIL, DrinkCategory.COFFEE]
    assert all(r.drink_count == 0 and r.revenue_dkk == 0 and r.revenue_share_pct == 0 and r.unit_share_pct == 0 for r in rows)
