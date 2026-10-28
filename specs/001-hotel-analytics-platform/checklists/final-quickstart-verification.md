# Final quickstart verification (task T106)

**Date**: 2026-10-28 | **What was run**: every section of [quickstart.md](../quickstart.md) on a clean copy of the
working tree (all tracked and untracked files, no `.git`, no build output), started with `docker compose up --build -d --wait`
on an empty volume.

**How**: as scripts with one assertion per expected value against `http://localhost:8000`, plus a headless Chrome run of the
booking page at `http://localhost:8080` and of Swagger UI at `http://localhost:8081`. Not done by a person clicking. The
expected values are the ones in quickstart.md, which were calculated from the sample CSV files independently of the code.

This file has no checkboxes on purpose, so it does not block `/speckit-implement`.

## Result per section

| Quickstart | What was checked | Result |
|------------|------------------|--------|
| §0 | Docker with Compose v2, ports 8080 / 8000 / 8081 free | as expected |
| §1 | One command starts `db`, `api`, `frontend` and `swagger-ui`, all healthy in **24.2 s** (build cache warm; a cold first build downloads images and packages and is longer, not measured). Empty state: 8 room types with 214 rooms and 3 rates each, empty bookings, reviews and drink sales, `available_room_nights` 78110, occupancy 0, 24 zero rows, empty `by-country`, both bar categories at 0 (10 of 10 checks) | as expected |
| §2 | Seed: 1000 bookings, 500 reviews, 30 drink sales; ids 1 to 1000; booking 1 is Liam Nguyen (2026-03-01, `mid`, 2577.00); booking 21 has family name `Müller`; running the seed twice gives an identical database state (7 of 7 checks) | as expected |
| §3 | Create (`201`, `Location`, `high`, 2026, 6000.00), KPIs after create (1001 bookings, 5382 nights, 11240034.00 DKK), edit to 5 nights (10000.00; 5384 nights, 11244034.00 DKK), invalid input (`422` on `room_type` and `days_rented`; price outside the band names 900.00–1,200.00; malformed JSON `400`), count unchanged by bad requests, delete `204` then `404`, KPIs back to 1000 and 11234034.00. In the browser: create, edit and delete each took about 0.1 s from click to confirmation, the message appears next to the field, `Müller` displays correctly | as expected |
| §4 | A2–A6, K2: total 11234034.00; Suite rank 1 (2119671.00, 18.87 %); South Korea rank 1 (767699.00, 63 bookings, 6.30 %); Egypt rank 20; LOFT Suite / `high` 683198.00 and Standard Single / `low` 239940.00; season revenue 3354077 / 3809387 / 4070570 (29.86 / 33.91 / 36.23 %); every share column sums to 100.00 | as expected |
| §5 | K1: 78110 room-nights, 6.89 % overall; seasons 9.34 / 5.61 / 6.70 %; Suite 7.44, Standard Single 6.37, LOFT Suite 5.13 %. K3: mean and share of ratings 4 or 5 equal the values calculated from the listed reviews. `POST /reviews` for booking 2: `201`, Grand Lit, 2026-01-01, `low`; `review_count` 501 | as expected |
| §6 | B1: 30 drinks, 179958 units, 13448640.34 DKK. B2: Espresso rank 1 (1012729.60, 14656 units, `units_rank` 1), Margarita rank 30 (171101.67), top cocktail Mint Julep (524351.62). B3: Cocktail 34.50 % of units and 52.83 % of revenue, Coffee 65.50 % and 47.17 % | as expected |
| §7 | A7: ALOS 5.38, ADR 2088.50, revenue per booking 11234.03; per season 5.36 / 1885.37 / 10102.64, 5.48 / 2073.70 / 11371.30, 5.29 / 2308.89 / 12223.93; price tiers 10 / 10 / 10 drinks, units 117881 / 29306 / 32771, shares 65.50 / 16.29 / 18.21 % (units) and 47.17 / 20.37 / 32.46 % (revenue); `?year=2030` gives zeros with 78110 room-nights, `by-country` empty, `?year=abc` gives `400` | as expected |
| §8 | **Repository side only**: `git ls-files` shows 0 Tableau files. The Tableau steps (connector, extract, dashboard) are not run here; they are the team's task T104 | repository side as expected; Tableau steps open |
| §9 | `docker compose run --rm tests`: 333 tests pass (198 unit, 8 architecture, 91 contract, 36 integration); the route-parity test passes, so the app's routes equal the contract's 19 operations; the tests use `hotel_test` | as expected |
| §10 | Swagger UI shows the contract (19 operations, 7 tags, no parse errors); *Try it out* on `GET /api/v1/room-types` returns `200` from the browser (CORS allows `http://localhost:8081`); a booking survives `docker compose down` and `up`; `down -v` followed by `up` gives the empty state again | as expected |

## Not covered

- The Tableau route and the dashboard (quickstart §8 steps 1 to 5, task T104).
- A cold first start, with images and packages downloaded.
- Browsers other than Chrome.
