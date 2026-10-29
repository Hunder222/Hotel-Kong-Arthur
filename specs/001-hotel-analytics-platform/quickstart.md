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
curl -s http://localhost:8000/api/v1/reviews
curl -s http://localhost:8000/api/v1/bar/drink-sales
```

**Expected on a fresh volume**:

- `{"status": "ok", "database": "ok"}`.
- 8 room types whose `room_count` adds up to **214**, each with 3 rate bands.
- `{"items": []}` for `bookings`, `reviews` and `bar/drink-sales`.

## 2. Load the sample data (idempotent reset/replace)

```bash
docker compose run --rm seed
docker compose run --rm seed   # run it twice: the result must be identical
```

**Expected**: both runs report **1000 bookings, 500 reviews, 30 drink sales**. Then:

| Check | Expected |
|-------|----------|
| `GET /api/v1/bookings` | 1,000 items (no query parameters) |
| `GET /api/v1/bookings/1` | Liam Nguyen, China, Spa Executive, `check_in_date` 2026-03-01, `season` `mid`, 1 night, `price_dkk` 2577.00 |
| `GET /api/v1/bookings/21` | `family_name` **`Müller`** (repaired from the CSV's U+FFFD), `check_in_date` 2026-01-08, `season` `low` |
| `GET /api/v1/reviews` | 500 items, every `rating` from 1 to 5 |
| `GET /api/v1/bar/drink-sales` | 30 items (20 `Cocktail`, 10 `Coffee`) with `id`, `year`, `drink_name`, `category`, `unit_price_dkk`, `units_sold` |

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
- `GET /api/v1/bookings` now returns 1,001 items whose `price_dkk` sums to **11240034.00**.

```bash
# Scenario 2: edit Days Rented 3 → 5 without a price, so the price is recalculated
curl -s -X PUT http://localhost:8000/api/v1/bookings/<id> \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Elena","family_name":"Müller","country":"Germany","room_type":"Superior Double","check_in_date":"2026-07-14","days_rented":5}'
```

**Expected**:

- `200` with `price_dkk` **10000.00**.
- `GET /api/v1/bookings` now has total `days_rented` 5384 and total `price_dkk` **11244034.00**.

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
- The booking count in `GET /api/v1/bookings` is unchanged.

```bash
# Scenario 3: delete
curl -s -i -X DELETE http://localhost:8000/api/v1/bookings/<id>
curl -s -i http://localhost:8000/api/v1/bookings/<id>
```

**Expected**:

- `204`, then `404` with Problem Details.
- `GET /api/v1/bookings` is back to 1000 bookings and **11234034.00** DKK.
- Each change shows up on the very next request (SC-004 allows up to 5 seconds).

```bash
# Scenario 5: a fixed price per night instead of a total price (FR-019)
curl -s -i -X POST http://localhost:8000/api/v1/bookings \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Elena","family_name":"Müller","country":"Germany","room_type":"Superior Double","check_in_date":"2026-07-14","days_rented":3,"price_per_night_dkk":2100.50}'
```

**Expected**:

- `201`, and `price_dkk` **6301.50** (3 × 2100.50).
- The same body with `"price_dkk": 6301.50` added gives `422` with an error on `price_per_night_dkk`
  (both prices given); a `price_per_night_dkk` of 1000 gives `422` naming 1,800.00–2,200.00 DKK per
  night for Superior Double in high season.
- Delete the booking afterwards (Scenario 3) so `GET /api/v1/bookings` is back to 1000 bookings.

**In the browser** (http://localhost:8080):

- Create, edit and delete one booking. Each takes less than 30 seconds (SC-001).
- An invalid entry shows its message next to the field (a rejected price per night shows next to
  that field).
- The list refreshes after each change, and `Müller` displays correctly.
- Choosing room type, check-in date and nights shows the season, the standard rate, the nights and
  the standard total (FR-018). Typing a total price or a price per night locks the other field,
  which then shows the calculated value; **Use standard price** clears both (FR-019).
- **Edit** switches the page into Edit Mode: an "EDIT MODE" banner, other colours and **Cancel edit**
  (FR-020). Saving or cancelling returns to the normal look.

## 4. US2: Revenue by room type, season and country — Tableau Golden Reference (A2–A6, K2, FR-006–FR-009)

The team connects Tableau to `GET /api/v1/bookings` (JSONPath `$.items[*]`) and builds the revenue
views manually. Against the seeded 2026 dataset, the Tableau views must match these golden values:

| Tableau View / Grain | Expected Golden Figures (2026 sample data) |
|----------------------|--------------------------------------------|
| **Overall summary (A6, K2)** | Total revenue **11,234,034.00 DKK**, booking count **1,000**, nights sold **5,379** |
| **By room type (A4)** | 8 rows. Rank 1 **Suite** 2,119,671.00 (18.87%); rank 2 Spa Executive 1,722,396.00; rank 8 Standard Single 730,444.00 (6.50%) |
| **By country (A1, A3, A5)** | 20 rows. Rank 1 **South Korea** 767,699.00 (63 bookings, 6.30%); rank 2 China 722,928.00; rank 20 Egypt 335,786.00 |
| **By room type × season (A2)** | 24 cells. LOFT Suite / `high` = 683,198.00; Standard Single / `low` = 239,940.00. All 24 cells sum to 11,234,034.00 |
| **By season** | Revenue `low` 3,354,077.00 (29.86%), `mid` 3,809,387.00 (33.91%), `high` 4,070,570.00 (36.23%) |

## 5. US3: Guest origin, occupancy and satisfaction — Tableau Golden Reference (A1, K1, K3, FR-010, FR-011)

The team connects Tableau to `GET /api/v1/bookings`, `GET /api/v1/room-types`, and
`GET /api/v1/reviews`:

| Tableau View / Grain | Expected Golden Figures (2026 sample data) |
|----------------------|--------------------------------------------|
| **Overall occupancy (K1)** | Available room-nights **78,110** (214 rooms × 365 days); occupancy rate **6.89%** (5,379 / 78,110) |
| **Occupancy by season (K1)** | Season days 89 / 153 / 123. Occupancy `low` **9.34%** (1,779 / 19,046), `mid` **5.61%** (1,837 / 32,742), `high` **6.70%** (1,763 / 26,322) |
| **Occupancy by room type (K1)** | Suite **7.44%** (706 / 9,490), Standard Single **6.37%** (628 / 9,855), LOFT Suite **5.13%** (487 / 9,490) |
| **Guest origin (A1)** | Booking count and % share per country from `GET /api/v1/bookings` (see §4) |
| **Guest satisfaction (K3)** | 500 seeded reviews in `GET /api/v1/reviews`. Mean `rating` (1–5) and satisfied share (`rating ≥ 4`) overall, by `room_type`, and by `season` |

```bash
# K3 is live too: record a review for booking 2 (Grand Lit, low season)
curl -s -i -X POST http://localhost:8000/api/v1/reviews \
  -H 'Content-Type: application/json' -d '{"booking_id": 2, "rating": 5}'
```

**Expected**:

- `201` with `room_type` `Grand Lit`, `stay_date` 2026-01-01 and `season` `low`.
- `GET /api/v1/reviews` now returns 501 items.

## 6. US4: Cocktail bar — Tableau Golden Reference (B1–B3, FR-012–FR-014)

The team connects Tableau to `GET /api/v1/bar/drink-sales` (30 rows) and computes `revenue_dkk = unit_price_dkk * units_sold`:

| Tableau View / Grain | Expected Golden Figures (2026 sample data) |
|----------------------|--------------------------------------------|
| **Bar total (B1)** | 30 drinks, `units_sold` **179,958**, total revenue **13,448,640.34 DKK** |
| **Per drink (B2)** | 30 rows. Rank 1 **Espresso** 1,012,729.60 DKK (14,656 units, rank 1 in units). Rank 30 Margarita 171,101.67 DKK. Top cocktail: Mint Julep 524,351.62 DKK |
| **By category (B3)** | `Cocktail`: 20 drinks, 62,077 units (**34.50%**), 7,104,755.43 DKK (**52.83%**). `Coffee`: 10 drinks, 117,881 units (**65.50%**), 6,343,884.91 DKK (**47.17%**) |

## 7. US5: Self-chosen KPIs — Tableau Golden Reference (A7, FR-015, FR-016)

Calculated in Tableau from `GET /api/v1/bookings` and `GET /api/v1/bar/drink-sales`:

| Tableau View / Grain | Expected Golden Figures (2026 sample data) |
|----------------------|--------------------------------------------|
| **Hotel overall (A7)** | ALOS **5.38** nights, ADR **2,088.50 DKK**, revenue per booking **11,234.03 DKK** |
| **Hotel by season (A7)** | ALOS / ADR / revenue per booking: `low` 5.36 / 1,885.37 / 10,102.64; `mid` 5.48 / 2,073.70 / 11,371.30; `high` 5.29 / 2,308.89 / 12,223.93 |
| **Bar by price tier (A7)** | `budget` (`< 70` DKK): 10 drinks, 117,881 units (65.50%), 6,343,884.91 DKK (47.17%). `standard` (`70 ≤ price < 110`): 10 drinks, 29,306 units (16.29%), 2,739,242.59 DKK (20.37%). `premium` (`≥ 110`): 10 drinks, 32,771 units (18.21%), 4,365,512.84 DKK (32.46%) |

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
2. Connect to a server, choose **REST API**, and connect to the four parameterless `GET` endpoints
   with JSONPath `$.items[*]`:
   - `http://localhost:8000/api/v1/bookings`
   - `http://localhost:8000/api/v1/room-types`
   - `http://localhost:8000/api/v1/reviews`
   - `http://localhost:8000/api/v1/bar/drink-sales`
   If an authentication mode is mandatory, any Basic or Bearer value works, because the API ignores it.
3. Create the extracts. Confirm 1,000 bookings, 8 room types, 500 reviews, and 30 drink sales.
4. Create a booking (§3), then choose *Data → Refresh All Extracts*. The new booking appears within
   5 seconds (SC-004).
5. Build the dashboard views and KPI calculated fields from the raw data. Compare every figure with
   the golden reference tables in §4–§7 (SC-003: within 0.01 DKK / 0.01%).

## 9. Automated tests (Principle IX)

```bash
docker compose run --rm tests                            # all suites
docker compose run --rm tests pytest tests/unit          # business rules only, no DB
docker compose run --rm tests pytest tests/contract      # every endpoint vs openapi.yaml
```

**Expected**:

- All suites pass.
- The contract suite includes the route-parity test: the app's routes equal the contract's 11
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
