"""Golden A7 figures from the seeded PostgreSQL sample data (T056, quickstart §7, SC-003), within 0.01 tolerance."""

from __future__ import annotations

import pytest

from hotel_api.presentation.cli.seed import main as seed_main

pytestmark = pytest.mark.integration

TOLERANCE = 0.01


@pytest.fixture()
def seeded(client, test_settings, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()


def test_hotel_summary_a7_stay_metrics_match_golden_values(client, seeded):
    response = client.get("/api/v1/kpis/hotel/summary?year=2026")
    assert response.status_code == 200
    summary = response.json()
    assert summary["average_length_of_stay_nights"] == pytest.approx(5.38, abs=TOLERANCE)
    assert summary["average_daily_rate_dkk"] == pytest.approx(2088.50, abs=TOLERANCE)
    assert summary["average_revenue_per_booking_dkk"] == pytest.approx(11234.03, abs=TOLERANCE)


def test_seasonal_and_room_type_a7_stay_metrics_match_golden_values(client, seeded):
    seasons = {
        r["season"]: r
        for r in client.get("/api/v1/kpis/hotel/by-season?year=2026").json()["items"]
    }
    assert seasons["low"]["average_length_of_stay_nights"] == pytest.approx(5.36, abs=TOLERANCE)
    assert seasons["low"]["average_daily_rate_dkk"] == pytest.approx(1885.37, abs=TOLERANCE)
    assert seasons["low"]["average_revenue_per_booking_dkk"] == pytest.approx(10102.64, abs=TOLERANCE)

    assert seasons["mid"]["average_length_of_stay_nights"] == pytest.approx(5.48, abs=TOLERANCE)
    assert seasons["mid"]["average_daily_rate_dkk"] == pytest.approx(2073.70, abs=TOLERANCE)
    assert seasons["mid"]["average_revenue_per_booking_dkk"] == pytest.approx(11371.30, abs=TOLERANCE)

    assert seasons["high"]["average_length_of_stay_nights"] == pytest.approx(5.29, abs=TOLERANCE)
    assert seasons["high"]["average_daily_rate_dkk"] == pytest.approx(2308.89, abs=TOLERANCE)
    assert seasons["high"]["average_revenue_per_booking_dkk"] == pytest.approx(12223.93, abs=TOLERANCE)

    room_types = {
        r["room_type"]: r
        for r in client.get("/api/v1/kpis/hotel/by-room-type?year=2026").json()["items"]
    }
    suite = room_types["Suite"]
    assert suite["average_length_of_stay_nights"] == pytest.approx(706 / 137, abs=TOLERANCE)
    assert suite["average_daily_rate_dkk"] == pytest.approx(2119671 / 706, abs=TOLERANCE)
    assert suite["average_revenue_per_booking_dkk"] == pytest.approx(2119671 / 137, abs=TOLERANCE)


def test_bar_price_tier_a7_matches_golden_values(client, seeded):
    response = client.get("/api/v1/kpis/bar/by-price-tier?year=2026")
    assert response.status_code == 200
    rows = response.json()["items"]
    assert len(rows) == 3
    budget, standard, premium = rows

    assert budget["price_tier"] == "budget"
    assert (budget["price_from_dkk"], budget["price_to_dkk"]) == (0.0, 70.0)
    assert budget["drink_count"] == 10
    assert budget["units_sold"] == 117881
    assert budget["unit_share_pct"] == pytest.approx(65.50, abs=TOLERANCE)
    assert budget["revenue_dkk"] == pytest.approx(6343884.91, abs=TOLERANCE)
    assert budget["revenue_share_pct"] == pytest.approx(47.17, abs=TOLERANCE)

    assert standard["price_tier"] == "standard"
    assert (standard["price_from_dkk"], standard["price_to_dkk"]) == (70.0, 110.0)
    assert standard["drink_count"] == 10
    assert standard["units_sold"] == 29306
    assert standard["unit_share_pct"] == pytest.approx(16.29, abs=TOLERANCE)
    assert standard["revenue_dkk"] == pytest.approx(2739242.59, abs=TOLERANCE)
    assert standard["revenue_share_pct"] == pytest.approx(20.37, abs=TOLERANCE)

    assert premium["price_tier"] == "premium"
    assert (premium["price_from_dkk"], premium["price_to_dkk"]) == (110.0, None)
    assert premium["drink_count"] == 10
    assert premium["units_sold"] == 32771
    assert premium["unit_share_pct"] == pytest.approx(18.21, abs=TOLERANCE)
    assert premium["revenue_dkk"] == pytest.approx(4365512.84, abs=TOLERANCE)
    assert premium["revenue_share_pct"] == pytest.approx(32.46, abs=TOLERANCE)

    assert sum(r["unit_share_pct"] for r in rows) == pytest.approx(100.00, abs=TOLERANCE)
    assert sum(r["revenue_share_pct"] for r in rows) == pytest.approx(100.00, abs=TOLERANCE)
    assert sum(r["revenue_dkk"] for r in rows) == pytest.approx(13448640.34, abs=TOLERANCE)

