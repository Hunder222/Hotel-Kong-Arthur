"""`/api/v1/kpis/bar/*`: B1 summary and B3 cocktail/coffee split. Handlers only call the service."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from hotel_api.business.services.bar_service import BarService
from hotel_api.presentation.api.dependencies import get_bar_service, report_year
from hotel_api.presentation.api.schemas.bar import BarCategoryKpi, BarCategoryKpiList, BarSummary

router = APIRouter(prefix="/api/v1/kpis/bar", tags=["Bar KPIs"])


@router.get("/summary", response_model=BarSummary, operation_id="getBarSummary")
def get_bar_summary(year: int = Depends(report_year), service: BarService = Depends(get_bar_service)) -> BarSummary:
    return BarSummary.from_model(service.summary(year))


@router.get("/by-category", response_model=BarCategoryKpiList, operation_id="listBarKpisByCategory")
def list_by_category(
    year: int = Depends(report_year), service: BarService = Depends(get_bar_service)
) -> BarCategoryKpiList:
    return BarCategoryKpiList(items=[BarCategoryKpi.from_model(r) for r in service.by_category(year)])
