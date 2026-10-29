"""All-time KPIs (FR-021) over MySQL with more than one year of data, which the one-year sample cannot show:
a year without bookings inside the span, a leap year, and a drink sold in two years. Runs against `hotel_test`."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

BOOKING = {
    "first_name": "Elena",
    "family_name": "Müller",
    "country": "Germany",
    "room_type": "Superior Double",  # high season (Jun-Aug): standard price 2,000 DKK per night
    "check_in_date": "2026-07-14",
    "days_rented": 3,
}


def post(client, **overrides):
    response = client.post("/api/v1/bookings", json={**BOOKING, **overrides})
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture()
def two_busy_years(client):
    """2026 (3 nights, 6,000 DKK) and 2028 (2 nights, 4,000 DKK) with nothing in 2027; 2028 is a leap year."""
    return post(client), post(client, check_in_date="2028-07-14", days_rented=2, country="Sweden")


@pytest.fixture()
def two_bar_years(clean_db):
    """Espresso sold in 2026 and 2027 at different prices, and a cocktail in 2027 (bar data has no write endpoint)."""
    with clean_db.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO bar_drink_sales (sales_year, drink_name, category, unit_price_dkk, units_sold) "
            "VALUES (%s, %s, %s, %s, %s)",
            [
                (2026, "Espresso", "Coffee", "70.00", 200),
                (2027, "Espresso", "Coffee", "75.00", 100),
                (2027, "Mojito", "Cocktail", "150.00", 10),
            ],
        )
    clean_db.commit()


# ---- hotel ----


def test_all_time_capacity_covers_the_empty_year_in_between_and_the_leap_year(client, check_contract, two_busy_years):
    response = client.get("/api/v1/kpis/hotel/summary?year=all")
    assert response.status_code == 200
    check_contract(response)
    body = response.json()
    assert (body["year"], body["booking_count"], body["nights_sold"], body["total_revenue_dkk"]) == (
        "all", 2, 5, 10000.0)
    assert body["available_room_nights"] == 214 * (365 + 365 + 366) == 234544
    assert client.get("/api/v1/kpis/hotel/summary?year=2028").json()["available_room_nights"] == 214 * 366
    assert client.get("/api/v1/kpis/hotel/summary?year=2027").json()["booking_count"] == 0


def test_all_time_by_season_adds_up_the_season_days_of_the_span(client, check_contract, two_busy_years):
    response = client.get("/api/v1/kpis/hotel/by-season?year=all")
    check_contract(response)
    items = response.json()["items"]
    assert [i["season_days"] for i in items] == [89 + 89 + 90, 153 * 3, 123 * 3]
    assert [i["booking_count"] for i in items] == [0, 0, 2]
    assert [i["available_room_nights"] for i in items] == [214 * 268, 214 * 459, 214 * 369]
    assert sum(i["revenue_share_pct"] for i in items) == 100.0


def test_all_time_by_country_room_type_and_season_rank_over_every_year(client, check_contract, two_busy_years):
    countries = client.get("/api/v1/kpis/hotel/by-country?year=all")
    check_contract(countries)
    assert [(i["revenue_rank"], i["country"], i["revenue_dkk"]) for i in countries.json()["items"]] == [
        (1, "Germany", 6000.0),
        (2, "Sweden", 4000.0),
    ]
    room_types = client.get("/api/v1/kpis/hotel/by-room-type?year=all")
    check_contract(room_types)
    top = room_types.json()["items"][0]
    assert (top["room_type"], top["booking_count"], top["revenue_dkk"], top["available_room_nights"]) == (
        "Superior Double", 2, 10000.0, 27 * 1096)
    grid = client.get("/api/v1/kpis/hotel/by-room-type-and-season?year=all")
    check_contract(grid)
    cell = next(i for i in grid.json()["items"] if (i["room_type"], i["season"]) == ("Superior Double", "high"))
    assert (cell["booking_count"], cell["revenue_dkk"]) == (2, 10000.0)


def test_all_time_counts_the_reviews_of_every_year(client, check_contract, two_busy_years):
    first, last = two_busy_years
    for booking, rating in ((first, 5), (last, 3)):
        assert client.post("/api/v1/reviews", json={"booking_id": booking["id"], "rating": rating}).status_code == 201
    everything = client.get("/api/v1/kpis/hotel/summary?year=all")
    check_contract(everything)
    body = everything.json()
    assert (body["review_count"], body["average_satisfaction"], body["satisfied_share_pct"]) == (2, 4.0, 50.0)
    one_year = client.get("/api/v1/kpis/hotel/summary?year=2026").json()
    assert (one_year["review_count"], one_year["average_satisfaction"]) == (1, 5.0)


# ---- bar ----


def test_all_time_bar_summary_counts_a_drink_sold_in_two_years_once(client, check_contract, two_bar_years):
    response = client.get("/api/v1/kpis/bar/summary?year=all")
    check_contract(response)
    assert response.json() == {"year": "all", "drink_count": 2, "units_sold": 310, "total_revenue_dkk": 23000.0}
    assert client.get("/api/v1/kpis/bar/summary?year=2027").json()["total_revenue_dkk"] == 9000.0


def test_all_time_bar_split_and_price_tiers(client, check_contract, two_bar_years):
    split = client.get("/api/v1/kpis/bar/by-category?year=all")
    check_contract(split)
    cocktail, coffee = split.json()["items"]
    assert (cocktail["drink_count"], cocktail["units_sold"], cocktail["revenue_dkk"], cocktail["revenue_share_pct"]) == (
        1, 10, 1500.0, 6.52)
    assert (coffee["drink_count"], coffee["units_sold"], coffee["revenue_dkk"], coffee["revenue_share_pct"]) == (
        1, 300, 21500.0, 93.48)
    tiers = client.get("/api/v1/kpis/bar/by-price-tier?year=all")
    check_contract(tiers)
    budget, standard, premium = tiers.json()["items"]
    # 70.00 and 75.00 are standard (70 up to 110), 150.00 is premium
    assert (budget["units_sold"], standard["units_sold"], premium["units_sold"]) == (0, 300, 10)


def test_all_time_drink_list_ranks_each_year_on_its_own(client, check_contract, two_bar_years):
    response = client.get("/api/v1/bar/drink-sales?year=all")
    check_contract(response)
    assert [(i["year"], i["drink_name"], i["revenue_rank"], i["units_rank"]) for i in response.json()["items"]] == [
        (2026, "Espresso", 1, 1),
        (2027, "Espresso", 1, 1),
        (2027, "Mojito", 2, 2),
    ]
    only_2027 = client.get("/api/v1/bar/drink-sales?year=2027").json()["items"]
    assert [(i["drink_name"], i["revenue_rank"]) for i in only_2027] == [("Espresso", 1), ("Mojito", 2)]
