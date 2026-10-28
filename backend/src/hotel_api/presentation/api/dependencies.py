"""Dependency providers for the routers.

Routers depend on the business services through the provider stubs below, so the presentation layer
never imports the data layer. The composition root (`main.py`) binds each stub to a request-scoped
factory that builds the repositories and the service (research R3).
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import Depends

from hotel_api.business.services.health_service import HealthService
from hotel_api.business.services.room_type_service import RoomTypeService

REPORTING_TIME_ZONE = "Europe/Copenhagen"


def get_health_service() -> HealthService:
    raise NotImplementedError("bound by the composition root (main.py)")


def get_room_type_service() -> RoomTypeService:
    raise NotImplementedError("bound by the composition root (main.py)")


def get_today() -> date:
    """Today's date in Europe/Copenhagen. Tests override this to freeze the clock."""
    return datetime.now(ZoneInfo(REPORTING_TIME_ZONE)).date()


def get_default_year(today: date = Depends(get_today)) -> int:
    """The default reporting year of the KPI endpoints: the current calendar year."""
    return today.year
