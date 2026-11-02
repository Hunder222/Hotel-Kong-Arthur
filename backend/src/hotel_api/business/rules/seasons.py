"""Season mapping rule (research R8, data-model §4.1). The single definition."""

from __future__ import annotations

from datetime import date, timedelta

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



def days_in_year(year: int) -> int:
    """Calendar days in `year` (366 in leap year, 365 otherwise)."""
    return (date(year + 1, 1, 1) - date(year, 1, 1)).days


def days_in_season(year: int, season: Season) -> int:
    """Calendar days of `year` that fall in `season` (2026: 89 low, 153 mid, 123 high; 90 low in a leap year)."""
    first = date(year, 1, 1)
    days = (date(year + 1, 1, 1) - first).days
    return sum(1 for offset in range(days) if season_of(first + timedelta(days=offset)) is season)
