"""Bar price tiers (FR-016, data-model §4.4). The single definition.

budget: unit price < 70 DKK; standard: 70 <= price < 110; premium: price >= 110.
"""

from __future__ import annotations

from decimal import Decimal

from hotel_api.business.domain.models import PriceTier

STANDARD_FROM_DKK = Decimal("70")
PREMIUM_FROM_DKK = Decimal("110")


def tier_for_price(unit_price_dkk: Decimal) -> PriceTier:
    if unit_price_dkk >= PREMIUM_FROM_DKK:
        return PriceTier.PREMIUM
    if unit_price_dkk >= STANDARD_FROM_DKK:
        return PriceTier.STANDARD
    return PriceTier.BUDGET
