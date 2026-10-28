"""The partly-shared hotel KPI endpoints (T067): `summary`, `by-room-type` and `by-season`.

The first tests check the shape and values field by field (T067); the last ones validate the responses
against the complete contract schemas with openapi-core, including ALOS / ADR (T086).
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


# ---- T086: the same endpoints against the COMPLETE contract schemas (incl. ALOS / ADR / revenue per booking) ----

@pytest.mark.parametrize("path", ["summary", "by-room-type", "by-season"])
@pytest.mark.parametrize("year", ["2026", "2030"])
def test_complete_contract_schemas(client, check_contract, seeded, path, year):
    response = client.get(f"/api/v1/kpis/hotel/{path}?year={year}")
    assert response.status_code == 200
    check_contract(response)


def test_a7_values_in_the_responses(client, check_contract, seeded):
    body = client.get("/api/v1/kpis/hotel/summary?year=2026").json()
    assert (body["average_length_of_stay_nights"], body["average_daily_rate_dkk"],
            body["average_revenue_per_booking_dkk"]) == (5.38, 2088.5, 11234.03)
    seasons = client.get("/api/v1/kpis/hotel/by-season?year=2026").json()["items"]
    assert [(i["average_length_of_stay_nights"], i["average_daily_rate_dkk"], i["average_revenue_per_booking_dkk"])
            for i in seasons] == [(5.36, 1885.37, 10102.64), (5.48, 2073.7, 11371.3), (5.29, 2308.89, 12223.93)]


def test_bad_year_is_400_with_the_contract_error_shape(client, check_contract):
    response = client.get("/api/v1/kpis/hotel/summary?year=abc")
    assert response.status_code == 400
    check_contract(response)
