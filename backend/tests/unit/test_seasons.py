from datetime import date

import pytest

from hotel_api.business.domain.models import Season
from hotel_api.business.rules.seasons import (
    available_room_nights,
    days_in_year,
    season_days,
    season_of,
    season_of_month,
)

pytestmark = pytest.mark.unit

LOW, MID, HIGH = Season.LOW, Season.MID, Season.HIGH


@pytest.mark.parametrize(
    "month,expected",
    [(1, LOW), (2, LOW), (3, MID), (4, MID), (5, MID), (6, HIGH), (7, HIGH), (8, HIGH),
     (9, MID), (10, MID), (11, LOW), (12, HIGH)],
)
def test_month_mapping(month, expected):
    assert season_of_month(month) is expected


def test_season_of_uses_check_in_month():
    assert season_of(date(2026, 7, 14)) is HIGH
    assert season_of(date(2026, 11, 30)) is LOW
    assert season_of(date(2026, 10, 31)) is MID


def test_season_days_2026():
    days = season_days(2026)
    assert days == {LOW: 89, MID: 153, HIGH: 123}
    assert sum(days.values()) == 365 == days_in_year(2026)


def test_season_days_leap_year():
    days = season_days(2028)
    assert days[LOW] == 90
    assert sum(days.values()) == 366 == days_in_year(2028)


def test_available_room_nights():
    assert available_room_nights(214, 365) == 78110
    assert available_room_nights(214, 89) == 19046
    assert available_room_nights(214, 153) == 32742
    assert available_room_nights(214, 123) == 26322
    assert available_room_nights(26, 365) == 9490
