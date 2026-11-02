"""`GET /api/v1/kpis/hotel/*`: hotel KPIs calculated in the business layer (`Hotel Analytics`)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from hotel_api.business.domain.models import HotelFilters
from hotel_api.business.services.kpi_service import KpiService
from hotel_api.presentation.api.dependencies import get_kpi_service, hotel_filters
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

router = APIRouter(prefix="/api/v1/kpis/hotel", tags=["Hotel Analytics"])


@router.get("/summary", response_model=HotelSummary, operation_id="getHotelSummary")
def get_hotel_summary(
    filters: HotelFilters = Depends(hotel_filters),
    service: KpiService = Depends(get_kpi_service),
) -> HotelSummary:
    return HotelSummary.from_model(service.summary(filters))


@router.get("/by-room-type", response_model=RoomTypeKpiList, operation_id="listHotelKpisByRoomType")
def list_by_room_type(
    filters: HotelFilters = Depends(hotel_filters),
    service: KpiService = Depends(get_kpi_service),
) -> RoomTypeKpiList:
    return RoomTypeKpiList(items=[RoomTypeKpi.from_model(k) for k in service.by_room_type(filters)])


@router.get("/by-season", response_model=SeasonKpiList, operation_id="listHotelKpisBySeason")
def list_by_season(
    filters: HotelFilters = Depends(hotel_filters),
    service: KpiService = Depends(get_kpi_service),
) -> SeasonKpiList:
    return SeasonKpiList(items=[SeasonKpi.from_model(k) for k in service.by_season(filters)])


@router.get(
    "/by-room-type-and-season",
    response_model=RoomTypeSeasonKpiList,
    operation_id="listHotelKpisByRoomTypeAndSeason",
)
def list_by_room_type_and_season(
    filters: HotelFilters = Depends(hotel_filters),
    service: KpiService = Depends(get_kpi_service),
) -> RoomTypeSeasonKpiList:
    return RoomTypeSeasonKpiList(
        items=[RoomTypeSeasonKpi.from_model(k) for k in service.by_room_type_and_season(filters)]
    )


@router.get("/by-country", response_model=CountryKpiList, operation_id="listHotelKpisByCountry")
def list_by_country(
    filters: HotelFilters = Depends(hotel_filters),
    service: KpiService = Depends(get_kpi_service),
) -> CountryKpiList:
    return CountryKpiList(items=[CountryKpi.from_model(k) for k in service.by_country(filters)])
