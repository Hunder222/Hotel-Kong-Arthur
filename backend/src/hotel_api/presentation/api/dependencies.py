"""Dependency providers for the routers.

Routers depend on the business services through the provider stubs below, so the presentation layer
never imports the data layer. The composition root (`main.py`) binds each stub to a request-scoped
factory that builds the repositories and the service (research R3).
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Query
from pydantic import BeforeValidator, Field

from hotel_api.business.services.bar_service import BarService
from hotel_api.business.services.booking_service import BookingService
from hotel_api.business.services.health_service import HealthService
from hotel_api.business.services.kpi_service import KpiService
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


def get_kpi_service() -> KpiService:
    raise NotImplementedError("bound by the composition root (main.py)")


def _all_means_every_year(value: Any) -> Any:
    """`all` selects every year (all-time, FR-021) and becomes None; any other value goes on to the 2000-2100 check."""
    return None if value == "all" else value


def report_year(
    year: Annotated[
        # The bounds sit on the inner int: pydantic applies a bound on the outer type after the validator below,
        # where the None that `all` turns into would fail it.
        Annotated[int, Field(ge=2000, le=2100)] | None,
        BeforeValidator(_all_means_every_year),
        Query(description="A calendar year from 2000 to 2100, or `all`. Omitted means `all`."),
    ] = None,
) -> int | None:
    """The `year` query parameter of the KPI and bar endpoints: a year from 2000 to 2100, or None for all-time
    (`year=all`, or no `year` at all; FR-021)."""
    return year
