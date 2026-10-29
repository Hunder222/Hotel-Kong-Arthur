"""Contract tests for `GET /api/v1/bar/drink-sales`, every response validated with openapi-core."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from hotel_api.config import Settings
from hotel_api.main import create_app
from hotel_api.presentation.cli.seed import main as seed_main

pytestmark = pytest.mark.contract


@pytest.fixture()
def seeded(client, test_settings, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()


def test_drink_sales_lists_all_30_drinks_in_canonical_order(client, check_contract, seeded):
    response = client.get("/api/v1/bar/drink-sales")
    assert response.status_code == 200
    check_contract(response)
    items = response.json()["items"]
    assert len(items) == 30
    assert [i["id"] for i in items] == list(range(1, 31))
    assert items[0] == {
        "id": 1,
        "year": 2026,
        "drink_name": "Margarita",
        "category": "Cocktail",
        "unit_price_dkk": 72.47,
        "units_sold": 2361,
    }
    assert {i["category"] for i in items} == {"Cocktail", "Coffee"}


def test_drink_sales_when_empty_is_an_empty_list(client, check_contract):
    response = client.get("/api/v1/bar/drink-sales")
    assert response.status_code == 200
    check_contract(response)
    assert response.json() == {"items": []}


def test_bar_endpoint_gives_503_when_the_database_is_down(check_contract):
    down = TestClient(
        create_app(Settings(db_host="127.0.0.1", db_port=1, db_name="hotel_test")),
        raise_server_exceptions=False,
    )
    response = down.get("/api/v1/bar/drink-sales")
    assert response.status_code == 503
    check_contract(response)

