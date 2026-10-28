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


TIER_ORDER: tuple[PriceTier, ...] = (PriceTier.BUDGET, PriceTier.STANDARD, PriceTier.PREMIUM)


def tier_bounds(tier: PriceTier) -> tuple[Decimal, Decimal | None]:
    """(inclusive lower bound, exclusive upper bound or None for the top tier) of a tier's unit price."""
    if tier is PriceTier.BUDGET:
        return Decimal("0"), STANDARD_FROM_DKK
    if tier is PriceTier.STANDARD:
        return STANDARD_FROM_DKK, PREMIUM_FROM_DKK
    return PREMIUM_FROM_DKK, None
