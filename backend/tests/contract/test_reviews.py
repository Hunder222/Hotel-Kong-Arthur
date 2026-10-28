"""Contract tests for the review operations (T065), every response validated with openapi-core.

Skipped until the reviews router is registered (T072); remove the skip then and mark T065 done.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from hotel_api.config import Settings
from hotel_api.main import create_app
from tests.contract.test_contract_validity import app_operations

pytestmark = [
    pytest.mark.contract,
    pytest.mark.skipif(("POST", "/api/v1/reviews") not in app_operations(), reason="reviews router not registered yet (T072)"),
]

BOOKING = {"first_name": "Elena", "family_name": "Müller", "country": "Germany", "room_type": "Superior Double",
           "check_in_date": "2026-07-14", "days_rented": 3}


@pytest.fixture()
def booking_id(client):
    return client.post("/api/v1/bookings", json=BOOKING).json()["id"]


@pytest.fixture()
def created(client, check_contract, booking_id):
    response = client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 5})
    assert response.status_code == 201
    return response


def test_create_for_a_booking_returns_201_with_location_and_derived_season(created, check_contract, booking_id):
    check_contract(created)
    body = created.json()
    assert created.headers["location"] == f"/api/v1/reviews/{body['id']}"
    assert (body["booking_id"], body["room_type"], body["stay_date"], body["season"], body["year"], body["rating"]) == (
        booking_id, "Superior Double", "2026-07-14", "high", 2026, 5)


def test_create_without_a_booking(client, check_contract):
    response = client.post("/api/v1/reviews", json={"room_type": "Suite", "stay_date": "2026-01-10", "rating": 3})
    assert response.status_code == 201
    check_contract(response)
    assert response.json()["booking_id"] is None and response.json()["season"] == "low"


def test_malformed_json_is_400(client, check_contract):
    response = client.post("/api/v1/reviews", content='{"rating": ', headers={"content-type": "application/json"})
    assert response.status_code == 400
    check_contract(response)


@pytest.mark.parametrize("body,fields", [
    ({"booking_id": 999, "rating": 4}, {"booking_id"}),
    ({"rating": 6, "room_type": "Suite", "stay_date": "2026-01-10"}, {"rating"}),
    ({"rating": 3}, {"room_type", "stay_date"}),
    ({"booking_id": 1, "room_type": "Suite", "rating": 3}, {"room_type"}),
])
def test_rule_violations_are_422_naming_the_fields(client, check_contract, body, fields):
    response = client.post("/api/v1/reviews", json=body)
    assert response.status_code == 422
    check_contract(response)
    assert {e["field"] for e in response.json()["errors"]} == fields


def test_list_and_filters(client, check_contract, created):
    response = client.get("/api/v1/reviews")
    assert response.status_code == 200
    check_contract(response)
    assert len(response.json()["items"]) == 1
    for query, count in (("?year=2026&season=high&room_type=Superior Double", 1), ("?year=2025", 0), ("?season=low", 0)):
        filtered = client.get("/api/v1/reviews" + query)
        check_contract(filtered)
        assert len(filtered.json()["items"]) == count


@pytest.mark.parametrize("query", ["?year=abc", "?year=1999", "?season=winter", "?room_type=Penthouse"])
def test_list_with_a_bad_filter_is_400(client, check_contract, query):
    response = client.get("/api/v1/reviews" + query)
    assert response.status_code == 400
    check_contract(response)


def test_get_one(client, check_contract, created):
    response = client.get(f"/api/v1/reviews/{created.json()['id']}")
    assert response.status_code == 200
    check_contract(response)
    assert response.json() == created.json()


def test_get_with_id_0_is_400_and_unknown_id_is_404(client, check_contract):
    for path, status in (("/api/v1/reviews/0", 400), ("/api/v1/reviews/abc", 400), ("/api/v1/reviews/4242", 404)):
        response = client.get(path)
        assert response.status_code == status
        check_contract(response)


def test_reviews_give_503_when_the_database_is_down(check_contract):
    down = TestClient(create_app(Settings(db_host="127.0.0.1", db_port=1, db_name="hotel_test")),
                      raise_server_exceptions=False)
    for response in (down.get("/api/v1/reviews"), down.post("/api/v1/reviews", json={"booking_id": 1, "rating": 4})):
        assert response.status_code == 503
        check_contract(response)
