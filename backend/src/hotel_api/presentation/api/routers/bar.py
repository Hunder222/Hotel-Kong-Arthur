"""`GET /api/v1/bar/drink-sales`: lobby bar drink sales. Read-only."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from hotel_api.business.services.bar_service import BarService
from hotel_api.presentation.api.dependencies import get_bar_service
from hotel_api.presentation.api.schemas.bar import DrinkSale, DrinkSaleList

router = APIRouter(prefix="/api/v1/bar", tags=["Bar"])


@router.get("/drink-sales", response_model=DrinkSaleList, operation_id="listDrinkSales")
def list_drink_sales(
    service: BarService = Depends(get_bar_service),
) -> DrinkSaleList:
    return DrinkSaleList(items=[DrinkSale.from_model(s) for s in service.drink_sales()])

