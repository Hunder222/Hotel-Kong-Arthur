"""Golden bar figures from the seeded PostgreSQL sample data (T046, quickstart §6, SC-003), within 0.01 tolerance."""

from __future__ import annotations

import pytest

from hotel_api.presentation.cli.seed import main as seed_main

pytestmark = pytest.mark.integration

TOLERANCE = 0.01


@pytest.fixture()
def seeded(client, test_settings, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()


def test_total_bar_sales_b1_matches_golden_values(client, seeded):
    response = client.get("/api/v1/kpis/bar/summary?year=2026")
    assert response.status_code == 200
    summary = response.json()
    assert summary["year"] == 2026
    assert summary["drink_count"] == 30
    assert summary["units_sold"] == 179958
    assert summary["total_revenue_dkk"] == pytest.approx(13448640.34, abs=TOLERANCE)


def test_revenue_per_drink_and_ranks_b2_matches_golden_values(client, seeded):
    response = client.get("/api/v1/kpis/bar/by-drink?year=2026")
    assert response.status_code == 200
    rows = response.json()["items"]
    assert len(rows) == 30
    assert [r["revenue_rank"] for r in rows] == sorted(r["revenue_rank"] for r in rows)
    assert sum(r["revenue_dkk"] for r in rows) == pytest.approx(13448640.34, abs=TOLERANCE)

    by_name = {r["drink_name"]: r for r in rows}
    espresso = by_name["Espresso"]
    assert espresso["revenue_rank"] == 1
    assert espresso["units_rank"] == 1
    assert espresso["units_sold"] == 14656
    assert espresso["revenue_dkk"] == pytest.approx(1012729.60, abs=TOLERANCE)

    margarita = by_name["Margarita"]
    assert margarita["revenue_rank"] == 30
    assert margarita["revenue_dkk"] == pytest.approx(171101.67, abs=TOLERANCE)

    cocktails = client.get("/api/v1/kpis/bar/by-drink?year=2026&category=Cocktail").json()["items"]
    assert len(cocktails) == 20
    assert cocktails[0]["drink_name"] == "Mint Julep"
    assert cocktails[0]["revenue_dkk"] == pytest.approx(524351.62, abs=TOLERANCE)


def test_cocktail_vs_coffee_split_b3_matches_golden_values(client, seeded):
    response = client.get("/api/v1/kpis/bar/by-category?year=2026")
    assert response.status_code == 200
    rows = response.json()["items"]
    assert len(rows) == 2
    cocktail, coffee = rows

    assert cocktail["category"] == "Cocktail"
    assert cocktail["drink_count"] == 20
    assert cocktail["units_sold"] == 62077
    assert cocktail["unit_share_pct"] == pytest.approx(34.50, abs=TOLERANCE)
    assert cocktail["revenue_dkk"] == pytest.approx(7104755.43, abs=TOLERANCE)
    assert cocktail["revenue_share_pct"] == pytest.approx(52.83, abs=TOLERANCE)

    assert coffee["category"] == "Coffee"
    assert coffee["drink_count"] == 10
    assert coffee["units_sold"] == 117881
    assert coffee["unit_share_pct"] == pytest.approx(65.50, abs=TOLERANCE)
    assert coffee["revenue_dkk"] == pytest.approx(6343884.91, abs=TOLERANCE)
    assert coffee["revenue_share_pct"] == pytest.approx(47.17, abs=TOLERANCE)

    assert cocktail["revenue_share_pct"] + coffee["revenue_share_pct"] == pytest.approx(100.00, abs=TOLERANCE)
    assert cocktail["unit_share_pct"] + coffee["unit_share_pct"] == pytest.approx(100.00, abs=TOLERANCE)

