"""DTOs for the bar endpoint (`GET /api/v1/bar/drink-sales`: `DrinkSale`, `DrinkSaleList`)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from hotel_api.business.domain.models import BarDrinkSale, DrinkCategory
from hotel_api.presentation.api.schemas.common import AmountDkk


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

