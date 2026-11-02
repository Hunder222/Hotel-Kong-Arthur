"""DTOs for the bar endpoints (`GET /api/v1/bar/drink-sales` and `GET /api/v1/kpis/bar/*`), matching openapi.yaml."""

from __future__ import annotations

from typing import Literal, Union

from pydantic import BaseModel, ConfigDict

from hotel_api.business.domain.models import (
    BarCategoryKpi as BarCategoryKpiModel,
    BarDrinkSale,
    BarPriceTierKpi as BarPriceTierKpiModel,
    BarSummary as BarSummaryModel,
    DrinkCategory,
    PriceTier,
    RankedDrinkSale as RankedDrinkSaleModel,
)
from hotel_api.presentation.api.schemas.common import AmountDkk

Year = Union[int, Literal["all"]]


class DrinkSale(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    year: int
    drink_name: str
    category: DrinkCategory
    unit_price_dkk: AmountDkk
    units_sold: int

    @classmethod
    def from_model(cls, sale: BarDrinkSale) -> DrinkSale:
        return cls(
            id=sale.id,
            year=sale.sales_year,
            drink_name=sale.drink_name,
            category=sale.category,
            unit_price_dkk=sale.unit_price_dkk,
            units_sold=sale.units_sold,
        )


class DrinkSaleList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DrinkSale]


class BarSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: Year
    drink_count: int
    units_sold: int
    total_revenue_dkk: AmountDkk

    @classmethod
    def from_model(cls, kpi: BarSummaryModel) -> BarSummary:
        return cls(
            year=kpi.year,
            drink_count=kpi.drink_count,
            units_sold=kpi.units_sold,
            total_revenue_dkk=kpi.total_revenue_dkk,
        )


class RankedDrinkSale(BaseModel):
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
    def from_model(cls, ranked: RankedDrinkSaleModel) -> RankedDrinkSale:
        return cls(
            id=ranked.id,
            year=ranked.year,
            drink_name=ranked.drink_name,
            category=ranked.category,
            unit_price_dkk=ranked.unit_price_dkk,
            units_sold=ranked.units_sold,
            revenue_dkk=ranked.revenue_dkk,
            revenue_rank=ranked.revenue_rank,
            units_rank=ranked.units_rank,
            price_tier=ranked.price_tier,
        )


class RankedDrinkSaleList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RankedDrinkSale]


class BarCategoryKpi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: Year
    category: DrinkCategory
    drink_count: int
    units_sold: int
    unit_share_pct: AmountDkk
    revenue_dkk: AmountDkk
    revenue_share_pct: AmountDkk

    @classmethod
    def from_model(cls, kpi: BarCategoryKpiModel) -> BarCategoryKpi:
        return cls(
            year=kpi.year,
            category=kpi.category,
            drink_count=kpi.drink_count,
            units_sold=kpi.units_sold,
            unit_share_pct=kpi.unit_share_pct,
            revenue_dkk=kpi.revenue_dkk,
            revenue_share_pct=kpi.revenue_share_pct,
        )


class BarCategoryKpiList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[BarCategoryKpi]


class BarPriceTierKpi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: Year
    price_tier: PriceTier
    price_from_dkk: AmountDkk
    price_to_dkk: AmountDkk | None
    drink_count: int
    units_sold: int
    unit_share_pct: AmountDkk
    revenue_dkk: AmountDkk
    revenue_share_pct: AmountDkk

    @classmethod
    def from_model(cls, kpi: BarPriceTierKpiModel) -> BarPriceTierKpi:
        return cls(
            year=kpi.year,
            price_tier=kpi.price_tier,
            price_from_dkk=kpi.price_from_dkk,
            price_to_dkk=kpi.price_to_dkk,
            drink_count=kpi.drink_count,
            units_sold=kpi.units_sold,
            unit_share_pct=kpi.unit_share_pct,
            revenue_dkk=kpi.revenue_dkk,
            revenue_share_pct=kpi.revenue_share_pct,
        )


class BarPriceTierKpiList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[BarPriceTierKpi]
