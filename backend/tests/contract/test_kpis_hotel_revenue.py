"""Contract tests for the hotel revenue `Hotel Analytics` endpoints, every response validated with openapi-core."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from hotel_api.config import Settings
from hotel_api.main import create_app
from hotel_api.presentation.cli.seed import main as seed_main

pytestmark = pytest.mark.contract

ENDPOINTS = [
    "/api/v1/kpis/hotel/by-room-type",
    "/api/v1/kpis/hotel/by-season",
    "/api/v1/kpis/hotel/by-room-type-and-season",
    "/api/v1/kpis/hotel/by-country",
]
VALID_FILTERS = ["", "?year=2026", "?year=all", "?season=high", "?room_type=Suite", "?country=Germany"]
INVALID_FILTERS = ["?year=abc", "?year=1999", "?season=autumn", "?room_type=Invalid", "?country="]


@pytest.fixture()
def seeded(client, test_settings, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()


@pytest.mark.parametrize("query", VALID_FILTERS)
@pytest.mark.parametrize("path", ENDPOINTS)
def test_valid_filters_give_200_matching_the_contract(client, check_contract, seeded, path, query):
    response = client.get(path + query)
    assert response.status_code == 200
    check_contract(response)
    assert "items" in response.json()


@pytest.mark.parametrize("query", INVALID_FILTERS)
@pytest.mark.parametrize("path", ENDPOINTS)
def test_invalid_filters_give_400_problem_details(client, check_contract, path, query):
    response = client.get(path + query)
    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    check_contract(response)
    assert response.json()["status"] == 400


def test_filters_narrow_the_rows(client, seeded):
    assert len(client.get("/api/v1/kpis/hotel/by-room-type").json()["items"]) == 8
    assert len(client.get("/api/v1/kpis/hotel/by-room-type?room_type=Suite").json()["items"]) == 1
    assert len(client.get("/api/v1/kpis/hotel/by-season").json()["items"]) == 3
    assert len(client.get("/api/v1/kpis/hotel/by-season?season=high").json()["items"]) == 1
    assert len(client.get("/api/v1/kpis/hotel/by-room-type-and-season").json()["items"]) == 24
    countries = client.get("/api/v1/kpis/hotel/by-country?country=Germany").json()["items"]
    assert [c["country"] for c in countries] == ["Germany"]


def test_the_year_is_echoed_as_a_number_or_all(client, seeded):
    assert client.get("/api/v1/kpis/hotel/by-season?year=2026").json()["items"][0]["year"] == 2026
    assert client.get("/api/v1/kpis/hotel/by-season").json()["items"][0]["year"] == "all"


def test_empty_database_gives_zeroed_rows_not_an_error(client, check_contract):
    response = client.get("/api/v1/kpis/hotel/by-room-type")
    assert response.status_code == 200
    check_contract(response)
    assert all(row["revenue_dkk"] == 0 for row in response.json()["items"])
    assert client.get("/api/v1/kpis/hotel/by-country").json() == {"items": []}


@pytest.mark.parametrize("path", ENDPOINTS)
def test_endpoints_give_503_when_the_database_is_down(check_contract, path):
    down = TestClient(
        create_app(Settings(db_host="127.0.0.1", db_port=1, db_name="hotel_test")),
        raise_server_exceptions=False,
    )
    response = down.get(path)
    assert response.status_code == 503
    check_contract(response)
