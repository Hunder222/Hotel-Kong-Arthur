"""Multi-year and all-time integration tests (T063, FR-021).

Verifies hotel and bar KPI endpoints with `year=all` and omitted `year`,
ensuring available room-nights span all booking years and bar totals aggregate
across sales years.
"""

from __future__ import annotations

import pytest

from hotel_api.presentation.cli.seed import main as seed_main

pytestmark = pytest.mark.integration

TOLERANCE = 0.01


@pytest.fixture()
def seeded(client, test_settings, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()


def test_hotel_summary_omitted_year_defaults_to_all_time(client, seeded):
    # FR-021: Omitting year or specifying year=all aggregates across all booking years
    res_default = client.get("/api/v1/kpis/hotel/summary")
    assert res_default.status_code == 200
    data_default = res_default.json()

    res_all = client.get("/api/v1/kpis/hotel/summary?year=all")
    assert res_all.status_code == 200
    data_all = res_all.json()

    assert data_default["year"] == "all"
    assert data_all["year"] == "all"
    assert data_default == data_all

    # In seeded data, all bookings are in 2026 (365 calendar days * 214 rooms = 78110 available room nights)
    assert data_default["booking_count"] == 1000
    assert data_default["total_revenue_dkk"] == pytest.approx(11234034.00, abs=TOLERANCE)
    assert data_default["available_room_nights"] == 78110
    assert data_default["occupancy_rate_pct"] == pytest.approx(6.89, abs=TOLERANCE)


def test_hotel_breakdowns_all_time_totals(client, seeded):
    for path in ("by-room-type", "by-season", "by-room-type-and-season", "by-country"):
        res_default = client.get(f"/api/v1/kpis/hotel/{path}")
        assert res_default.status_code == 200
        items_default = res_default.json()["items"]

        res_all = client.get(f"/api/v1/kpis/hotel/{path}?year=all")
        assert res_all.status_code == 200
        items_all = res_all.json()["items"]

        assert items_default == items_all
        total_rev = sum(item["revenue_dkk"] for item in items_default)
        assert total_rev == pytest.approx(11234034.00, abs=TOLERANCE), path


def test_bar_summary_omitted_year_defaults_to_all_time(client, seeded):
    res_default = client.get("/api/v1/kpis/bar/summary")
    assert res_default.status_code == 200
    data_default = res_default.json()

    res_all = client.get("/api/v1/kpis/bar/summary?year=all")
    assert res_all.status_code == 200
    data_all = res_all.json()

    assert data_default["year"] == "all"
    assert data_all["year"] == "all"
    assert data_default == data_all

    # Seeded bar data contains 30 distinct drinks, 179,958 units, 13,448,640.34 DKK
    assert data_default["drink_count"] == 30
    assert data_default["units_sold"] == 179958
    assert data_default["total_revenue_dkk"] == pytest.approx(13448640.34, abs=TOLERANCE)


def test_bar_breakdowns_all_time_totals(client, seeded):
    # by-drink
    res_drink_default = client.get("/api/v1/kpis/bar/by-drink")
    assert res_drink_default.status_code == 200
    items_drink = res_drink_default.json()["items"]
    res_drink_all = client.get("/api/v1/kpis/bar/by-drink?year=all")
    assert res_drink_all.status_code == 200
    assert items_drink == res_drink_all.json()["items"]
    assert len(items_drink) == 30
    assert sum(d["revenue_dkk"] for d in items_drink) == pytest.approx(13448640.34, abs=TOLERANCE)

    # by-category
    res_cat = client.get("/api/v1/kpis/bar/by-category")
    assert res_cat.status_code == 200
    items_cat = res_cat.json()["items"]
    assert len(items_cat) == 2
    assert sum(c["revenue_dkk"] for c in items_cat) == pytest.approx(13448640.34, abs=TOLERANCE)
    assert sum(c["units_sold"] for c in items_cat) == 179958

    # by-price-tier
    res_tier = client.get("/api/v1/kpis/bar/by-price-tier")
    assert res_tier.status_code == 200
    items_tier = res_tier.json()["items"]
    assert len(items_tier) == 3
    assert sum(t["revenue_dkk"] for t in items_tier) == pytest.approx(13448640.34, abs=TOLERANCE)
    assert sum(t["units_sold"] for t in items_tier) == 179958

