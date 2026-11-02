"""DTOs for the hotel `Hotel Analytics` endpoints (`/api/v1/kpis/hotel/*`), matching openapi.yaml."""

from __future__ import annotations

from typing import Literal, Union

from pydantic import BaseModel, ConfigDict

from hotel_api.business.domain.models import (
    CountryKpi as CountryKpiModel,
    RoomTypeKpi as RoomTypeKpiModel,
    RoomTypeSeasonKpi as RoomTypeSeasonKpiModel,
    Season,
    SeasonKpi as SeasonKpiModel,
)
from hotel_api.presentation.api.schemas.common import AmountDkk

# Percentages, rates and averages leave the API as JSON numbers, like money.
Year = Union[int, Literal["all"]]


class RoomTypeKpi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: Year
    revenue_rank: int
    room_type: str
    room_count: int
    booking_count: int
    nights_sold: int
    revenue_dkk: AmountDkk
    revenue_share_pct: AmountDkk
    available_room_nights: int
    occupancy_rate_pct: AmountDkk
    review_count: int
    average_satisfaction: AmountDkk
    satisfied_share_pct: AmountDkk
    average_length_of_stay_nights: AmountDkk
    average_daily_rate_dkk: AmountDkk
    average_revenue_per_booking_dkk: AmountDkk

    @classmethod
    def from_model(cls, kpi: RoomTypeKpiModel) -> RoomTypeKpi:
        return cls(
            year=kpi.year,
            revenue_rank=kpi.revenue_rank,
            room_type=kpi.room_type,
            room_count=kpi.room_count,
            booking_count=kpi.stay.booking_count,
            nights_sold=kpi.stay.nights_sold,
            revenue_dkk=kpi.stay.revenue_dkk,
            revenue_share_pct=kpi.revenue_share_pct,
            available_room_nights=kpi.available_room_nights,
            occupancy_rate_pct=kpi.occupancy_rate_pct,
            review_count=kpi.satisfaction.review_count,
            average_satisfaction=kpi.satisfaction.average_satisfaction,
            satisfied_share_pct=kpi.satisfaction.satisfied_share_pct,
            average_length_of_stay_nights=kpi.stay.average_length_of_stay_nights,
            average_daily_rate_dkk=kpi.stay.average_daily_rate_dkk,
            average_revenue_per_booking_dkk=kpi.stay.average_revenue_per_booking_dkk,
        )


class RoomTypeKpiList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RoomTypeKpi]


class SeasonKpi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: Year
    season: Season
    season_days: int
    booking_count: int
    nights_sold: int
    revenue_dkk: AmountDkk
    revenue_share_pct: AmountDkk
    available_room_nights: int
    occupancy_rate_pct: AmountDkk
    review_count: int
    average_satisfaction: AmountDkk
    satisfied_share_pct: AmountDkk
    average_length_of_stay_nights: AmountDkk
    average_daily_rate_dkk: AmountDkk
    average_revenue_per_booking_dkk: AmountDkk

    @classmethod
    def from_model(cls, kpi: SeasonKpiModel) -> SeasonKpi:
        return cls(
            year=kpi.year,
            season=kpi.season,
            season_days=kpi.season_days,
            booking_count=kpi.stay.booking_count,
            nights_sold=kpi.stay.nights_sold,
            revenue_dkk=kpi.stay.revenue_dkk,
            revenue_share_pct=kpi.revenue_share_pct,
            available_room_nights=kpi.available_room_nights,
            occupancy_rate_pct=kpi.occupancy_rate_pct,
            review_count=kpi.satisfaction.review_count,
            average_satisfaction=kpi.satisfaction.average_satisfaction,
            satisfied_share_pct=kpi.satisfaction.satisfied_share_pct,
            average_length_of_stay_nights=kpi.stay.average_length_of_stay_nights,
            average_daily_rate_dkk=kpi.stay.average_daily_rate_dkk,
            average_revenue_per_booking_dkk=kpi.stay.average_revenue_per_booking_dkk,
        )


class SeasonKpiList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SeasonKpi]


class RoomTypeSeasonKpi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: Year
    room_type: str
    season: Season
    room_count: int
    season_days: int
    booking_count: int
    nights_sold: int
    revenue_dkk: AmountDkk
    available_room_nights: int
    occupancy_rate_pct: AmountDkk
    average_length_of_stay_nights: AmountDkk
    average_daily_rate_dkk: AmountDkk
    average_revenue_per_booking_dkk: AmountDkk

    @classmethod
    def from_model(cls, kpi: RoomTypeSeasonKpiModel) -> RoomTypeSeasonKpi:
        return cls(
            year=kpi.year,
            room_type=kpi.room_type,
            season=kpi.season,
            room_count=kpi.room_count,
            season_days=kpi.season_days,
            booking_count=kpi.stay.booking_count,
            nights_sold=kpi.stay.nights_sold,
            revenue_dkk=kpi.stay.revenue_dkk,
            available_room_nights=kpi.available_room_nights,
            occupancy_rate_pct=kpi.occupancy_rate_pct,
            average_length_of_stay_nights=kpi.stay.average_length_of_stay_nights,
            average_daily_rate_dkk=kpi.stay.average_daily_rate_dkk,
            average_revenue_per_booking_dkk=kpi.stay.average_revenue_per_booking_dkk,
        )


class RoomTypeSeasonKpiList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RoomTypeSeasonKpi]


class CountryKpi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: Year
    revenue_rank: int
    country: str
    booking_count: int
    booking_share_pct: AmountDkk
    nights_sold: int
    revenue_dkk: AmountDkk
    revenue_share_pct: AmountDkk

    @classmethod
    def from_model(cls, kpi: CountryKpiModel) -> CountryKpi:
        return cls(
            year=kpi.year,
            revenue_rank=kpi.revenue_rank,
            country=kpi.country,
            booking_count=kpi.booking_count,
            booking_share_pct=kpi.booking_share_pct,
            nights_sold=kpi.nights_sold,
            revenue_dkk=kpi.revenue_dkk,
            revenue_share_pct=kpi.revenue_share_pct,
        )


class CountryKpiList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[CountryKpi]
