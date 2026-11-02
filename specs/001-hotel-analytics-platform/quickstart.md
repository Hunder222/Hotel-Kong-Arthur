# Quickstart & Validation Guide: Hotel Kong Arthur Operations & Analytics Platform

**Feature**: `001-hotel-analytics-platform` | **Date**: 2026-10-28 (Updated 2026-11-02 for Week 2 Demands) | **Plan**: [plan.md](plan.md)

This guide proves the feature works end to end. Each section maps to user stories and success
criteria in [spec.md](spec.md). Endpoint shapes are in [contracts/openapi.yaml](contracts/openapi.yaml),
and every formula is in [data-model.md](data-model.md) §7. Run the steps from the repository root.

> The expected values below come from the sample data (T3), calculated independently of the
> application. The integration tests assert the same numbers against the **`Hotel Analytics`**
> endpoints. If the API disagrees, the code is wrong (Constitution I).

## 0. Prerequisites & Git Baseline (`G1`, `FR-023`)

- Docker Engine or Docker Desktop with Compose v2 or newer (`docker compose version`).
- Free host ports **8080** (frontend), **8000** (API) and **8081** (Swagger UI). PostgreSQL (`5432`) publishes no host port.
- `curl`. Pretty-print JSON by appending `| python3 -m json.tool`.
- Confirm the Week 1 release (`v1.0.0`) is preserved in Git (`Tillægsopgave_uge_2.md`):

```bash
git tag -l v1.0.0
```

## 1. Start the whole system with one command (SC-005, FR-004)

```bash
docker compose up --build -d
docker compose ps
```

**Expected**:

- `db` (`postgres:17-alpine`), `api` and `frontend` report `healthy`, and `swagger-ui` reports `running`, within 60 seconds once the images are built or pulled.
- No other manual step is needed.
- `seed` and `tests` are **not** started; they sit in compose profiles.

```bash
curl -s http://localhost:8000/api/v1/health
curl -s http://localhost:8000/api/v1/room-types
curl -s http://localhost:8000/api/v1/bookings
curl -s http://localhost:8000/api/v1/reviews
curl -s http://localhost:8000/api/v1/bar/drink-sales
curl -s http://localhost:8000/api/v1/kpis/hotel/summary
curl -s http://localhost:8000/api/v1/kpis/bar/summary
```

**Expected on a fresh volume**:

- `{"status": "ok", "database": "ok"}`.
- 8 room types whose `room_count` adds up to **214**, each with 3 rate bands.
- `{"items": []}` for `bookings`, `reviews` and `bar/drink-sales`.
- `GET /api/v1/kpis/hotel/summary` returns `year: "all"`, `booking_count: 0`, `total_revenue_dkk: 0`, `available_room_nights: 0`, `occupancy_rate_pct: 0`.
- `GET /api/v1/kpis/hotel/summary?year=2026` returns `year: 2026`, `booking_count: 0`, `available_room_nights: 78110`, `occupancy_rate_pct: 0`.

## 2. Load the sample data into PostgreSQL (idempotent reset/replace)

```bash
docker compose run --rm seed
docker compose run --rm seed   # run it twice: the result must be identical
```

**Expected**: both runs report **1000 bookings, 500 reviews, 30 drink sales**. Then:

| Check | Expected |
|-------|----------|
| `GET /api/v1/bookings` | 1,000 items (no query parameters, raw table for Tableau) |
| `GET /api/v1/bookings/1` | Liam Nguyen, China, Spa Executive, `check_in_date` 2026-03-01, `season` `mid`, 1 night, `price_dkk` 2577.00 |
| `GET /api/v1/bookings/21` | `family_name` **`Müller`** (repaired from the CSV's U+FFFD), `check_in_date` 2026-01-08, `season` `low` |
| `GET /api/v1/reviews` | 500 items, every `rating` from 1 to 5 |
| `GET /api/v1/bar/drink-sales` | 30 raw items (`id`, `year`, `drink_name`, `category`, `unit_price_dkk`, `units_sold`) |

## 3. US1: Manage room bookings (F1, FR-001–FR-005, SC-001, SC-004)

Start from the seeded state in §2.

```bash
# Scenario 1: create without a price, so the standard rate is used
curl -s -i -X POST http://localhost:8000/api/v1/bookings \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Elena","family_name":"Müller","country":"Germany","room_type":"Superior Double","check_in_date":"2026-07-14","days_rented":3}'
```

**Expected**:

- `201 Created` with header `Location: /api/v1/bookings/1001`.
- The body has `season` `high`, `year` 2026 and `price_dkk` **6000.00** (high-season standard rate 2000 × 3).
- `GET /api/v1/kpis/hotel/summary?year=2026` now returns `booking_count: 1001` and `total_revenue_dkk: 11240034.00`.

```bash
# Scenario 2: edit Days Rented 3 → 5 without a price, so the price is recalculated
curl -s -X PUT http://localhost:8000/api/v1/bookings/1001 \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Elena","family_name":"Müller","country":"Germany","room_type":"Superior Double","check_in_date":"2026-07-14","days_rented":5}'
```

**Expected**:

- `200` with `price_dkk` **10000.00**.
- `GET /api/v1/kpis/hotel/summary?year=2026` now has `nights_sold: 5384` and `total_revenue_dkk: 11244034.00`.

```bash
# Scenario 3: delete
curl -s -i -X DELETE http://localhost:8000/api/v1/bookings/1001
curl -s -i http://localhost:8000/api/v1/bookings/1001
```

**Expected**:

- `204`, then `404` with Problem Details.
- `GET /api/v1/kpis/hotel/summary?year=2026` is back to 1000 bookings and **11234034.00** DKK.

## 4. US2: Revenue by room type, season and country via `"Hotel Analytics"` (A2–A6, K2, FR-006–FR-009, FR-021)

```bash
curl -s "http://localhost:8000/api/v1/kpis/hotel/summary?year=2026"
curl -s "http://localhost:8000/api/v1/kpis/hotel/by-room-type?year=2026"
curl -s "http://localhost:8000/api/v1/kpis/hotel/by-season?year=2026"
curl -s "http://localhost:8000/api/v1/kpis/hotel/by-room-type-and-season?year=2026"
curl -s "http://localhost:8000/api/v1/kpis/hotel/by-country?year=2026"
# Filtered queries:
curl -s "http://localhost:8000/api/v1/kpis/hotel/by-room-type?year=2026&season=high"
curl -s "http://localhost:8000/api/v1/kpis/hotel/by-country?year=2026&country=South%20Korea"
```

| `"Hotel Analytics"` Endpoint | Expected Golden Figures (2026 sample data) |
|------------------------------|--------------------------------------------|
| `GET /api/v1/kpis/hotel/summary?year=2026` (**A6, K2**) | `total_revenue_dkk` **11,234,034.00**, `booking_count` **1,000**, `nights_sold` **5,379** |
| `GET /api/v1/kpis/hotel/by-room-type?year=2026` (**A4**) | 8 rows. Rank 1 **Suite** `2,119,671.00` (`18.87%`); rank 2 Spa Executive `1,722,396.00`; rank 8 Standard Single `730,444.00` (`6.50%`) |
| `GET /api/v1/kpis/hotel/by-country?year=2026` (**A1, A3, A5**) | 20 rows. Rank 1 **South Korea** `767,699.00` (`63` bookings, `6.30%`); rank 2 China `722,928.00`; rank 20 Egypt `335,786.00` |
| `GET /api/v1/kpis/hotel/by-room-type-and-season?year=2026` (**A2**) | 24 rows. LOFT Suite / `high` = `683,198.00`; Standard Single / `low` = `239,940.00`. All 24 rows sum to `11,234,034.00` |
| `GET /api/v1/kpis/hotel/by-season?year=2026` | Revenue `low` `3,354,077.00` (`29.86%`), `mid` `3,809,387.00` (`33.91%`), `high` `4,070,570.00` (`36.23%`) |

## 5. US3: Guest origin, occupancy and satisfaction via `"Hotel Analytics"` (A1, K1, K3, FR-010, FR-011)

| `"Hotel Analytics"` Endpoint | Expected Golden Figures (2026 sample data) |
|------------------------------|--------------------------------------------|
| `GET /api/v1/kpis/hotel/summary?year=2026` (**K1, K3**) | `available_room_nights` **78,110** (214 rooms × 365 days); `occupancy_rate_pct` **6.89** (`5,379 / 78,110`); `review_count` **500** |
| `GET /api/v1/kpis/hotel/by-season?year=2026` (**K1**) | `season_days` `89` / `153` / `123`. `occupancy_rate_pct`: `low` **9.34** (`1,779 / 19,046`), `mid` **5.61** (`1,837 / 32,742`), `high` **6.70** (`1,763 / 26,322`) |
| `GET /api/v1/kpis/hotel/by-room-type?year=2026` (**K1**) | Suite **7.44** (`706 / 9,490`), Standard Single **6.37** (`628 / 9,855`), LOFT Suite **5.13** (`487 / 9,490`) |

## 6. US4: Cocktail bar via `"Hotel Analytics"` (B1–B3, FR-012–FR-014)

```bash
curl -s "http://localhost:8000/api/v1/kpis/bar/summary?year=2026"
curl -s "http://localhost:8000/api/v1/kpis/bar/by-drink?year=2026"
curl -s "http://localhost:8000/api/v1/kpis/bar/by-category?year=2026"
curl -s "http://localhost:8000/api/v1/kpis/bar/by-drink?year=2026&category=Cocktail"
```

| `"Hotel Analytics"` Endpoint | Expected Golden Figures (2026 sample data) |
|------------------------------|--------------------------------------------|
| `GET /api/v1/kpis/bar/summary?year=2026` (**B1**) | `drink_count` **30**, `units_sold` **179,958**, `total_revenue_dkk` **13,448,640.34** |
| `GET /api/v1/kpis/bar/by-drink?year=2026` (**B2**) | 30 rows. Rank 1 **Espresso** `1,012,729.60` DKK (`14,656` units, `units_rank` 1). Rank 30 Margarita `171,101.67` DKK. Top cocktail: Mint Julep `524,351.62` DKK |
| `GET /api/v1/kpis/bar/by-category?year=2026` (**B3**) | `Cocktail`: 20 drinks, `62,077` units (**34.50%**), `7,104,755.43` DKK (**52.83%**). `Coffee`: 10 drinks, `117,881` units (**65.50%**), `6,343,884.91` DKK (**47.17%**) |

## 7. US5: Self-chosen KPIs via `"Hotel Analytics"` (A7, FR-015, FR-016)

```bash
curl -s "http://localhost:8000/api/v1/kpis/bar/by-price-tier?year=2026"
```

| `"Hotel Analytics"` Endpoint | Expected Golden Figures (2026 sample data) |
|------------------------------|--------------------------------------------|
| `GET /api/v1/kpis/hotel/summary?year=2026` (**A7**) | `average_length_of_stay_nights` **5.38**, `average_daily_rate_dkk` **2,088.50**, `average_revenue_per_booking_dkk` **11,234.03** |
| `GET /api/v1/kpis/hotel/by-season?year=2026` (**A7**) | ALOS / ADR / rev per booking: `low` `5.36` / `1,885.37` / `10,102.64`; `mid` `5.48` / `2,073.70` / `11,371.30`; `high` `5.29` / `2,308.89` / `12,223.93` |
| `GET /api/v1/kpis/bar/by-price-tier?year=2026` (**A7**) | `budget` (`< 70` DKK): 10 drinks, `117,881` units (`65.50%`), `6,343,884.91` DKK (`47.17%`). `standard` (`70 ≤ price < 110`): 10 drinks, `29,306` units (`16.29%`), `2,739,242.59` DKK (`20.37%`). `premium` (`≥ 110`): 10 drinks, `32,771` units (`18.21%`), `4,365,512.84` DKK (`32.46%`) |

## 8. Browser Frontend Analytics View (`F2`, `FR-022`) & Tableau Compatibility (`FR-017`)

1. Open `http://localhost:8080` in a browser:
   - Verify the **Hotel Analytics** section displays the hotel summary cards (`A6`/`K2`, `K1`, `K3`, `A7`), breakdowns by Room Type (`A4`), Season, Room Type × Season (`A2`), and Country (`A1`, `A3`, `A5`), and Helene Christine's Lobby Bar analytics (`B1`, `B2`, `B3`, price tiers `A7`), all loaded from `/api/v1/kpis/*`.
   - Change the filter controls (`year`, `season`, `room_type`, `country`, `category`, `price_tier`) and confirm the analytics update dynamically from the REST API.
   - Create or delete a booking and confirm the Hotel Analytics figures update immediately.
2. Open Swagger UI at `http://localhost:8081`:
   - Confirm the 5 original headers (`Health`, `Reference data`, `Bookings`, `Reviews`, `Bar`) are unchanged and the new 6th header **`Hotel Analytics`** lists all 9 `GET` analytics endpoints with their filter attributes.
3. Confirm no Tableau files exist in the repository:

```bash
git ls-files | grep -Ei '\.(twb|twbx|tbm|tds|tdsx|hyper)$'
```

## 9. Automated tests (Principle IX)

```bash
docker compose run --rm tests                            # all suites
docker compose run --rm tests pytest tests/unit          # business rules & KPIs only, no DB
docker compose run --rm tests pytest tests/contract      # all 20 operations vs openapi.yaml
docker compose run --rm tests pytest tests/integration   # PostgreSQL repos, CRUD, seed, golden KPIs
docker compose run --rm tests pytest tests/architecture  # layers, frontend mirror, no Tableau files
```

**Expected**:

- All four suites pass.
- Route parity confirms the FastAPI app registers all **20 operations** in `openapi.yaml`.
- Tests use the separate `hotel_test` PostgreSQL database, leaving `hotel` untouched.
