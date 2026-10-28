"""`/api/v1/kpis/hotel/*`: authoritative hotel KPIs, one table per grain. Handlers only call the
service; every figure is computed once in the business layer."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from hotel_api.business.services.kpi_service import KpiService
from hotel_api.presentation.api.dependencies import get_kpi_service, report_year
from hotel_api.presentation.api.schemas.kpis_hotel import (
    CountryKpi,
    CountryKpiList,
    HotelSummary,
    RoomTypeKpi,
    RoomTypeKpiList,
    RoomTypeSeasonKpi,
    RoomTypeSeasonKpiList,
    SeasonKpi,
    SeasonKpiList,
)

router = APIRouter(prefix="/api/v1/kpis/hotel", tags=["Hotel KPIs"])


@router.get("/summary", response_model=HotelSummary, operation_id="getHotelSummary")
def get_hotel_summary(year: int = Depends(report_year), service: KpiService = Depends(get_kpi_service)) -> HotelSummary:
    return HotelSummary.from_model(service.summary(year))


@router.get("/by-room-type", response_model=RoomTypeKpiList, operation_id="listHotelKpisByRoomType")
def list_by_room_type(
    year: int = Depends(report_year), service: KpiService = Depends(get_kpi_service)
) -> RoomTypeKpiList:
    return RoomTypeKpiList(items=[RoomTypeKpi.from_model(r) for r in service.by_room_type(year)])


@router.get("/by-season", response_model=SeasonKpiList, operation_id="listHotelKpisBySeason")
def list_by_season(year: int = Depends(report_year), service: KpiService = Depends(get_kpi_service)) -> SeasonKpiList:
    return SeasonKpiList(items=[SeasonKpi.from_model(r) for r in service.by_season(year)])


@router.get(
    "/by-room-type-and-season", response_model=RoomTypeSeasonKpiList, operation_id="listHotelKpisByRoomTypeAndSeason"
)
def list_by_room_type_and_season(
    year: int = Depends(report_year), service: KpiService = Depends(get_kpi_service)
) -> RoomTypeSeasonKpiList:
    return RoomTypeSeasonKpiList(items=[RoomTypeSeasonKpi.from_model(r) for r in service.by_room_type_and_season(year)])


@router.get("/by-country", response_model=CountryKpiList, operation_id="listHotelKpisByCountry")
def list_by_country(
    year: int = Depends(report_year), service: KpiService = Depends(get_kpi_service)
) -> CountryKpiList:
    return CountryKpiList(items=[CountryKpi.from_model(r) for r in service.by_country(year)])
