"""DTOs for the bar endpoints (contract: `DrinkSale`, `DrinkSaleList`, `BarSummary`, `BarCategoryKpi`, lists)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from hotel_api.business.domain.models import BarCategoryKpi as BarCategoryKpiModel
from hotel_api.business.domain.models import BarPriceTierKpi as BarPriceTierKpiModel
from hotel_api.business.domain.models import BarSummary as BarSummaryModel
from hotel_api.business.domain.models import DrinkCategory, PriceTier, RankedDrinkSale
from hotel_api.presentation.api.schemas.common import AmountDkk, Percent


class DrinkSale(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    year: int
    drink_name: str
    category: DrinkCategory
    unit_price_dkk: AmountDkk
    units_sold: int
    revenue_dkk: AmountDkk
    revenue_rank: int
    units_rank: int
    price_tier: PriceTier

    @classmethod
    def from_model(cls, ranked: RankedDrinkSale) -> DrinkSale:
        s = ranked.sale
        return cls(id=s.id, year=s.sales_year, drink_name=s.drink_name, category=s.category,
                   unit_price_dkk=s.unit_price_dkk, units_sold=s.units_sold, revenue_dkk=s.revenue_dkk,
                   revenue_rank=ranked.revenue_rank, units_rank=ranked.units_rank, price_tier=s.price_tier)


class DrinkSaleList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DrinkSale]


class BarSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: int
    drink_count: int
    units_sold: int
    total_revenue_dkk: AmountDkk

    @classmethod
    def from_model(cls, m: BarSummaryModel) -> BarSummary:
        return cls(year=m.year, drink_count=m.drink_count, units_sold=m.units_sold,
                   total_revenue_dkk=m.total_revenue_dkk)


class BarCategoryKpi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: int
    category: DrinkCategory
    drink_count: int
    units_sold: int
    unit_share_pct: Percent
    revenue_dkk: AmountDkk
    revenue_share_pct: Percent

    @classmethod
    def from_model(cls, m: BarCategoryKpiModel) -> BarCategoryKpi:
        return cls(year=m.year, category=m.category, drink_count=m.drink_count, units_sold=m.units_sold,
                   unit_share_pct=m.unit_share_pct, revenue_dkk=m.revenue_dkk,
                   revenue_share_pct=m.revenue_share_pct)


class BarCategoryKpiList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[BarCategoryKpi]


class BarPriceTierKpi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: int
    price_tier: PriceTier
    price_from_dkk: AmountDkk
    price_to_dkk: AmountDkk | None
    drink_count: int
    units_sold: int
    unit_share_pct: Percent
    revenue_dkk: AmountDkk
    revenue_share_pct: Percent

    @classmethod
    def from_model(cls, m: BarPriceTierKpiModel) -> BarPriceTierKpi:
        return cls(year=m.year, price_tier=m.price_tier, price_from_dkk=m.price_from_dkk,
                   price_to_dkk=m.price_to_dkk, drink_count=m.drink_count, units_sold=m.units_sold,
                   unit_share_pct=m.unit_share_pct, revenue_dkk=m.revenue_dkk,
                   revenue_share_pct=m.revenue_share_pct)


class BarPriceTierKpiList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[BarPriceTierKpi]
