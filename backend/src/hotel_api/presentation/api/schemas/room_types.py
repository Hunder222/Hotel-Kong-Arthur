"""DTOs for `GET /api/v1/room-types` (contract: `RoomType`, `SeasonRate`, `RoomTypeList`)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from hotel_api.business.domain.models import RoomType as RoomTypeModel
from hotel_api.business.domain.models import Season
from hotel_api.business.rules.seasons import SEASON_ORDER
from hotel_api.presentation.api.schemas.common import AmountDkk


class SeasonRate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    season: Season
    min_nightly_dkk: AmountDkk
    max_nightly_dkk: AmountDkk
    standard_nightly_dkk: AmountDkk


class RoomType(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    name_da: str
    room_count: int
    max_guests: int
    rates: list[SeasonRate]

    @classmethod
    def from_model(cls, room_type: RoomTypeModel) -> RoomType:
        return cls(
            name=room_type.name,
            name_da=room_type.name_da,
            room_count=room_type.room_count,
            max_guests=room_type.max_guests,
            rates=[
                SeasonRate(
                    season=rate.season,
                    min_nightly_dkk=rate.min_nightly_dkk,
                    max_nightly_dkk=rate.max_nightly_dkk,
                    standard_nightly_dkk=rate.standard_nightly_dkk,
                )
                for rate in (room_type.rates[season] for season in SEASON_ORDER)
            ],
        )


class RoomTypeList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RoomType]
