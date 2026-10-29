"""Contract tests for the two complete US2 endpoints (T056), validated with openapi-core."""

from __future__ import annotations

import pytest

from hotel_api.presentation.cli.seed import main as seed_main

pytestmark = pytest.mark.contract

ROOM_TYPES = ["Standard Single", "Grand Lit", "Standard Double", "Superior Double",
              "Junior Suite", "Spa Executive", "Suite", "LOFT Suite"]
SEASONS = ["low", "mid", "high"]


@pytest.fixture()
def seeded(client, test_settings, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()


def test_by_room_type_and_season_has_24_rows_in_order(client, check_contract, seeded):
    response = client.get("/api/v1/kpis/hotel/by-room-type-and-season?year=2026")
    assert response.status_code == 200
    check_contract(response)
    items = response.json()["items"]
    assert [(i["room_type"], i["season"]) for i in items] == [(r, s) for r in ROOM_TYPES for s in SEASONS]
    assert round(sum(i["revenue_dkk"] for i in items), 2) == 11234034.00


def test_by_room_type_and_season_for_an_empty_year_still_has_24_rows(client, check_contract):
    response = client.get("/api/v1/kpis/hotel/by-room-type-and-season?year=2030")
    check_contract(response)
    items = response.json()["items"]
    assert len(items) == 24 and all(i["revenue_dkk"] == 0 for i in items)


def test_by_country_is_ordered_by_revenue_rank(client, check_contract, seeded):
    response = client.get("/api/v1/kpis/hotel/by-country?year=2026")
    assert response.status_code == 200
    check_contract(response)
    items = response.json()["items"]
    assert len(items) == 20
    assert [i["revenue_rank"] for i in items] == sorted(i["revenue_rank"] for i in items)
    assert items[0]["country"] == "South Korea" and items[0]["revenue_dkk"] == 767699.0


def test_by_country_for_an_empty_year_is_an_empty_list(client, check_contract):
    response = client.get("/api/v1/kpis/hotel/by-country?year=2030")
    assert response.status_code == 200
    check_contract(response)
    assert response.json() == {"items": []}


@pytest.mark.parametrize("path", ["by-country", "by-room-type-and-season"])
@pytest.mark.parametrize("query", ["?year=abc", "?year=1999", "?year=2101", "?year=ALL", "?year=All"])
def test_a_bad_year_is_400(client, check_contract, path, query):
    response = client.get(f"/api/v1/kpis/hotel/{path}{query}")
    assert response.status_code == 400
    check_contract(response)


# ---- FR-021: `year=all`, or no year at all, means all-time ----


def test_by_country_for_year_all_covers_every_year(client, check_contract, seeded):
    response = client.get("/api/v1/kpis/hotel/by-country?year=all")
    assert response.status_code == 200
    check_contract(response)
    items = response.json()["items"]
    assert len(items) == 20 and {i["year"] for i in items} == {"all"}
    # the sample data is all in 2026, so the all-time ranking equals that year's
    assert items[0]["country"] == "South Korea" and items[0]["revenue_dkk"] == 767699.0


def test_by_room_type_and_season_for_year_all_has_24_rows(client, check_contract, seeded):
    response = client.get("/api/v1/kpis/hotel/by-room-type-and-season?year=all")
    assert response.status_code == 200
    check_contract(response)
    items = response.json()["items"]
    assert [(i["room_type"], i["season"]) for i in items] == [(r, s) for r in ROOM_TYPES for s in SEASONS]
    assert {i["year"] for i in items} == {"all"}
    assert round(sum(i["revenue_dkk"] for i in items), 2) == 11234034.00


@pytest.mark.parametrize("path", ["by-country", "by-room-type-and-season"])
def test_omitting_the_year_means_all_time(client, check_contract, seeded, path):
    omitted = client.get(f"/api/v1/kpis/hotel/{path}")
    assert omitted.status_code == 200
    check_contract(omitted)
    assert omitted.json() == client.get(f"/api/v1/kpis/hotel/{path}?year=all").json()


def test_year_all_with_no_data_is_an_empty_country_list_and_24_zero_rows(client, check_contract):
    countries = client.get("/api/v1/kpis/hotel/by-country?year=all")
    check_contract(countries)
    assert countries.json() == {"items": []}
    grid = client.get("/api/v1/kpis/hotel/by-room-type-and-season?year=all")
    check_contract(grid)
    assert len(grid.json()["items"]) == 24 and all(i["revenue_dkk"] == 0 for i in grid.json()["items"])
