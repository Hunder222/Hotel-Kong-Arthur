"""Unit tests for bar price-tier classification and bounds (T054, FR-016, data-model §4.3)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from hotel_api.business.domain.models import PriceTier
from hotel_api.business.rules.price_tiers import (
    PREMIUM_FROM_DKK,
    PRICE_TIER_ORDER,
    STANDARD_FROM_DKK,
    classify_price_tier,
    price_tier_bounds,
    tier_bounds,
    tier_for_price,
)

pytestmark = pytest.mark.unit

D = Decimal


def test_price_tier_canonical_order_and_constants():
    assert PRICE_TIER_ORDER == (PriceTier.BUDGET, PriceTier.STANDARD, PriceTier.PREMIUM)
    assert STANDARD_FROM_DKK == D("70.00")
    assert PREMIUM_FROM_DKK == D("110.00")


@pytest.mark.parametrize(
    ("unit_price", "expected"),
    [
        ("0.01", PriceTier.BUDGET),
        ("40.84", PriceTier.BUDGET),
        ("69.10", PriceTier.BUDGET),
        ("69.99", PriceTier.BUDGET),
        ("70.00", PriceTier.STANDARD),
        ("72.47", PriceTier.STANDARD),
        ("109.99", PriceTier.STANDARD),
        ("110.00", PriceTier.PREMIUM),
        ("142.38", PriceTier.PREMIUM),
        ("250.00", PriceTier.PREMIUM),
    ],
)
def test_classify_price_tier_at_and_around_boundaries(unit_price: str, expected: PriceTier):
    assert classify_price_tier(D(unit_price)) is expected
    assert tier_for_price(D(unit_price)) is expected


def test_price_tier_bounds_for_all_three_tiers():
    assert price_tier_bounds(PriceTier.BUDGET) == (D("0.00"), D("70.00"))
    assert price_tier_bounds(PriceTier.STANDARD) == (D("70.00"), D("110.00"))
    assert price_tier_bounds(PriceTier.PREMIUM) == (D("110.00"), None)
    assert [tier_bounds(t) for t in PRICE_TIER_ORDER] == [
        (D("0.00"), D("70.00")),
        (D("70.00"), D("110.00")),
        (D("110.00"), None),
    ]

