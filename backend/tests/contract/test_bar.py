"""Contract tests for the bar endpoints (T076), every response validated with openapi-core.

Rank semantics assumed by these tests: `revenue_rank` and `units_rank` are always ranks among ALL drinks of
the year; the `category` filter only selects which rows are returned.
"""

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


def test_drink_sales_lists_30_drinks_ordered_by_revenue_rank(client, check_contract, seeded):
    response = client.get("/api/v1/bar/drink-sales?year=2026")
    assert response.status_code == 200
    check_contract(response)
    items = response.json()["items"]
    assert len(items) == 30
    assert [i["revenue_rank"] for i in items] == sorted(i["revenue_rank"] for i in items)
    assert items[0]["drink_name"] == "Espresso" and items[0]["revenue_dkk"] == 1012729.6
    assert {i["price_tier"] for i in items} == {"budget", "standard", "premium"}


def test_category_filter_returns_only_that_category(client, check_contract, seeded):
    response = client.get("/api/v1/bar/drink-sales?year=2026&category=Cocktail")
    assert response.status_code == 200
    check_contract(response)
    items = response.json()["items"]
    assert len(items) == 20 and {i["category"] for i in items} == {"Cocktail"}
    assert items[0]["drink_name"] == "Mint Julep"
    assert [i["revenue_rank"] for i in items] == sorted(i["revenue_rank"] for i in items)


def test_drink_sales_of_an_empty_year_is_an_empty_list(client, check_contract):
    response = client.get("/api/v1/bar/drink-sales?year=2030")
    assert response.status_code == 200
    check_contract(response)
    assert response.json() == {"items": []}


@pytest.mark.parametrize("query", ["?year=abc", "?year=1999", "?year=2101", "?category=Tea", "?category=cocktail"])
def test_drink_sales_with_a_bad_parameter_is_400(client, check_contract, query):
    response = client.get("/api/v1/bar/drink-sales" + query)
    assert response.status_code == 400
    check_contract(response)


def test_summary_b1(client, check_contract, seeded):
    response = client.get("/api/v1/kpis/bar/summary?year=2026")
    assert response.status_code == 200
    check_contract(response)
    assert response.json() == {"year": 2026, "drink_count": 30, "units_sold": 179958, "total_revenue_dkk": 13448640.34}


def test_summary_of_an_empty_year_is_zeros(client, check_contract):
    response = client.get("/api/v1/kpis/bar/summary?year=2030")
    assert response.status_code == 200
    check_contract(response)
    assert response.json() == {"year": 2030, "drink_count": 0, "units_sold": 0, "total_revenue_dkk": 0.0}


def test_by_category_has_two_rows_cocktail_then_coffee(client, check_contract, seeded):
    response = client.get("/api/v1/kpis/bar/by-category?year=2026")
    assert response.status_code == 200
    check_contract(response)
    items = response.json()["items"]
    assert [i["category"] for i in items] == ["Cocktail", "Coffee"]
    assert round(sum(i["revenue_share_pct"] for i in items), 2) == 100.0
    assert round(sum(i["unit_share_pct"] for i in items), 2) == 100.0


def test_by_category_of_an_empty_year_still_has_both_rows(client, check_contract):
    response = client.get("/api/v1/kpis/bar/by-category?year=2030")
    check_contract(response)
    items = response.json()["items"]
    assert [i["category"] for i in items] == ["Cocktail", "Coffee"]
    assert all(i["revenue_dkk"] == 0 and i["revenue_share_pct"] == 0 and i["drink_count"] == 0 for i in items)


def test_the_year_defaults_to_the_current_year(client, check_contract):
    for path in ("/api/v1/kpis/bar/summary", "/api/v1/kpis/bar/by-category", "/api/v1/bar/drink-sales"):
        response = client.get(path)
        assert response.status_code == 200
        check_contract(response)


@pytest.mark.parametrize("path", ["/api/v1/kpis/bar/summary", "/api/v1/kpis/bar/by-category"])
@pytest.mark.parametrize("query", ["?year=abc", "?year=1999"])
def test_kpi_endpoints_reject_a_bad_year_with_400(client, check_contract, path, query):
    response = client.get(path + query)
    assert response.status_code == 400
    check_contract(response)


def test_bar_endpoints_give_503_when_the_database_is_down(check_contract):
    down = TestClient(create_app(Settings(db_host="127.0.0.1", db_port=1, db_name="hotel_test")), raise_server_exceptions=False)
    for path in ("/api/v1/bar/drink-sales", "/api/v1/kpis/bar/summary", "/api/v1/kpis/bar/by-category"):
        response = down.get(path)
        assert response.status_code == 503
        check_contract(response)
