"""`/api/v1/bookings`: list, create, read, replace, delete (F1). Handlers only call the service."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response

from hotel_api.business.domain.models import Season
from hotel_api.business.services.booking_service import BookingService
from hotel_api.presentation.api.dependencies import get_booking_service
from hotel_api.presentation.api.schemas.bookings import Booking, BookingInput, BookingList, RoomTypeName

router = APIRouter(prefix="/api/v1/bookings", tags=["Bookings"])

BookingId = Annotated[int, Path(ge=1)]


@router.get("", response_model=BookingList, operation_id="listBookings")
def list_bookings(
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    season: Season | None = None,
    room_type: RoomTypeName | None = None,
    country: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    service: BookingService = Depends(get_booking_service),
) -> BookingList:
    bookings = service.list(year=year, season=season, room_type=room_type, country=country)
    return BookingList(items=[Booking.from_model(b) for b in bookings])


@router.post("", response_model=Booking, status_code=201, operation_id="createBooking")
def create_booking(
    body: BookingInput,
    response: Response,
    service: BookingService = Depends(get_booking_service),
) -> Booking:
    booking = service.create(body.model_dump())
    response.headers["Location"] = f"/api/v1/bookings/{booking.id}"
    return Booking.from_model(booking)


@router.get("/{booking_id}", response_model=Booking, operation_id="getBooking")
def get_booking(booking_id: BookingId, service: BookingService = Depends(get_booking_service)) -> Booking:
    return Booking.from_model(service.get(booking_id))


@router.put("/{booking_id}", response_model=Booking, operation_id="replaceBooking")
def replace_booking(
    booking_id: BookingId,
    body: BookingInput,
    service: BookingService = Depends(get_booking_service),
) -> Booking:
    return Booking.from_model(service.replace(booking_id, body.model_dump()))


@router.delete("/{booking_id}", status_code=204, response_class=Response, operation_id="deleteBooking")
def delete_booking(booking_id: BookingId, service: BookingService = Depends(get_booking_service)) -> Response:
    service.delete(booking_id)
    return Response(status_code=204)
