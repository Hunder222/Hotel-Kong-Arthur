"""Dependency providers for the routers.

Routers depend on the business services through the provider stubs below, so the presentation layer
never imports the data layer. The composition root (`main.py`) binds each stub to a request-scoped
factory that builds the repositories and the service (research R3).
"""

from __future__ import annotations

from hotel_api.business.services.bar_service import BarService
from hotel_api.business.services.booking_service import BookingService
from hotel_api.business.services.health_service import HealthService
from hotel_api.business.services.review_service import ReviewService
from hotel_api.business.services.room_type_service import RoomTypeService


def get_health_service() -> HealthService:
    raise NotImplementedError("bound by the composition root (main.py)")


def get_room_type_service() -> RoomTypeService:
    raise NotImplementedError("bound by the composition root (main.py)")


def get_booking_service() -> BookingService:
    raise NotImplementedError("bound by the composition root (main.py)")


def get_review_service() -> ReviewService:
    raise NotImplementedError("bound by the composition root (main.py)")


def get_bar_service() -> BarService:
    raise NotImplementedError("bound by the composition root (main.py)")

