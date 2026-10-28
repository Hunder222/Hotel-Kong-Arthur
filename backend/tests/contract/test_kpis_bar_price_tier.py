"""Contract tests for `GET /kpis/bar/by-price-tier` (T086), validated with openapi-core.

Skipped until the route exists (T092); remove the guard then and mark T086 done (with the A7 part in
test_kpis_hotel_summary.py).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from hotel_api.config import Settings
from hotel_api.main import create_app
from hotel_api.presentation.cli.seed import main as seed_main
from tests.contract.test_contract_validity import app_operations

pytestmark = [
    pytest.mark.contract,
    pytest.mark.skipif(("GET", "/api/v1/kpis/bar/by-price-tier") not in app_operations(), reason="route not registered yet (T092)"),
]

URL = "/api/v1/kpis/bar/by-price-tier"


@pytest.fixture()
def seeded(client, test_settings, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()


def test_always_three_rows_with_the_price_bounds(client, check_contract, seeded):
    response = client.get(URL + "?year=2026")
    assert response.status_code == 200
    check_contract(response)
    budget, standard, premium = response.json()["items"]
    assert (budget["price_tier"], budget["price_from_dkk"], budget["price_to_dkk"]) == ("budget", 0, 70)
    assert (standard["price_tier"], standard["price_from_dkk"], standard["price_to_dkk"]) == ("standard", 70, 110)
    assert (premium["price_tier"], premium["price_from_dkk"], premium["price_to_dkk"]) == ("premium", 110, None)


def test_golden_values(client, check_contract, seeded):
    items = client.get(URL + "?year=2026").json()["items"]
    assert [(i["drink_count"], i["units_sold"], i["revenue_dkk"]) for i in items] == [
        (10, 117881, 6343884.91), (10, 29306, 2739242.59), (10, 32771, 4365512.84)]
    assert [i["unit_share_pct"] for i in items] == [65.5, 16.29, 18.21]
    assert [i["revenue_share_pct"] for i in items] == [47.17, 20.37, 32.46]


def test_an_empty_year_has_three_zero_rows(client, check_contract):
    response = client.get(URL + "?year=2030")
    assert response.status_code == 200
    check_contract(response)
    items = response.json()["items"]
    assert len(items) == 3 and all(i["units_sold"] == 0 and i["revenue_share_pct"] == 0 for i in items)
    assert items[2]["price_to_dkk"] is None


def test_the_year_defaults_to_the_current_year(client, check_contract):
    response = client.get(URL)
    assert response.status_code == 200
    check_contract(response)


@pytest.mark.parametrize("query", ["?year=abc", "?year=1999", "?year=2101"])
def test_a_bad_year_is_400(client, check_contract, query):
    response = client.get(URL + query)
    assert response.status_code == 400
    check_contract(response)


def test_503_when_the_database_is_down(check_contract):
    down = TestClient(create_app(Settings(db_host="127.0.0.1", db_port=1, db_name="hotel_test")), raise_server_exceptions=False)
    response = down.get(URL)
    assert response.status_code == 503
    check_contract(response)
