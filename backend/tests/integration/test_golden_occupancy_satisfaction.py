"""Golden occupancy (K1) and customer satisfaction (K3) integration tests against seeded PostgreSQL data (T038, SC-003)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

import pytest

from hotel_api.presentation.cli.seed import main as seed_main

pytestmark = pytest.mark.integration

TOLERANCE = 0.01
D = Decimal


def half_up(value: Decimal) -> float:
    return float(value.quantize(D("0.01"), rounding=ROUND_HALF_UP))


@pytest.fixture()
def seeded(client, test_settings, capsys):
    seed_main(settings=test_settings)
    capsys.readouterr()


def test_overall_occupancy_matches_golden_values(client, seeded):
    response = client.get("/api/v1/kpis/hotel/summary?year=2026")
    assert response.status_code == 200
    summary = response.json()
    assert summary["booking_count"] == 1000
    assert summary["nights_sold"] == 5379
    assert summary["total_revenue_dkk"] == pytest.approx(11234034.00, abs=TOLERANCE)
    assert summary["available_room_nights"] == 78110
    assert summary["occupancy_rate_pct"] == pytest.approx(6.89, abs=TOLERANCE)


def test_seasonal_occupancy_matches_golden_values(client, seeded):
    response = client.get("/api/v1/kpis/hotel/by-season?year=2026")
    assert response.status_code == 200
    rows = {r["season"]: r for r in response.json()["items"]}
    assert list(rows) == ["low", "mid", "high"]

    assert rows["low"]["season_days"] == 89
    assert rows["low"]["available_room_nights"] == 19046
    assert rows["low"]["nights_sold"] == 1779
    assert rows["low"]["occupancy_rate_pct"] == pytest.approx(9.34, abs=TOLERANCE)

    assert rows["mid"]["season_days"] == 153
    assert rows["mid"]["available_room_nights"] == 32742
    assert rows["mid"]["nights_sold"] == 1837
    assert rows["mid"]["occupancy_rate_pct"] == pytest.approx(5.61, abs=TOLERANCE)

    assert rows["high"]["season_days"] == 123
    assert rows["high"]["available_room_nights"] == 26322
    assert rows["high"]["nights_sold"] == 1763
    assert rows["high"]["occupancy_rate_pct"] == pytest.approx(6.70, abs=TOLERANCE)


def test_room_type_occupancy_matches_golden_values(client, seeded):
    response = client.get("/api/v1/kpis/hotel/by-room-type?year=2026")
    assert response.status_code == 200
    rows = {r["room_type"]: r for r in response.json()["items"]}

    assert rows["Suite"]["available_room_nights"] == 9490
    assert rows["Suite"]["nights_sold"] == 706
    assert rows["Suite"]["occupancy_rate_pct"] == pytest.approx(7.44, abs=TOLERANCE)

    assert rows["Standard Single"]["available_room_nights"] == 9855
    assert rows["Standard Single"]["nights_sold"] == 628
    assert rows["Standard Single"]["occupancy_rate_pct"] == pytest.approx(6.37, abs=TOLERANCE)

    assert rows["LOFT Suite"]["available_room_nights"] == 9490
    assert rows["LOFT Suite"]["nights_sold"] == 487
    assert rows["LOFT Suite"]["occupancy_rate_pct"] == pytest.approx(5.13, abs=TOLERANCE)


def test_satisfaction_metrics_match_seeded_reviews_and_update_on_new_review(client, seeded):
    reviews = client.get("/api/v1/reviews").json()["items"]
    assert len(reviews) == 500

    def expected_satisfaction(subset: list[dict]) -> tuple[int, float, float]:
        count = len(subset)
        if count == 0:
            return 0, 0.0, 0.0
        mean = half_up(D(sum(r["rating"] for r in subset)) / count)
        satisfied = half_up(D(sum(1 for r in subset if r["rating"] >= 4) * 100) / count)
        return count, mean, satisfied

    summary = client.get("/api/v1/kpis/hotel/summary?year=2026").json()
    exp_count, exp_mean, exp_sat = expected_satisfaction(reviews)
    assert summary["review_count"] == exp_count == 500
    assert summary["average_satisfaction"] == pytest.approx(exp_mean, abs=TOLERANCE)
    assert summary["satisfied_share_pct"] == pytest.approx(exp_sat, abs=TOLERANCE)

    season_rows = client.get("/api/v1/kpis/hotel/by-season?year=2026").json()["items"]
    assert sum(r["review_count"] for r in season_rows) == 500
    for row in season_rows:
        subset = [r for r in reviews if r["season"] == row["season"]]
        c, m, s = expected_satisfaction(subset)
        assert row["review_count"] == c
        assert row["average_satisfaction"] == pytest.approx(m, abs=TOLERANCE)
        assert row["satisfied_share_pct"] == pytest.approx(s, abs=TOLERANCE)

    room_rows = client.get("/api/v1/kpis/hotel/by-room-type?year=2026").json()["items"]
    assert sum(r["review_count"] for r in room_rows) == 500
    for row in room_rows:
        subset = [r for r in reviews if r["room_type"] == row["room_type"]]
        c, m, s = expected_satisfaction(subset)
        assert row["review_count"] == c
        assert row["average_satisfaction"] == pytest.approx(m, abs=TOLERANCE)
        assert row["satisfied_share_pct"] == pytest.approx(s, abs=TOLERANCE)

    # Creating a review via POST /api/v1/reviews immediately updates review_count to 501
    created = client.post("/api/v1/reviews", json={"booking_id": 2, "rating": 5})
    assert created.status_code == 201
    updated = client.get("/api/v1/kpis/hotel/summary?year=2026").json()
    assert updated["review_count"] == 501

