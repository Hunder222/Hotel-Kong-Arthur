"""Dependency providers for the routers.

Routers depend on the business services through the provider stubs below, so the presentation layer
never imports the data layer. The composition root (`main.py`) binds each stub to a request-scoped
factory that builds the repositories and the service (research R3).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query
from fastapi.exceptions import RequestValidationError

from hotel_api.business.domain.models import ROOM_TYPE_NAMES, HotelFilters, ReportYear, Season
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


def _invalid_query(name: str, message: str) -> RequestValidationError:
    """A bad query parameter is answered with 400 Problem Details (see `errors.py`)."""
    return RequestValidationError([{"loc": ("query", name), "msg": message, "type": "value_error"}])


def report_year(
    year: Annotated[str | None, Query(description="A calendar year (2000-2100) or `all`.")] = None,
) -> ReportYear:
    """`year` as an int 2000-2100, or `all` (the default) for all-time totals (FR-021)."""
    if year is None or year == "all":
        return "all"
    if year.isascii() and year.isdigit() and 2000 <= int(year) <= 2100:
        return int(year)
    raise _invalid_query("year", "Must be a year between 2000 and 2100, or 'all'.")


def season_filter(season: Season | None = None) -> Season | None:
    """`season` is validated against the enum (low, mid, high) by FastAPI."""
    return season


def room_type_filter(room_type: str | None = None) -> str | None:
    if room_type is not None and room_type not in ROOM_TYPE_NAMES:
        raise _invalid_query("room_type", "Must be one of the 8 room types.")
    return room_type


def country_filter(country: Annotated[str | None, Query(max_length=100)] = None) -> str | None:
    """A trimmed, non-empty country name of at most 100 characters."""
    if country is None:
        return None
    trimmed = country.strip()
    if not trimmed:
        raise _invalid_query("country", "Must not be empty.")
    return trimmed


def hotel_filters(
    year: ReportYear = Depends(report_year),
    season: Season | None = Depends(season_filter),
    room_type: str | None = Depends(room_type_filter),
    country: str | None = Depends(country_filter),
) -> HotelFilters:
    return HotelFilters(year=year, season=season, room_type=room_type, country=country)
