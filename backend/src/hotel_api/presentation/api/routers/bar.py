"""`GET /api/v1/bar/drink-sales` (B2): revenue, ranks and price tier per drink. Read-only."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from hotel_api.business.domain.models import DrinkCategory
from hotel_api.business.services.bar_service import BarService
from hotel_api.presentation.api.dependencies import get_bar_service, report_year
from hotel_api.presentation.api.schemas.bar import DrinkSale, DrinkSaleList

router = APIRouter(prefix="/api/v1/bar", tags=["Bar"])


@router.get("/drink-sales", response_model=DrinkSaleList, operation_id="listDrinkSales")
def list_drink_sales(
    category: DrinkCategory | None = None,
    year: int | None = Depends(report_year),
    service: BarService = Depends(get_bar_service),
) -> DrinkSaleList:
    return DrinkSaleList(items=[DrinkSale.from_model(r) for r in service.drink_sales(year, category)])
