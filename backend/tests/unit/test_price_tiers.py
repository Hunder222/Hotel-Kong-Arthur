"""Price tiers (T074, FR-016, data-model §4.4): budget < 70, standard 70 <= price < 110, premium >= 110 DKK.

Skipped until `rules/price_tiers.py` exists (T078); remove the guard then and mark T074 done.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from hotel_api.business.domain.models import PriceTier

price_tiers = pytest.importorskip("hotel_api.business.rules.price_tiers", reason="price_tiers.py not written yet (T078)")

pytestmark = pytest.mark.unit

D = Decimal


@pytest.mark.parametrize(
    "price,tier",
    [
        ("0.01", PriceTier.BUDGET),
        ("33.43", PriceTier.BUDGET),
        ("69.99", PriceTier.BUDGET),
        ("70", PriceTier.STANDARD),
        ("70.00", PriceTier.STANDARD),
        ("72.47", PriceTier.STANDARD),
        ("109.99", PriceTier.STANDARD),
        ("110", PriceTier.PREMIUM),
        ("110.00", PriceTier.PREMIUM),
        ("149.48", PriceTier.PREMIUM),
        ("1000", PriceTier.PREMIUM),
    ],
)
def test_tier_boundaries(price, tier):
    assert price_tiers.tier_for_price(D(price)) is tier


def test_the_sample_menu_splits_into_three_tiers_of_ten(room_types):
    # the 30 sample drinks: all 10 coffees are budget, the 20 cocktails split 10 standard / 10 premium
    import csv
    from pathlib import Path

    path = Path(__file__).resolve().parents[3] / "context" / "teacher" / "drinks_menu_with_sales.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline=""), delimiter=";"))
    tiers = [price_tiers.tier_for_price(D(r["Price (DKK)"].replace(",", "."))) for r in rows]
    assert [tiers.count(t) for t in (PriceTier.BUDGET, PriceTier.STANDARD, PriceTier.PREMIUM)] == [10, 10, 10]
    assert all(t is PriceTier.BUDGET for t, r in zip(tiers, rows) if r["Category"] == "Coffee")


def test_a_drink_sale_reports_its_tier():
    from hotel_api.business.domain.models import BarDrinkSale, DrinkCategory

    sale = BarDrinkSale(1, 2026, "Negroni", DrinkCategory.COCKTAIL, D("149.48"), 2691)
    assert sale.price_tier is PriceTier.PREMIUM
