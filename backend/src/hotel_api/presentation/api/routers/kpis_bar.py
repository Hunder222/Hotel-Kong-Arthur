"""`GET /api/v1/kpis/bar/*`: cocktail bar KPIs calculated in the business layer (`Hotel Analytics`)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from hotel_api.business.domain.models import BarFilters
from hotel_api.business.services.kpi_service import KpiService
from hotel_api.presentation.api.dependencies import bar_filters, get_kpi_service
from hotel_api.presentation.api.schemas.bar import (
    BarCategoryKpi,
    BarCategoryKpiList,
    BarSummary,
    RankedDrinkSale,
    RankedDrinkSaleList,
)

router = APIRouter(prefix="/api/v1/kpis/bar", tags=["Hotel Analytics"])


@router.get("/summary", response_model=BarSummary, operation_id="getBarSummary")
def get_bar_summary(
    filters: BarFilters = Depends(bar_filters),
    service: KpiService = Depends(get_kpi_service),
) -> BarSummary:
    return BarSummary.from_model(service.bar_summary(filters))


@router.get("/by-drink", response_model=RankedDrinkSaleList, operation_id="listBarKpisByDrink")
def list_by_drink(
    filters: BarFilters = Depends(bar_filters),
    service: KpiService = Depends(get_kpi_service),
) -> RankedDrinkSaleList:
    return RankedDrinkSaleList(items=[RankedDrinkSale.from_model(r) for r in service.bar_by_drink(filters)])


@router.get("/by-category", response_model=BarCategoryKpiList, operation_id="listBarKpisByCategory")
def list_by_category(
    filters: BarFilters = Depends(bar_filters),
    service: KpiService = Depends(get_kpi_service),
) -> BarCategoryKpiList:
    return BarCategoryKpiList(items=[BarCategoryKpi.from_model(r) for r in service.bar_by_category(filters)])

