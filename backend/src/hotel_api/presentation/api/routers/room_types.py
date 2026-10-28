"""`GET /api/v1/room-types`."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from hotel_api.business.services.room_type_service import RoomTypeService
from hotel_api.presentation.api.dependencies import get_room_type_service
from hotel_api.presentation.api.schemas.room_types import RoomType, RoomTypeList

router = APIRouter(prefix="/api/v1", tags=["Reference data"])


@router.get("/room-types", response_model=RoomTypeList, operation_id="listRoomTypes")
def list_room_types(service: RoomTypeService = Depends(get_room_type_service)) -> RoomTypeList:
    return RoomTypeList(items=[RoomType.from_model(r) for r in service.list_all()])
