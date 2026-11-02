"""Golden revenue figures from the seeded sample year (quickstart §4, SC-003), within 0.01 DKK."""

from __future__ import annotations

import pytest

from hotel_api.presentation.cli.seed import main as seed_main

pytestmark = pytest.mark.integration

TOLERANCE = 0.01


@pytest.fixture()
def seeded(client, test_settings, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()


def items(client, path: str) -> list[dict]:
    response = client.get(path)
    assert response.status_code == 200
    return response.json()["items"]


def test_total_revenue_is_the_same_in_every_breakdown(client, seeded):
    for path in ("by-room-type", "by-season", "by-room-type-and-season", "by-country"):
        total = sum(row["revenue_dkk"] for row in items(client, f"/api/v1/kpis/hotel/{path}?year=2026"))
        assert total == pytest.approx(11234034.00, abs=TOLERANCE), path


def test_revenue_by_room_type_ranks_suite_first_and_standard_single_last(client, seeded):
    rows = items(client, "/api/v1/kpis/hotel/by-room-type?year=2026")
    assert len(rows) == 8
    assert [r["revenue_rank"] for r in rows] == list(range(1, 9))
    suite, spa, standard_single = rows[0], rows[1], rows[-1]
    assert suite["room_type"] == "Suite"
    assert suite["revenue_dkk"] == pytest.approx(2119671.00, abs=TOLERANCE)
    assert suite["revenue_share_pct"] == pytest.approx(18.87, abs=TOLERANCE)
    assert (spa["room_type"], spa["revenue_dkk"]) == ("Spa Executive", pytest.approx(1722396.00, abs=TOLERANCE))
    assert standard_single["room_type"] == "Standard Single"
    assert standard_single["revenue_dkk"] == pytest.approx(730444.00, abs=TOLERANCE)
    assert standard_single["revenue_share_pct"] == pytest.approx(6.50, abs=TOLERANCE)
    assert sum(r["revenue_share_pct"] for r in rows) == pytest.approx(100.00, abs=TOLERANCE)


def test_revenue_by_country_ranks_south_korea_first_and_egypt_last(client, seeded):
    rows = items(client, "/api/v1/kpis/hotel/by-country?year=2026")
    assert len(rows) == 20
    first, second, last = rows[0], rows[1], rows[-1]
    assert (first["revenue_rank"], first["country"], first["booking_count"]) == (1, "South Korea", 63)
    assert first["revenue_dkk"] == pytest.approx(767699.00, abs=TOLERANCE)
    assert first["booking_share_pct"] == pytest.approx(6.30, abs=TOLERANCE)
    assert (second["country"], second["revenue_dkk"]) == ("China", pytest.approx(722928.00, abs=TOLERANCE))
    assert (last["revenue_rank"], last["country"]) == (20, "Egypt")
    assert last["revenue_dkk"] == pytest.approx(335786.00, abs=TOLERANCE)
    assert sum(r["booking_count"] for r in rows) == 1000
    assert sum(r["booking_share_pct"] for r in rows) == pytest.approx(100.00, abs=TOLERANCE)


def test_revenue_by_room_type_and_season_has_24_cells(client, seeded):
    rows = items(client, "/api/v1/kpis/hotel/by-room-type-and-season?year=2026")
    assert len(rows) == 24
    cells = {(r["room_type"], r["season"]): r["revenue_dkk"] for r in rows}
    assert cells[("LOFT Suite", "high")] == pytest.approx(683198.00, abs=TOLERANCE)
    assert cells[("Standard Single", "low")] == pytest.approx(239940.00, abs=TOLERANCE)


def test_revenue_by_season_matches_the_quickstart(client, seeded):
    rows = {r["season"]: r for r in items(client, "/api/v1/kpis/hotel/by-season?year=2026")}
    assert list(rows) == ["low", "mid", "high"]
    assert rows["low"]["revenue_dkk"] == pytest.approx(3354077.00, abs=TOLERANCE)
    assert rows["mid"]["revenue_dkk"] == pytest.approx(3809387.00, abs=TOLERANCE)
    assert rows["high"]["revenue_dkk"] == pytest.approx(4070570.00, abs=TOLERANCE)
    assert rows["low"]["revenue_share_pct"] == pytest.approx(29.86, abs=TOLERANCE)
    assert rows["mid"]["revenue_share_pct"] == pytest.approx(33.91, abs=TOLERANCE)
    assert rows["high"]["revenue_share_pct"] == pytest.approx(36.23, abs=TOLERANCE)


def test_filters_slice_the_golden_data(client, seeded):
    high = items(client, "/api/v1/kpis/hotel/by-room-type?year=2026&season=high")
    assert sum(r["revenue_dkk"] for r in high) == pytest.approx(4070570.00, abs=TOLERANCE)
    korea = items(client, "/api/v1/kpis/hotel/by-country?year=2026&country=South%20Korea")
    assert [(r["country"], r["revenue_rank"]) for r in korea] == [("South Korea", 1)]
    assert korea[0]["revenue_share_pct"] == pytest.approx(100.00, abs=TOLERANCE)
    all_time = items(client, "/api/v1/kpis/hotel/by-room-type")
    assert sum(r["revenue_dkk"] for r in all_time) == pytest.approx(11234034.00, abs=TOLERANCE)
