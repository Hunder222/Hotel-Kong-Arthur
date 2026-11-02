"""Contract tests for `GET /api/v1/kpis/bar/by-price-tier` (T055), validated with openapi-core."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from hotel_api.config import Settings
from hotel_api.main import create_app
from hotel_api.presentation.cli.seed import main as seed_main

pytestmark = pytest.mark.contract

PATH = "/api/v1/kpis/bar/by-price-tier"
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
def test_by_price_tier_with_valid_filters_gives_200_matching_contract(
    client, check_contract, seeded, query
):
    response = client.get(PATH + query)
    assert response.status_code == 200
    check_contract(response)


@pytest.mark.parametrize("query", INVALID_FILTERS)
def test_by_price_tier_with_invalid_filters_gives_400_problem_details(
    client, check_contract, query
):
    response = client.get(PATH + query)
    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    check_contract(response)
    assert response.json()["status"] == 400


def test_by_price_tier_filters_and_bounds(client, check_contract, seeded):
    all_tiers = client.get(f"{PATH}?year=2026")
    assert all_tiers.status_code == 200
    check_contract(all_tiers)
    items = all_tiers.json()["items"]
    assert [i["price_tier"] for i in items] == ["budget", "standard", "premium"]
    assert [(i["price_from_dkk"], i["price_to_dkk"]) for i in items] == [
        (0.0, 70.0),
        (70.0, 110.0),
        (110.0, None),
    ]

    only_premium = client.get(f"{PATH}?year=2026&price_tier=premium")
    assert only_premium.status_code == 200
    check_contract(only_premium)
    assert [i["price_tier"] for i in only_premium.json()["items"]] == ["premium"]


def test_by_price_tier_on_empty_database_returns_three_zero_rows(client, check_contract):
    response = client.get(PATH)
    assert response.status_code == 200
    check_contract(response)
    items = response.json()["items"]
    assert [i["price_tier"] for i in items] == ["budget", "standard", "premium"]
    assert all(
        i["drink_count"] == 0
        and i["units_sold"] == 0
        and i["unit_share_pct"] == 0
        and i["revenue_dkk"] == 0
        and i["revenue_share_pct"] == 0
        for i in items
    )


def test_by_price_tier_gives_503_when_database_is_down(check_contract):
    down = TestClient(
        create_app(Settings(db_host="127.0.0.1", db_port=1, db_name="hotel_test")),
        raise_server_exceptions=False,
    )
    response = down.get(PATH)
    assert response.status_code == 503
    check_contract(response)

