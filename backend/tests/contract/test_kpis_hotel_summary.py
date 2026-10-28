"""The partly-shared hotel KPI endpoints (T067): `summary`, `by-room-type` and `by-season`.

They are checked here for the shape produced so far (revenue, occupancy, satisfaction). They are
validated against the complete contract schemas, including ALOS / ADR, in T086; until then openapi-core
cannot be used on them because `required` lists fields that do not exist yet.
"""

from __future__ import annotations

import pytest

from hotel_api.presentation.cli.seed import main as seed_main

pytestmark = pytest.mark.contract

SHARED = {"year", "booking_count", "nights_sold", "available_room_nights", "occupancy_rate_pct", "review_count",
          "average_satisfaction", "satisfied_share_pct"}
SUMMARY_KEYS = SHARED | {"total_revenue_dkk"}
ROW_KEYS = SHARED | {"revenue_dkk", "revenue_share_pct"}


@pytest.fixture()
def seeded(client, test_settings, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()


def test_summary_shape_and_values(client, seeded):
    response = client.get("/api/v1/kpis/hotel/summary?year=2026")
    assert response.status_code == 200
    body = response.json()
    assert SUMMARY_KEYS <= set(body)
    assert (body["total_revenue_dkk"], body["available_room_nights"], body["occupancy_rate_pct"], body["review_count"]) == (
        11234034.0, 78110, 6.89, 500)
    assert 1 <= body["average_satisfaction"] <= 5


def test_by_room_type_has_8_rows(client, seeded):
    items = client.get("/api/v1/kpis/hotel/by-room-type?year=2026").json()["items"]
    assert len(items) == 8
    assert all(ROW_KEYS | {"revenue_rank", "room_type", "room_count"} <= set(i) for i in items)
    suite = next(i for i in items if i["room_type"] == "Suite")
    assert (suite["available_room_nights"], suite["occupancy_rate_pct"]) == (9490, 7.44)


def test_by_season_has_3_rows(client, seeded):
    items = client.get("/api/v1/kpis/hotel/by-season?year=2026").json()["items"]
    assert [i["season"] for i in items] == ["low", "mid", "high"]
    assert all(ROW_KEYS | {"season_days"} <= set(i) for i in items)
    assert [i["occupancy_rate_pct"] for i in items] == [9.34, 5.61, 6.70]


def test_an_empty_year_has_zero_rates_and_full_capacity(client):
    body = client.get("/api/v1/kpis/hotel/summary?year=2030").json()
    assert (body["occupancy_rate_pct"], body["review_count"], body["average_satisfaction"], body["available_room_nights"]) == (
        0.0, 0, 0.0, 78110)


def test_a_bad_year_is_400(client):
    assert client.get("/api/v1/kpis/hotel/summary?year=abc").status_code == 400
