"""GET /api/v1/health and GET /api/v1/room-types, validated against openapi.yaml (T037)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from hotel_api.config import Settings
from hotel_api.main import create_app

pytestmark = pytest.mark.contract


def test_health_ok(client, check_contract):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    assert response.headers["cache-control"] == "no-store"
    check_contract(response)


def test_room_types(client, check_contract):
    response = client.get("/api/v1/room-types")
    assert response.status_code == 200
    check_contract(response)
    items = response.json()["items"]
    assert len(items) == 8
    assert sum(item["room_count"] for item in items) == 214
    assert all(len(item["rates"]) == 3 for item in items)
    assert [r["season"] for r in items[0]["rates"]] == ["low", "mid", "high"]
    assert items[0]["name"] == "Standard Single"
    assert items[0]["name_da"] == "Standard enkeltværelse"


def test_amounts_are_json_numbers_not_strings(client):
    rate = client.get("/api/v1/room-types").json()["items"][0]["rates"][0]
    assert rate["min_nightly_dkk"] == 900 and rate["standard_nightly_dkk"] == 1050
    assert all(isinstance(v, (int, float)) for k, v in rate.items() if k != "season")


def test_unknown_route_is_a_not_found_problem(client):
    response = client.get("/api/v1/nothing-here")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["type"] == "urn:hotel-kong-arthur:problem:not-found"


def test_generated_documentation_is_off(client):
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404


def test_database_down_gives_503_problem(check_contract):
    unreachable = Settings(db_host="127.0.0.1", db_port=1, db_name="hotel_test")
    client = TestClient(create_app(unreachable), raise_server_exceptions=False)
    for path in ("/api/v1/health", "/api/v1/room-types"):
        response = client.get(path)
        assert response.status_code == 503
        assert response.headers["content-type"].startswith("application/problem+json")
        assert response.json()["type"] == "urn:hotel-kong-arthur:problem:service-unavailable"
        check_contract(response)
