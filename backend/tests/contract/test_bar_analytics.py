"""Contract tests for the bar `Hotel Analytics` endpoints (`T045`), validated with openapi-core."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from hotel_api.config import Settings
from hotel_api.main import create_app
from hotel_api.presentation.cli.seed import main as seed_main

pytestmark = pytest.mark.contract

ENDPOINTS = [
    "/api/v1/kpis/bar/summary",
    "/api/v1/kpis/bar/by-drink",
    "/api/v1/kpis/bar/by-category",
]
VALID_FILTERS = [
    "",
    "?year=2026",
    "?year=all",
    "?category=Cocktail",
    "?category=Coffee",
    "?price_tier=budget",
    "?price_tier=standard",
    "?price_tier=premium",
    "?year=2026&category=Cocktail&price_tier=premium",
]
INVALID_FILTERS = [
    "?year=abc",
    "?year=1999",
    "?year=2101",
    "?year=ALL",
    "?category=Tea",
    "?category=cocktail",
    "?price_tier=luxury",
    "?price_tier=BUDGET",
]


@pytest.fixture()
def seeded(client, test_settings, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()


@pytest.mark.parametrize("query", VALID_FILTERS)
@pytest.mark.parametrize("path", ENDPOINTS)
def test_bar_analytics_with_valid_filters_gives_200_matching_contract(
    client, check_contract, seeded, path, query
):
    response = client.get(path + query)
    assert response.status_code == 200
    check_contract(response)


@pytest.mark.parametrize("query", INVALID_FILTERS)
@pytest.mark.parametrize("path", ENDPOINTS)
def test_bar_analytics_with_invalid_filters_gives_400_problem_details(
    client, check_contract, path, query
):
    response = client.get(path + query)
    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    check_contract(response)
    assert response.json()["status"] == 400


def test_bar_filters_narrow_drink_and_category_rows(client, check_contract, seeded):
    all_drinks = client.get("/api/v1/kpis/bar/by-drink?year=2026")
    check_contract(all_drinks)
    assert len(all_drinks.json()["items"]) == 30

    cocktails = client.get("/api/v1/kpis/bar/by-drink?year=2026&category=Cocktail")
    check_contract(cocktails)
    items = cocktails.json()["items"]
    assert len(items) == 20
    assert {i["category"] for i in items} == {"Cocktail"}
    assert items[0]["drink_name"] == "Mint Julep"

    premium = client.get("/api/v1/kpis/bar/by-drink?year=2026&price_tier=premium")
    check_contract(premium)
    premium_items = premium.json()["items"]
    assert len(premium_items) == 10
    assert {i["price_tier"] for i in premium_items} == {"premium"}

    categories = client.get("/api/v1/kpis/bar/by-category?year=2026")
    check_contract(categories)
    assert [i["category"] for i in categories.json()["items"]] == ["Cocktail", "Coffee"]

    only_coffee = client.get("/api/v1/kpis/bar/by-category?year=2026&category=Coffee")
    check_contract(only_coffee)
    assert [i["category"] for i in only_coffee.json()["items"]] == ["Coffee"]


def test_bar_analytics_on_empty_database_returns_zeros_and_matches_contract(client, check_contract):
    summary = client.get("/api/v1/kpis/bar/summary")
    assert summary.status_code == 200
    check_contract(summary)
    assert summary.json() == {"year": "all", "drink_count": 0, "units_sold": 0, "total_revenue_dkk": 0.0}

    drinks = client.get("/api/v1/kpis/bar/by-drink")
    assert drinks.status_code == 200
    check_contract(drinks)
    assert drinks.json() == {"items": []}

    categories = client.get("/api/v1/kpis/bar/by-category")
    assert categories.status_code == 200
    check_contract(categories)
    cat_items = categories.json()["items"]
    assert [i["category"] for i in cat_items] == ["Cocktail", "Coffee"]
    assert all(i["drink_count"] == 0 and i["revenue_dkk"] == 0 and i["revenue_share_pct"] == 0 for i in cat_items)


@pytest.mark.parametrize("path", ENDPOINTS)
def test_bar_analytics_endpoints_give_503_when_database_is_down(check_contract, path):
    down = TestClient(
        create_app(Settings(db_host="127.0.0.1", db_port=1, db_name="hotel_test")),
        raise_server_exceptions=False,
    )
    response = down.get(path)
    assert response.status_code == 503
    check_contract(response)

