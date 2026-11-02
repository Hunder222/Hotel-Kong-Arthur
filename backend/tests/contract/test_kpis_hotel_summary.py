"""Contract tests for `GET /api/v1/kpis/hotel/summary` under `Hotel Analytics` (T037)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from hotel_api.config import Settings
from hotel_api.main import create_app
from hotel_api.presentation.cli.seed import main as seed_main

pytestmark = pytest.mark.contract

SUMMARY_PATH = "/api/v1/kpis/hotel/summary"
VALID_FILTERS = [
    "",
    "?year=2026",
    "?year=all",
    "?season=low",
    "?season=mid",
    "?season=high",
    "?room_type=Suite",
    "?country=Germany",
    "?year=2026&season=high&room_type=Suite&country=Germany",
]
INVALID_FILTERS = [
    "?year=abc",
    "?year=1999",
    "?year=2101",
    "?season=autumn",
    "?room_type=Invalid",
    "?country=",
    "?country=%20%20",
]


@pytest.fixture()
def seeded(client, test_settings, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()


@pytest.mark.parametrize("query", VALID_FILTERS)
def test_summary_with_valid_filters_gives_200_matching_contract(client, check_contract, seeded, query):
    response = client.get(SUMMARY_PATH + query)
    assert response.status_code == 200
    check_contract(response)
    body = response.json()
    assert "occupancy_rate_pct" in body
    assert "available_room_nights" in body
    assert "review_count" in body
    assert "average_satisfaction" in body
    assert "satisfied_share_pct" in body


@pytest.mark.parametrize("query", INVALID_FILTERS)
def test_summary_with_invalid_filters_gives_400_problem_details(client, check_contract, query):
    response = client.get(SUMMARY_PATH + query)
    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    check_contract(response)
    assert response.json()["status"] == 400


def test_summary_on_empty_database_returns_zeros_and_matches_contract(client, check_contract):
    all_time = client.get(SUMMARY_PATH)
    assert all_time.status_code == 200
    check_contract(all_time)
    body_all = all_time.json()
    assert body_all["year"] == "all"
    assert body_all["booking_count"] == 0
    assert body_all["total_revenue_dkk"] == 0
    assert body_all["available_room_nights"] == 0
    assert body_all["occupancy_rate_pct"] == 0
    assert body_all["review_count"] == 0
    assert body_all["average_satisfaction"] == 0
    assert body_all["satisfied_share_pct"] == 0

    year_2026 = client.get(f"{SUMMARY_PATH}?year=2026")
    assert year_2026.status_code == 200
    check_contract(year_2026)
    body_2026 = year_2026.json()
    assert body_2026["year"] == 2026
    assert body_2026["available_room_nights"] == 78110
    assert body_2026["occupancy_rate_pct"] == 0


def test_summary_gives_503_when_database_is_down(check_contract):
    down = TestClient(
        create_app(Settings(db_host="127.0.0.1", db_port=1, db_name="hotel_test")),
        raise_server_exceptions=False,
    )
    response = down.get(SUMMARY_PATH)
    assert response.status_code == 503
    check_contract(response)

