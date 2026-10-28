# US3 Verification Record: quickstart §5 (task T073)

**Date**: 2026-10-28 | **Stack**: `docker compose up --build`, then `docker compose run --rm seed` (1000 bookings, 500 reviews, 30 drink sales)

**How it was run**: as a script with an assertion per step against `http://localhost:8000`, not by a person
clicking. The Tableau side of A1, K1 and K3 is built by the team and is not covered here (FR-017). Afterwards the
sample data was reloaded, which removes the review created by the `POST` example.

This file has no checkboxes on purpose, so it does not block `/speckit-implement`.

## Results: 23 of 23 checks as expected

| Quickstart §5 | Expected | Result |
|---------------|----------|--------|
| `summary?year=2026` | `available_room_nights` 78110, `occupancy_rate_pct` 6.89, `review_count` 500 | as expected |
| `by-season` days | 89 / 153 / 123 | as expected |
| `by-season` occupancy | low 9.34 (1779 / 19046), mid 5.61 (1837 / 32742), high 6.70 (1763 / 26322) | as expected |
| `by-room-type` occupancy | Suite 7.44 (706 / 9490), Standard Single 6.37 (628 / 9855), LOFT Suite 5.13 (487 / 9490) | as expected |
| A1 `by-country` | booking counts add up to 1000, booking shares to 100.00 | as expected |
| `GET /reviews?year=2026` | 500 items, every rating 1 to 5 | as expected |
| K3 overall | `average_satisfaction` and `satisfied_share_pct` equal the mean and the share of ratings 4 or 5 of the listed reviews (3.83 and 68.60 for this seed) | as expected |
| K3 per room type and per season | equal to the same figures calculated from the matching review subsets, review counts add up | as expected |
| `POST /reviews {"booking_id": 2, "rating": 5}` | `201`, `Location: /api/v1/reviews/<id>`, `Grand Lit`, `stay_date` 2026-01-01, `season` `low`, `year` 2026 | as expected |
| `review_count` afterwards | 501 | as expected |
| Unknown `booking_id` | `422`, field `booking_id` | as expected |
| Rating 9 | `422`, field `rating` | as expected |
| `GET /reviews/{id}`, `/0`, unknown id | `200`, `400`, `404` | as expected |
| `summary?year=2030` | occupancy 0.0, 0 reviews, satisfaction 0.0, `available_room_nights` 78110 | as expected |

The satisfaction ratings are synthetic (fixed-seed generator, research R13), so they are checked against the
reviews the API lists, not against fixed numbers.

## Not covered here

- ALOS / ADR / revenue per booking (A7) are not in the three shared endpoints yet (T091), so those responses still do
  not match the complete contract; the contract tests for them are in T086.
