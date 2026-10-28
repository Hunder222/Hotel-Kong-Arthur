"""Use case: read the static room-type reference data."""

from __future__ import annotations

from hotel_api.business.domain.models import RoomType
from hotel_api.business.ports import RoomTypeRepository


class RoomTypeService:
    def __init__(self, room_types: RoomTypeRepository) -> None:
        self._room_types = room_types

    def list_all(self) -> list[RoomType]:
        return self._room_types.list_all()
