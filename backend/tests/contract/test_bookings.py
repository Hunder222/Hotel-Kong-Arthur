"""Contract tests for the 5 booking operations (T043), every response validated with openapi-core."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from hotel_api.config import Settings
from hotel_api.main import create_app

pytestmark = pytest.mark.contract

QUICKSTART = {
    "first_name": "Elena",
    "family_name": "Müller",
    "country": "Germany",
    "room_type": "Superior Double",
    "check_in_date": "2026-07-14",
    "days_rented": 3,
}


@pytest.fixture()
def created(client, check_contract):
    response = client.post("/api/v1/bookings", json=QUICKSTART)
    assert response.status_code == 201
    return response


def test_list_empty_and_filtered(client, check_contract, created):
    response = client.get("/api/v1/bookings")
    assert response.status_code == 200
    check_contract(response)
    assert len(response.json()["items"]) == 1
    for query, expected in (
        ("?year=2026&season=high&room_type=Superior Double&country=Germany", 1),
        ("?year=2025", 0),
        ("?season=low", 0),
    ):
        filtered = client.get("/api/v1/bookings" + query)
        check_contract(filtered)
        assert len(filtered.json()["items"]) == expected


@pytest.mark.parametrize("query", ["?year=abc", "?year=1999", "?season=winter", "?room_type=Penthouse"])
def test_list_with_a_bad_filter_is_400(client, check_contract, query):
    response = client.get("/api/v1/bookings" + query)
    assert response.status_code == 400
    check_contract(response)


def test_create_returns_201_with_location_and_derived_fields(created, check_contract):
    check_contract(created)
    body = created.json()
    assert created.headers["location"] == f"/api/v1/bookings/{body['id']}"
    assert (body["season"], body["year"], body["price_dkk"]) == ("high", 2026, 6000.0)


def test_create_with_malformed_json_is_400(client, check_contract):
    response = client.post("/api/v1/bookings", content='{"first_name": ', headers={"content-type": "application/json"})
    assert response.status_code == 400
    check_contract(response)


def test_create_with_invalid_fields_is_422_naming_each_field(client, check_contract):
    response = client.post("/api/v1/bookings", json={**QUICKSTART, "room_type": "Penthouse", "days_rented": 0})
    assert response.status_code == 422
    check_contract(response)
    assert {e["field"] for e in response.json()["errors"]} == {"room_type", "days_rented"}
    assert client.get("/api/v1/bookings").json() == {"items": []}


def test_create_with_a_price_outside_the_band_is_422(client, check_contract):
    response = client.post("/api/v1/bookings", json={**QUICKSTART, "price_dkk": 1000})
    assert response.status_code == 422
    check_contract(response)
    assert response.json()["errors"][0]["field"] == "price_dkk"


def test_get_one(client, check_contract, created):
    booking_id = created.json()["id"]
    response = client.get(f"/api/v1/bookings/{booking_id}")
    assert response.status_code == 200
    check_contract(response)
    assert response.json() == created.json()


def test_get_with_id_0_is_400_and_unknown_id_is_404(client, check_contract):
    for path, status in (("/api/v1/bookings/0", 400), ("/api/v1/bookings/abc", 400), ("/api/v1/bookings/4242", 404)):
        response = client.get(path)
        assert response.status_code == status
        check_contract(response)


def test_put_recalculates_the_price_when_omitted(client, check_contract, created):
    booking_id = created.json()["id"]
    response = client.put(f"/api/v1/bookings/{booking_id}", json={**QUICKSTART, "days_rented": 5})
    assert response.status_code == 200
    check_contract(response)
    assert response.json()["price_dkk"] == 10000.0
    assert client.get(f"/api/v1/bookings/{booking_id}").json()["days_rented"] == 5


def test_put_errors(client, check_contract, created):
    unknown = client.put("/api/v1/bookings/4242", json=QUICKSTART)
    assert unknown.status_code == 404
    check_contract(unknown)
    invalid = client.put(f"/api/v1/bookings/{created.json()['id']}", json={**QUICKSTART, "days_rented": 0})
    assert invalid.status_code == 422
    check_contract(invalid)
    bad_id = client.put("/api/v1/bookings/0", json=QUICKSTART)
    assert bad_id.status_code == 400
    check_contract(bad_id)


# ---- FR-019: a fixed price per night instead of a total price ----


def test_create_with_a_price_per_night_stores_the_total(client, check_contract):
    response = client.post("/api/v1/bookings", json={**QUICKSTART, "price_per_night_dkk": 2000})
    assert response.status_code == 201
    check_contract(response)
    body = response.json()
    assert body["price_dkk"] == 6000.0  # 3 nights x 2000.00
    assert "price_per_night_dkk" not in body  # a booking is read back with its total only


def test_a_null_price_field_is_accepted_next_to_the_other(client, check_contract):
    response = client.post("/api/v1/bookings", json={**QUICKSTART, "price_dkk": None, "price_per_night_dkk": 2000})
    assert response.status_code == 201
    check_contract(response)
    assert response.json()["price_dkk"] == 6000.0


def test_create_with_a_price_per_night_outside_the_band_is_422(client, check_contract):
    response = client.post("/api/v1/bookings", json={**QUICKSTART, "price_per_night_dkk": 1000})
    assert response.status_code == 422
    check_contract(response)
    assert [e["field"] for e in response.json()["errors"]] == ["price_per_night_dkk"]
    assert client.get("/api/v1/bookings").json() == {"items": []}


def test_create_with_both_prices_is_422_and_stores_nothing(client, check_contract):
    response = client.post("/api/v1/bookings", json={**QUICKSTART, "price_dkk": 6000, "price_per_night_dkk": 2000})
    assert response.status_code == 422
    check_contract(response)
    assert [e["field"] for e in response.json()["errors"]] == ["price_per_night_dkk"]
    assert client.get("/api/v1/bookings").json() == {"items": []}


def test_put_with_a_price_per_night_recalculates_the_total(client, check_contract, created):
    booking_id = created.json()["id"]
    response = client.put(
        f"/api/v1/bookings/{booking_id}", json={**QUICKSTART, "days_rented": 5, "price_per_night_dkk": 2100.5}
    )
    assert response.status_code == 200
    check_contract(response)
    assert response.json()["price_dkk"] == 10502.5  # 5 nights x 2100.50
    assert client.get(f"/api/v1/bookings/{booking_id}").json()["price_dkk"] == 10502.5


def test_put_with_both_prices_is_422_and_changes_nothing(client, check_contract, created):
    booking_id = created.json()["id"]
    response = client.put(
        f"/api/v1/bookings/{booking_id}", json={**QUICKSTART, "price_dkk": 6000, "price_per_night_dkk": 2000}
    )
    assert response.status_code == 422
    check_contract(response)
    assert client.get(f"/api/v1/bookings/{booking_id}").json() == created.json()


def test_delete_then_404(client, check_contract, created):
    booking_id = created.json()["id"]
    response = client.delete(f"/api/v1/bookings/{booking_id}")
    assert response.status_code == 204 and response.content == b""
    check_contract(response)
    again = client.delete(f"/api/v1/bookings/{booking_id}")
    assert again.status_code == 404
    check_contract(again)
    assert client.get(f"/api/v1/bookings/{booking_id}").status_code == 404


def test_bookings_give_503_when_the_database_is_down(check_contract):
    down = TestClient(create_app(Settings(db_host="127.0.0.1", db_port=1, db_name="hotel_test")),
                      raise_server_exceptions=False)
    for response in (down.get("/api/v1/bookings"), down.post("/api/v1/bookings", json=QUICKSTART)):
        assert response.status_code == 503
        check_contract(response)
