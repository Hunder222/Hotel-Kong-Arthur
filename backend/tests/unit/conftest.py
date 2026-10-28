"""Room types as seeded by db/init/02_reference_data.sql (data-model.md §2), without a database."""

from decimal import Decimal

import pytest

from hotel_api.business.domain.models import RoomType, Season, SeasonRate

# name, name_da, rooms, max_guests, {season: (min, max)}; standard = midpoint
_TABLE = [
    ("Standard Single", "Standard enkeltværelse", 27, 1, (900, 1200), (1000, 1300), (1200, 1500)),
    ("Grand Lit", "Grand lit værelse", 27, 2, (1100, 1400), (1200, 1600), (1400, 1800)),
    ("Standard Double", "Standard dobbeltværelse", 27, 2, (1200, 1600), (1300, 1700), (1600, 2000)),
    ("Superior Double", "Superior dobbeltværelse", 27, 2, (1400, 1800), (1500, 2000), (1800, 2200)),
    ("Junior Suite", "Junior suite", 27, 2, (1800, 2200), (2000, 2400), (2200, 2500)),
    ("Spa Executive", "Spa executive", 27, 2, (2000, 2500), (2200, 2600), (2500, 2800)),
    ("Suite", "Suite", 26, 2, (2500, 3000), (2700, 3300), (3000, 3500)),
    ("LOFT Suite", "LOFT suite", 26, 3, (3000, 3500), (3200, 3800), (3500, 4000)),
]


@pytest.fixture(scope="session")
def room_types() -> list[RoomType]:
    result = []
    for i, (name, name_da, rooms, guests, low, mid, high) in enumerate(_TABLE, start=1):
        rates = {
            season: SeasonRate(season, Decimal(lo), Decimal(hi), Decimal((lo + hi) // 2))
            for season, (lo, hi) in zip((Season.LOW, Season.MID, Season.HIGH), (low, mid, high))
        }
        result.append(RoomType(i, name, name_da, rooms, guests, rates))
    return result


@pytest.fixture(scope="session")
def by_name(room_types):
    return {r.name: r for r in room_types}
