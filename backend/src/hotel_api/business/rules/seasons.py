"""Season mapping and calendar day counts (research R8, data-model §4.1). The single definition."""

from __future__ import annotations

import calendar
from collections.abc import Iterable
from datetime import date

from hotel_api.business.domain.models import Season

SEASON_ORDER: tuple[Season, ...] = (Season.LOW, Season.MID, Season.HIGH)

_MONTH_TO_SEASON: dict[int, Season] = {
    1: Season.LOW,
    2: Season.LOW,
    11: Season.LOW,
    3: Season.MID,
    4: Season.MID,
    5: Season.MID,
    9: Season.MID,
    10: Season.MID,
    6: Season.HIGH,
    7: Season.HIGH,
    8: Season.HIGH,
    12: Season.HIGH,
}


def season_of_month(month: int) -> Season:
    return _MONTH_TO_SEASON[month]


def season_of(day: date) -> Season:
    """A stay belongs entirely to the season of its check-in date."""
    return _MONTH_TO_SEASON[day.month]


def season_days(year: int) -> dict[Season, int]:
    """Days per season in `year`, from the calendar (2026: low 89, mid 153, high 123)."""
    days = {season: 0 for season in SEASON_ORDER}
    for month, season in _MONTH_TO_SEASON.items():
        days[season] += calendar.monthrange(year, month)[1]
    return days


def days_in_year(year: int) -> int:
    return 366 if calendar.isleap(year) else 365


def available_room_nights(room_count: int, days: int) -> int:
    """K1 denominator: rooms x days."""
    return room_count * days


def covered_years(years: Iterable[int]) -> range:
    """Every calendar year from the earliest to the latest of `years`, years in between included (FR-021).

    This is the period an all-time scope has capacity for: a year without a single booking between two busy
    years still had its rooms available. No years, no period.
    """
    found = list(years)
    return range(min(found), max(found) + 1) if found else range(0)


def calendar_days(years: Iterable[int]) -> int:
    """Days in the given calendar years, leap years included."""
    return sum(days_in_year(year) for year in years)


def season_days_over(years: Iterable[int]) -> dict[Season, int]:
    """Days per season summed over the given calendar years."""
    total = {season: 0 for season in SEASON_ORDER}
    for year in years:
        for season, days in season_days(year).items():
            total[season] += days
    return total
