# Quickstart & Validation Guide: Hotel Kong Arthur Operations & Analytics Platform

**Feature**: `001-hotel-analytics-platform` | **Date**: 2026-10-28 | **Plan**: [plan.md](plan.md)

This guide proves the feature works end to end. Each section maps to user stories and success
criteria in [spec.md](spec.md). Endpoint shapes are in [contracts/openapi.yaml](contracts/openapi.yaml),
and every formula is in [data-model.md](data-model.md) §7. Run the steps from the repository root.

> The expected values below come from the sample data (T3), calculated independently of the
> application. The integration tests assert the same numbers. If the API disagrees, the code is
> wrong (Constitution I).

## 0. Prerequisites

- Docker Engine or Docker Desktop with Compose v2 or newer (`docker compose version`).
- Free host ports **8080** (frontend), **8000** (API) and **8081** (Swagger UI). MySQL publishes no
  port.
- `curl`. Pretty-print JSON by appending `| python3 -m json.tool`.
- For §8 only: Tableau Desktop 2023.3+ with the REST API Connector (team members only).

## 1. Start the whole system with one command (SC-005, FR-004)

```bash
docker compose up --build -d
docker compose ps
```

**Expected**:

- `db`, `api` and `frontend` report `healthy`, and `swagger-ui` reports `running`, within 60 seconds
  once the images are built or pulled.
- No other manual step is needed.
- `seed` and `tests` are **not** started; they sit in compose profiles.

```bash
curl -s http://localhost:8000/api/v1/health
curl -s http://localhost:8000/api/v1/room-types
curl -s http://localhost:8000/api/v1/bookings
curl -s "http://localhost:8000/api/v1/kpis/hotel/summary?year=2026"
```

**Expected on a fresh volume**:

- `{"status": "ok", "database": "ok"}`.
- 8 room types whose `room_count` adds up to **214**, each with 3 rate bands.
- `{"items": []}`.
- A summary with every count and amount at 0, `available_room_nights` = **78110** and
  `occupancy_rate_pct` = 0 (zero-division rule).

## 2. Load the sample data (idempotent reset/replace)

```bash
docker compose run --rm seed
docker compose run --rm seed   # run it twice: the result must be identical
```

**Expected**: both runs report **1000 bookings, 500 reviews, 30 drink sales**. Then:

| Check | Expected |
|-------|----------|
| `GET /api/v1/bookings?year=2026` | 1,000 items |
| `GET /api/v1/bookings/1` | Liam Nguyen, China, Spa Executive, `check_in_date` 2026-03-01, `season` `mid`, 1 night, `price_dkk` 2577.00 |
| `GET /api/v1/bookings/21` | `family_name` **`Müller`** (repaired from the CSV's U+FFFD), `check_in_date` 2026-01-08, `season` `low` |
| `GET /api/v1/reviews?year=2026` | 500 items, every `rating` from 1 to 5 |
| `GET /api/v1/bar/drink-sales?year=2026` | 30 items (20 `Cocktail`, 10 `Coffee`) |

The seed **removes user-created bookings and reviews**. That is the documented reset behaviour.

## 3. US1: Manage room bookings (F1, FR-001–FR-005, SC-001, SC-004)

Start from the seeded state in §2.

```bash
# Scenario 1: create without a price, so the standard rate is used
curl -s -i -X POST http://localhost:8000/api/v1/bookings \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Elena","family_name":"Müller","country":"Germany","room_type":"Superior Double","check_in_date":"2026-07-14","days_rented":3}'
```

**Expected**:

- `201 Created` with header `Location: /api/v1/bookings/<id>`.
- The body has `season` `high`, `year` 2026 and `price_dkk` **6000.00** (high-season standard
  rate 2000 × 3).
- `GET /api/v1/kpis/hotel/summary?year=2026` now shows `booking_count` 1001, `nights_sold` 5382 and
  `total_revenue_dkk` **11240034.00**.

```bash
# Scenario 2: edit Days Rented 3 → 5 without a price, so the price is recalculated
curl -s -X PUT http://localhost:8000/api/v1/bookings/<id> \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Elena","family_name":"Müller","country":"Germany","room_type":"Superior Double","check_in_date":"2026-07-14","days_rented":5}'
```

**Expected**:

- `200` with `price_dkk` **10000.00**.
- The summary now shows `nights_sold` 5384 and `total_revenue_dkk` **11244034.00**.

```bash
# Scenario 4: invalid input is rejected and nothing changes
curl -s -i -X POST http://localhost:8000/api/v1/bookings \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Elena","family_name":"Müller","country":"Germany","room_type":"Penthouse","check_in_date":"2026-07-14","days_rented":0}'
curl -s -i -X POST http://localhost:8000/api/v1/bookings \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Ann","family_name":"Lee","country":"Japan","room_type":"Standard Single","check_in_date":"2026-01-10","days_rented":3,"price_dkk":4500}'
curl -s -i -X POST http://localhost:8000/api/v1/bookings \
  -H 'Content-Type: application/json' -d '{"first_name": '
```

**Expected**:

- First call: `422`, `application/problem+json`, with `errors` for `room_type` and `days_rented`.
- Second call: `422`, with a `price_dkk` error naming 900.00–1,200.00 DKK per night for Standard
  Single in low season.
- Third call: `400` (malformed JSON).
- The booking count in the summary is unchanged.

```bash
# Scenario 3: delete
curl -s -i -X DELETE http://localhost:8000/api/v1/bookings/<id>
curl -s -i http://localhost:8000/api/v1/bookings/<id>
```

**Expected**:

- `204`, then `404` with Problem Details.
- The summary is back to 1000 bookings and **11234034.00** DKK.
- Each change shows up on the very next request (SC-004 allows up to 5 seconds).

**In the browser** (http://localhost:8080):

- Create, edit and delete one booking. Each takes less than 30 seconds (SC-001).
- An invalid entry shows its message next to the field.
- The list refreshes after each change, and `Müller` displays correctly.

## 4. US2: Revenue by room type, season and country (A2–A6, K2, FR-006–FR-009)

| Request (`?year=2026`) | Expected |
|------------------------|----------|
| `GET /api/v1/kpis/hotel/summary` | `total_revenue_dkk` **11234034.00** (A6), `booking_count` 1000, `nights_sold` 5379 |
| `GET /api/v1/kpis/hotel/by-room-type` | 8 rows. Rank 1 **Suite** 2119671.00 (18.87%); rank 2 Spa Executive 1722396.00; rank 8 Standard Single 730444.00 (6.50%). `revenue_share_pct` adds up to 100.00 |
| `GET /api/v1/kpis/hotel/by-country` | 20 rows. Rank 1 **South Korea** 767699.00 (63 bookings, 6.30%); rank 2 China 722928.00; rank 20 Egypt 335786.00. Both share columns add up to 100.00 |
| `GET /api/v1/kpis/hotel/by-room-type-and-season` | 24 rows. LOFT Suite / `high` = 683198.00; Standard Single / `low` = 239940.00. All rows add up to 11234034.00 |
| `GET /api/v1/kpis/hotel/by-season` | revenue `low` 3354077.00 (29.86%), `mid` 3809387.00 (33.91%), `high` 4070570.00 (36.23%) |

## 5. US3: Guest origin, occupancy and satisfaction (A1, K1, K3, FR-010, FR-011)

| Request (`?year=2026`) | Expected |
|------------------------|----------|
| `GET /api/v1/kpis/hotel/summary` | `available_room_nights` 78110; `occupancy_rate_pct` **6.89**; `review_count` 500 |
| `GET /api/v1/kpis/hotel/by-season` | `season_days` 89 / 153 / 123. Occupancy `low` **9.34** (1779 / 19046), `mid` **5.61** (1837 / 32742), `high` **6.70** (1763 / 26322) |
| `GET /api/v1/kpis/hotel/by-room-type` | Occupancy Suite 7.44 (706 / 9490), Standard Single 6.37 (628 / 9855), LOFT Suite 5.13 (487 / 9490) |
| `GET /api/v1/kpis/hotel/by-country` | A1: booking count and `booking_share_pct` per country (see §4) |
| K3 | `average_satisfaction` lies from 1 to 5 and equals the mean `rating` of `GET /api/v1/reviews?year=2026`. `satisfied_share_pct` equals the share of those ratings ≥ 4. Per room type and per season, the same holds for the matching review subsets |

The satisfaction values are **synthetic** (fixed-seed generator, research R13). The example in the
contract is only illustrative. The integration test pins the exact seeded values once
implemented.

```bash
# K3 is live too: record a review for booking 2 (Grand Lit, low season)
curl -s -i -X POST http://localhost:8000/api/v1/reviews \
  -H 'Content-Type: application/json' -d '{"booking_id": 2, "rating": 5}'
```

**Expected**:

- `201` with `room_type` `Grand Lit`, `stay_date` 2026-01-01 and `season` `low`.
- `review_count` in the summary becomes 501.

## 6. US4: Cocktail bar (B1–B3, FR-012–FR-014)

| Request (`?year=2026`) | Expected |
|------------------------|----------|
| `GET /api/v1/kpis/bar/summary` | `drink_count` 30, `units_sold` **179958**, `total_revenue_dkk` **13448640.34** (B1) |
| `GET /api/v1/bar/drink-sales` | 30 rows (B2). Rank 1 **Espresso** 1012729.60 DKK, which also has the most units (14656, `units_rank` 1). Rank 30 Margarita 171101.67. Top cocktail: Mint Julep 524351.62 |
| `GET /api/v1/kpis/bar/by-category` | `Cocktail`: 20 drinks, 62077 units (**34.50%**), 7104755.43 DKK (**52.83%**). `Coffee`: 10 drinks, 117881 units (**65.50%**), 6343884.91 DKK (**47.17%**). Each share column adds up to 100.00 |

## 7. US5: Self-chosen KPIs (A7, FR-015, FR-016)

| Request (`?year=2026`) | Expected |
|------------------------|----------|
| `GET /api/v1/kpis/hotel/summary` | ALOS **5.38** nights, ADR **2088.50** DKK, revenue per booking **11234.03** DKK |
| `GET /api/v1/kpis/hotel/by-season` | ALOS / ADR / revenue per booking: `low` 5.36 / 1885.37 / 10102.64; `mid` 5.48 / 2073.70 / 11371.30; `high` 5.29 / 2308.89 / 12223.93 |
| `GET /api/v1/kpis/bar/by-price-tier` | `budget` (< 70): 10 drinks, 117881 units (65.50%), 6343884.91 DKK (47.17%). `standard` (70 to < 110): 10 drinks, 29306 units (16.29%), 2739242.59 DKK (20.37%). `premium` (≥ 110, `price_to_dkk` null): 10 drinks, 32771 units (18.21%), 4365512.84 DKK (32.46%) |

Edge cases (spec):

- `GET /api/v1/kpis/hotel/summary?year=2030` returns 0 for every count, amount, average and rate,
  and `available_room_nights` = 78110. There is no error.
- `?year=abc` returns `400`.
- `GET /api/v1/kpis/bar/by-category?year=2030` returns both categories with 0 values.

## 8. Tableau route check (team, manual, outside this repository; FR-017)

The repository contains **no** Tableau files (`.twb`, `.twbx`, `.tbm`, `.tds`, `.tdsx`, `.hyper`)
and no connector code. Check it with:

```bash
git ls-files | grep -Ei '\.(twb|twbx|tbm|tds|tdsx|hyper)$'
```

**Expected**: no output.

Do this early, the first day the API runs (research R14 risk):

1. Install Tableau's **REST API Connector** from Tableau Exchange (Tableau Desktop 2023.3+), and
   put the JDBC REST driver in Tableau's `Drivers` folder.
2. Connect to a server, choose **REST API**, use the URL
   `http://localhost:8000/api/v1/kpis/hotel/by-room-type?year=2026` and the JSONPath to records
   `$.items[*]`. If an authentication mode is mandatory, any Basic or Bearer value works, because
   the API ignores it.
3. Create the extract. The 8 rows must match §4.
4. Create a booking (§3), then choose *Data → Refresh All Extracts*. The Suite or Superior Double
   figures change within 5 seconds (SC-004).
5. Build the dashboard views from the endpoints in §4–§7. Compare every figure with the tables
   above (SC-003: within 0.01 DKK / 0.01%).

## 9. Automated tests (Principle IX)

```bash
docker compose run --rm tests                            # all suites
docker compose run --rm tests pytest tests/unit          # business rules only, no DB
docker compose run --rm tests pytest tests/contract      # every endpoint vs openapi.yaml
```

**Expected**:

- All suites pass.
- The contract suite includes the route-parity test: the app's routes equal the contract's 19
  operations.
- Tests use the separate `hotel_test` database, so your data in `hotel` is untouched.

## 10. Swagger UI and persistence

- http://localhost:8081 shows this contract. *Try it out* on `GET /api/v1/room-types` returns 200;
  CORS allows the Swagger UI origin.
- `docker compose down` followed by `docker compose up -d` keeps every booking (named volume
  `mysql-data`).
- `docker compose down -v` followed by `up` gives the empty state from §1 again.

## Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| `api` waits and never starts | `db` is not healthy yet. On first start MySQL initialises the schema (about 20 seconds). Check `docker compose logs db` |
| Changed `db/init/*.sql` has no effect | Init scripts only run on an empty volume. Run `docker compose down -v` and then `docker compose up --build` (this deletes the data, so re-run `seed`) |
| Port already in use | Stop the other process, or change the host port in `docker-compose.yml` (8080 / 8000 / 8081) |
| Swagger *Try it out* fails with a CORS error | Open Swagger UI at `http://localhost:8081` (an allowed origin), not at another host name |
