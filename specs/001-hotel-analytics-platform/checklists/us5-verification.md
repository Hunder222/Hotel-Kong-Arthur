# US5 Verification Record: quickstart §7 (task T093)

**Date**: 2026-10-28 | **Stack**: `docker compose up --build`, then `docker compose run --rm seed` (1000 bookings, 500 reviews, 30 drink sales)

**How it was run**: as a script with an assertion per step against `http://localhost:8000`, not by a person.
The Tableau views for A7 are built by the team and are not covered here (FR-017).

This file has no checkboxes on purpose, so it does not block `/speckit-implement`.

## Results: 12 of 12 checks as expected

| Quickstart §7 | Expected | Result |
|---------------|----------|--------|
| `kpis/hotel/summary?year=2026` | ALOS 5.38 nights, ADR 2088.50 DKK, revenue per booking 11234.03 DKK | as expected |
| `kpis/hotel/by-season` | ALOS / ADR / revenue per booking: low 5.36 / 1885.37 / 10102.64, mid 5.48 / 2073.70 / 11371.30, high 5.29 / 2308.89 / 12223.93 | as expected |
| `kpis/hotel/by-room-type` | all 8 rows carry the three A7 values; Suite equals 706 / 137 nights per booking and 2119671 / 706 per night | as expected |
| `kpis/bar/by-price-tier` | `budget` 10 drinks / 117881 units / 6343884.91 DKK, `standard` 10 / 29306 / 2739242.59, `premium` 10 / 32771 / 4365512.84 | as expected |
| Tier unit shares | 65.50 / 16.29 / 18.21 | as expected |
| Tier revenue shares | 47.17 / 20.37 / 32.46 | as expected |
| Tier bounds | budget 0 to 70, standard 70 to 110, premium from 110 with `price_to_dkk` null | as expected |
| `summary?year=2030` | `200`; every count, amount, average and rate is 0; `available_room_nights` 78110 | as expected |
| `by-price-tier?year=2030` | `200`, 3 rows, 0 units | as expected |
| `?year=abc` on the summary | `400`, `application/problem+json`, error on `year` | as expected |
| `?year=abc` on `by-price-tier` | `400` | as expected |

## Contract status after US5

All 19 operations of `contracts/openapi.yaml` are implemented. The route-parity test (T037) passes without its
`xfail` marker, and the three shared hotel KPI endpoints are validated against the complete contract schemas (T086).
