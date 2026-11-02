"""Bar price tiers (FR-016, data-model §4.3): budget < 70 DKK <= standard < 110 DKK <= premium."""

from __future__ import annotations

from decimal import Decimal

from hotel_api.business.domain.models import PriceTier

STANDARD_FROM_DKK = Decimal("70.00")
PREMIUM_FROM_DKK = Decimal("110.00")

PRICE_TIER_ORDER: tuple[PriceTier, ...] = (
    PriceTier.BUDGET,
    PriceTier.STANDARD,
    PriceTier.PREMIUM,
)
TIER_ORDER = PRICE_TIER_ORDER


def classify_price_tier(unit_price_dkk: Decimal) -> PriceTier:
    if unit_price_dkk >= PREMIUM_FROM_DKK:
        return PriceTier.PREMIUM
    if unit_price_dkk >= STANDARD_FROM_DKK:
        return PriceTier.STANDARD
    return PriceTier.BUDGET


tier_for_price = classify_price_tier


def price_tier_bounds(tier: PriceTier) -> tuple[Decimal, Decimal | None]:
    """(inclusive lower bound, exclusive upper bound or None for the top tier) of a tier's unit price."""
    if tier is PriceTier.BUDGET:
        return Decimal("0.00"), STANDARD_FROM_DKK
    if tier is PriceTier.STANDARD:
        return STANDARD_FROM_DKK, PREMIUM_FROM_DKK
    return PREMIUM_FROM_DKK, None


tier_bounds = price_tier_bounds

