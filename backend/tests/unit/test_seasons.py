from datetime import date

import pytest

from hotel_api.business.domain.models import Season
from hotel_api.business.rules.seasons import (
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



def test_days_in_season_matches_the_calendar_including_leap_years():
    from hotel_api.business.rules.seasons import days_in_season

    assert [days_in_season(2026, season) for season in Season] == [89, 153, 123]
    assert [days_in_season(2024, season) for season in Season] == [90, 153, 123]
