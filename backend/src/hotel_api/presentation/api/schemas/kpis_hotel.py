"""DTOs for the hotel KPI endpoints (contract: `HotelSummary`, `RoomTypeKpi`, `SeasonKpi`,
`RoomTypeSeasonKpi`, `CountryKpi` and their `{"items": [...]}` lists).

All five are complete, field for field as the contract. `HotelSummary`, `RoomTypeKpi` and `SeasonKpi`
carry revenue, occupancy, satisfaction and ALOS / ADR / revenue per booking (A7).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from hotel_api.business.domain.models import (
    CountryKpi as CountryKpiModel,
)
from hotel_api.business.domain.models import (
    HotelSummary as HotelSummaryModel,
)
from hotel_api.business.domain.models import (
    RoomTypeKpi as RoomTypeKpiModel,
)
from hotel_api.business.domain.models import (
    RoomTypeSeasonKpi as RoomTypeSeasonKpiModel,
)
from hotel_api.business.domain.models import (
    Season,
)
from hotel_api.business.domain.models import (
    SeasonKpi as SeasonKpiModel,
)
from hotel_api.presentation.api.schemas.common import AmountDkk, Percent


class HotelSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: int
    booking_count: int
    nights_sold: int
    total_revenue_dkk: AmountDkk
    available_room_nights: int
    occupancy_rate_pct: Percent
    review_count: int
    average_satisfaction: AmountDkk
    satisfied_share_pct: Percent
    average_length_of_stay_nights: AmountDkk
    average_daily_rate_dkk: AmountDkk
    average_revenue_per_booking_dkk: AmountDkk

    @classmethod
    def from_model(cls, m: HotelSummaryModel) -> HotelSummary:
        return cls(year=m.year, booking_count=m.booking_count, nights_sold=m.nights_sold,
                   total_revenue_dkk=m.total_revenue_dkk,
                   available_room_nights=m.available_room_nights, occupancy_rate_pct=m.occupancy_rate_pct,
                   review_count=m.review_count, average_satisfaction=m.average_satisfaction,
                   satisfied_share_pct=m.satisfied_share_pct,
                   average_length_of_stay_nights=m.average_length_of_stay_nights,
                   average_daily_rate_dkk=m.average_daily_rate_dkk,
                   average_revenue_per_booking_dkk=m.average_revenue_per_booking_dkk)


class RoomTypeKpi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: int
    revenue_rank: int
    room_type: str
    room_count: int
    booking_count: int
    nights_sold: int
    revenue_dkk: AmountDkk
    revenue_share_pct: Percent
    available_room_nights: int
    occupancy_rate_pct: Percent
    review_count: int
    average_satisfaction: AmountDkk
    satisfied_share_pct: Percent
    average_length_of_stay_nights: AmountDkk
    average_daily_rate_dkk: AmountDkk
    average_revenue_per_booking_dkk: AmountDkk

    @classmethod
    def from_model(cls, m: RoomTypeKpiModel) -> RoomTypeKpi:
        return cls(year=m.year, revenue_rank=m.revenue_rank, room_type=m.room_type, room_count=m.room_count,
                   booking_count=m.booking_count, nights_sold=m.nights_sold, revenue_dkk=m.revenue_dkk,
                   revenue_share_pct=m.revenue_share_pct,
                   available_room_nights=m.available_room_nights, occupancy_rate_pct=m.occupancy_rate_pct,
                   review_count=m.review_count, average_satisfaction=m.average_satisfaction,
                   satisfied_share_pct=m.satisfied_share_pct,
                   average_length_of_stay_nights=m.average_length_of_stay_nights,
                   average_daily_rate_dkk=m.average_daily_rate_dkk,
                   average_revenue_per_booking_dkk=m.average_revenue_per_booking_dkk)


class RoomTypeKpiList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RoomTypeKpi]


class SeasonKpi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: int
    season: Season
    season_days: int
    booking_count: int
    nights_sold: int
    revenue_dkk: AmountDkk
    revenue_share_pct: Percent
    available_room_nights: int
    occupancy_rate_pct: Percent
    review_count: int
    average_satisfaction: AmountDkk
    satisfied_share_pct: Percent
    average_length_of_stay_nights: AmountDkk
    average_daily_rate_dkk: AmountDkk
    average_revenue_per_booking_dkk: AmountDkk

    @classmethod
    def from_model(cls, m: SeasonKpiModel) -> SeasonKpi:
        return cls(year=m.year, season=m.season, season_days=m.season_days, booking_count=m.booking_count,
                   nights_sold=m.nights_sold, revenue_dkk=m.revenue_dkk, revenue_share_pct=m.revenue_share_pct,
                   available_room_nights=m.available_room_nights, occupancy_rate_pct=m.occupancy_rate_pct,
                   review_count=m.review_count, average_satisfaction=m.average_satisfaction,
                   satisfied_share_pct=m.satisfied_share_pct,
                   average_length_of_stay_nights=m.average_length_of_stay_nights,
                   average_daily_rate_dkk=m.average_daily_rate_dkk,
                   average_revenue_per_booking_dkk=m.average_revenue_per_booking_dkk)


class SeasonKpiList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SeasonKpi]


class RoomTypeSeasonKpi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: int
    room_type: str
    season: Season
    booking_count: int
    nights_sold: int
    revenue_dkk: AmountDkk

    @classmethod
    def from_model(cls, m: RoomTypeSeasonKpiModel) -> RoomTypeSeasonKpi:
        return cls(year=m.year, room_type=m.room_type, season=m.season, booking_count=m.booking_count,
                   nights_sold=m.nights_sold, revenue_dkk=m.revenue_dkk)


class RoomTypeSeasonKpiList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RoomTypeSeasonKpi]


class CountryKpi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: int
    revenue_rank: int
    country: str
    booking_count: int
    booking_share_pct: Percent
    nights_sold: int
    revenue_dkk: AmountDkk
    revenue_share_pct: Percent

    @classmethod
    def from_model(cls, m: CountryKpiModel) -> CountryKpi:
        return cls(year=m.year, revenue_rank=m.revenue_rank, country=m.country, booking_count=m.booking_count,
                   booking_share_pct=m.booking_share_pct, nights_sold=m.nights_sold, revenue_dkk=m.revenue_dkk,
                   revenue_share_pct=m.revenue_share_pct)


class CountryKpiList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[CountryKpi]
