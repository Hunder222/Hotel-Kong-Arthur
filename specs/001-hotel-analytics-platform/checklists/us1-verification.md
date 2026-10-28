# US1 Verification Record: quickstart §2–§3 (task T054)

**Date**: 2026-10-28 | **Stack**: `docker compose up --build` (db, api, frontend, swagger-ui all healthy), then `docker compose run --rm seed`

**How it was run**: the curl scenarios from quickstart §3 were run as a script with an assertion per step.
The browser page at `http://localhost:8080` was driven by a script in headless Chrome (puppeteer-core), not by a
person. A team member should still click through the page once before the presentation (Constitution X); the
numbers below measure system response time only, not how long a person takes to type.

This file has no checkboxes on purpose, so it does not block `/speckit-implement`.

## curl (quickstart §2 and §3): 17 of 17 steps as expected

| Step | Expected | Result |
|------|----------|--------|
| `GET /bookings?year=2026` after seed | 1,000 items | as expected |
| `GET /bookings/1` | Liam Nguyen, China, Spa Executive, 2026-03-01, `mid`, 1 night, 2577.00 | as expected |
| `GET /bookings/21` | `family_name` `Müller`, 2026-01-08, `low` | as expected |
| Scenario 1: `POST` without price | `201`, `Location: /api/v1/bookings/<id>`, `high`, 2026, `price_dkk` 6000.00 | as expected |
| Next request | 1,001 bookings | as expected |
| Scenario 2: `PUT` nights 3 → 5, no price | `200`, `price_dkk` 10000.00 | as expected |
| Scenario 4: unknown room type, 0 nights | `422`, `application/problem+json`, `errors` for `room_type` and `days_rented` | as expected |
| Scenario 4: Standard Single, low season, 4,500 DKK for 3 nights | `422`, `price_dkk` error naming 900.00–1,200.00 DKK per night | as expected |
| Scenario 4: malformed JSON | `400` | as expected |
| Count after the three bad requests | unchanged (1,001) | as expected |
| Scenario 3: `DELETE`, then `GET` | `204`, then `404` | as expected |
| Count after delete | 1,000 | as expected |

Whole curl scenario: 0.45 s.

## Browser (`http://localhost:8080`)

| Check | Result |
|-------|--------|
| Create (click → confirmation "Booking N created.") | 96 ms; limit 30 s (SC-001) |
| Edit nights 3 → 5 (click → "Booking N saved.") | 78 ms; price recalculated to 10.000,00 kr. |
| Delete with confirmation dialog | 93 ms |
| Invalid entry (0 nights) | message next to the field: "Days rented must be a whole number from 1 to 365." |
| `Müller` in the list | displayed correctly, no replacement character |
| 1,000 seeded rows | first 50 shown, "Show more" adds 50 |
| HTML in a name | shown as text, not interpreted |
| Price field after changing room type, check-in date or nights | cleared, so the API recalculates |

## Not covered here

- The KPI figures in quickstart §3 (summary after create: `booking_count` 1001, `total_revenue_dkk` 11240034.00, and so
  on) need the KPI endpoints from US2 and are not testable yet.
- Browsers other than Chrome were not tried.
