# Research: Hotel Kong Arthur Operations & Analytics Platform

**Feature**: `001-hotel-analytics-platform` | **Date**: 2026-10-28 | **Plan**: [plan.md](plan.md)

Phase 0 output of `/speckit-plan`. Every open point in the plan's Technical Context is settled here
as **Decision / Rationale / Alternatives considered**. No `NEEDS CLARIFICATION` remains. The
decision log at the end is the record that Constitution Principle X asks for.

## Facts gathered before deciding

**Sample data (T3)**, checked with a throw-away script outside the repository:

- `international_names_with_rooms_1000.csv` has 1,000 data rows (the file has no trailing newline)
  and the columns `First Name, Family Name, Country, Room Type, Days Rented, Season, Price`. It
  contains 20 countries, all 8 room types and the seasons `low` 332, `mid` 335 and `high` 333.
  `Days Rented` ranges from 1 to 10. Every `Price` is a whole number of DKK and divisible by
  `Days Rented`.
- 54 rows contain the family name `M�ller`. The file stores the literal Unicode replacement
  character (U+FFFD) where `ü` used to be, so the original letter is lost in the file itself.
  Everything else is ASCII.
- `drinks_menu_with_sales.csv` is UTF-8 **with a BOM**, uses `;` as delimiter and a decimal comma
  (`72,47`), and has 30 rows: 20 `Cocktail` and 10 `Coffee`.
- Nightly rates (`Price / Days Rented`) fall in tight bands per room type and season. Every one of
  the 1,000 rows fits the bands chosen in R9.

**Tooling**: one team laptop runs Python 3.9.6, and a `.pyc` committed under `.specify/` was
compiled by Python 3.15. Local Python versions differ across the team. Docker 29.7 and Compose
v5.4 are available.

**Tableau** (checked 2026-10-27; see Sources):

- Web Data Connector 3.0 is deprecated and will be removed with the Tableau 26.3 release.
- Tableau now recommends the **REST API Connector** on Tableau Exchange. It needs Tableau 2023.3+
  and a JDBC REST driver, uses HTTP GET only, reads JSON (with a JSONPath to the records) or CSV,
  and is extract-only.
- The JSON file connector reads local files only.

---

## R1. Backend language and web framework

- **Decision**: Python 3.13 (`python:3.13-slim` image) with **FastAPI 0.16x** on **Uvicorn 0.5x**.
  Endpoints are synchronous `def` functions; FastAPI runs them in its thread pool. DTOs are
  Pydantic 2 models. FastAPI's generated documentation is switched off (`docs_url=None`,
  `redoc_url=None`, `openapi_url=None`, see R4).
- **Rationale**: The team plan (TM) chose Python. Pydantic DTOs give the presentation layer
  type-checked JSON input and output without hand-written parsing. Synchronous endpoints match the
  blocking MySQL driver and are easier to explain than async. Python 3.13 is supported until 2029
  and every dependency ships wheels for it. Running everything in the image makes the different
  local Python versions irrelevant.
- **Alternatives considered**:
  - Flask: needs extra libraries for validation and serialisation.
  - Django REST Framework: its ORM-centred design blurs the explicit data layer the constitution
    asks for.
  - Python 3.14: also fine, but 3.13 has the longest track record with the chosen libraries.

## R2. Database and driver

- **Decision**: **MySQL 8.4 LTS** (`mysql:8.4`), InnoDB, `utf8mb4` throughout. The data layer uses
  **PyMySQL 1.2 with the `rsa` extra**, hand-written parameterised SQL and no ORM. Each HTTP request
  (or CLI run) opens one connection with autocommit off. The composition root commits when the
  request succeeds and rolls back on an error.
- **Rationale**: MySQL is required (T1). 8.4 is a long-term-support release with abundant
  documentation; 9.7 (the newer LTS) offers nothing this project needs. MySQL 8.4 authenticates with
  `caching_sha2_password`, which PyMySQL supports through `cryptography` (the `rsa` extra). PyMySQL
  is pure Python, so the image needs no compiler. Plain SQL in repositories makes the data layer
  easy to point to and explain (Q3, Q5). One transaction per request means a booking change is
  either fully stored or not at all.
- **Alternatives considered**:
  - mysqlclient: faster, but needs `gcc` and `libmysqlclient-dev` in the image.
  - SQLAlchemy ORM: hides the SQL the team must defend, and is not needed for five tables.
  - aiomysql: async gives no benefit here.
  - Connection pooling: unnecessary at this scale; it can be added in the data layer alone.

## R3. Layer boundaries and how they are enforced

- **Decision**: The backend package `hotel_api` has exactly three layer packages:
  `presentation` (REST routers, DTOs, error mapping and the seed CLI adapter), `business` (domain
  models, rules, KPI calculators, services, repository protocols) and `data` (connection handling
  and repositories).
  - Two root modules sit outside the layers: `main.py` is the **composition root** that wires the
    layers together, and `config.py` reads settings.
  - The business layer defines the repository interfaces (`business/ports.py`, Python `Protocol`s)
    that the data layer implements.
  - `presentation/api/dependencies.py` declares service providers typed with business services.
    `main.py` binds them to request-scoped factories that build repositories and services.
  - An architecture test parses every module's imports and fails when:
    - `presentation` imports `data`;
    - `business` imports `presentation`, `data`, `fastapi` or `pymysql`;
    - `data` imports `presentation` or `business.services`.
- **Rationale**: Calls run presentation → business → data. Imports from `data` to
  `business.domain`/`business.ports` exist only so the data layer can map rows to domain models
  (Principle III gives the data layer that job). Pointing to `main.py` answers "where are the layers
  connected?" (Q3). Swapping MySQL touches only `data/` plus the compose file. Swapping the
  frontend for the hotel's booking system touches nothing in the backend (Q5).
- **Alternatives considered**:
  - Services importing repositories directly: this couples business to MySQL and breaks Q5.
  - import-linter: works, but adds a tool to learn. A 30-line pytest is easier to explain.

## R4. API contract: OpenAPI 3.0.3 design-first, and how contract and code stay in sync

- **Decision**: [contracts/openapi.yaml](contracts/openapi.yaml) (**OpenAPI 3.0.3**) is the single
  authoritative contract. It stays in the spec folder; nothing copies it.
  - The Swagger UI container mounts it read-only. The test container mounts it too.
  - FastAPI's own generated contract (OpenAPI 3.1) is switched off, so only one contract can be seen.
  - The sync mechanism has three automated parts:
    1. `openapi-spec-validator` checks that the file is valid OpenAPI 3.0.3.
    2. A **route-parity test** checks that the (method, path) pairs registered in the FastAPI app
       exactly equal those in the contract (HEAD/OPTIONS are ignored).
    3. **Contract tests** call every operation through FastAPI's `TestClient` and validate status
       code, content type, documented headers and body with **openapi-core 0.23**:
       `OpenAPI.from_file_path(...).validate_response(...)`, fed by `openapi_core.testing.MockRequest`
       and `MockResponse`. Every response schema uses `additionalProperties: false`, so an
       undocumented field fails the test.
- **Rationale**: The team chose 3.0 (constitution V). FastAPI generates 3.1 and cannot emit 3.0, so
  3.0.3 can only be authoritative design-first. Validating real responses catches drift in both
  directions, which answers Q7. One file avoids drift between copies.
- **Alternatives considered**:
  - Code-first, exporting FastAPI's 3.1 output plus a diff test: rejected, because it contradicts
    the team's 3.0 choice and the generated schemas are less precise (Problem Details, nullable
    fields).
  - Schemathesis property-based testing: powerful, but its random inputs make results noisier for
    a two-week project. It can be added later.
  - A copy of the contract inside `backend/`: rejected, because two files drift.

## R5. REST resource design, status codes and error format

- **Decision**: All endpoints sit under `/api/v1`. Domain resources are `room-types`, `bookings`,
  `reviews` and `bar/drink-sales`. KPI reports are read-only resources under `kpis/hotel/*` and
  `kpis/bar/*`, with **one table per grain**: summary, by room type, by season, by room type and
  season, by country, by category and by price tier.
  - Collections and KPI tables return `{"items": [...]}`. Summaries are single objects.
  - Methods: `GET` reads. `POST` creates and returns `201` with a `Location` header. `PUT` replaces
    a booking and returns `200`. `DELETE` returns `204`.
  - Error status codes:
    - `400`: malformed JSON, or an invalid query/path parameter.
    - `404`: unknown id in the path.
    - `422`: well-formed body that breaks a field or business rule.
    - `503`: database unavailable.
  - Errors are **RFC 9457 Problem Details** (`application/problem+json`) with an `errors` list of
    `{field, message}`. The frontend uses it to show the message next to the field (US1 scenario 4).
  - Resources carry per-record derived fields: a booking's `season` and `year`, and a drink's
    `revenue_dkk`, `price_tier` and ranks. Aggregates live only under `kpis/`.
- **Rationale**: Resources mirror the domain (Principle IV). One table per grain is what Tableau
  reads best: flat rows, each row has all KPIs of its grain, and Tableau needs no joins. The
  `items` envelope leaves room for metadata later without breaking clients. The 400/422 split
  follows HTTP semantics and is easy to defend on a concrete endpoint (Q6).
- **Alternatives considered**:
  - A generic `?group_by=` parameter: one path would need several response shapes, which weakens
    the contract and the Tableau mapping.
  - Bare JSON arrays: cannot be extended without a breaking change.
  - FastAPI's default `{"detail": ...}` errors: not a standard, and they do not name fields
    consistently.
  - `PATCH`: the constitution names `PUT`, and the form always sends the whole booking.

## R6. KPI placement (answers Q4)

- **Decision**: Every KPI and business rule (season mapping, pricing, validation, occupancy,
  revenue, satisfaction, ALOS/ADR, shares, rankings and price tiers) is implemented **once**, as
  pure functions in `business/rules/` and `business/kpis/`. Services load one reporting year of
  domain objects through the repositories and pass them to those functions. SQL only filters
  (`WHERE check_in_date >= ? AND check_in_date < ?`) and stores data. Tableau and the frontend
  display API values and never recompute a rule. Tableau may still sum, count and filter for
  interactivity (Principle VII).
- **Rationale**: One definition per KPI, unit-testable without a database, and independent of the
  database product (Q5). At 1,000 to 10,000 bookings per year, loading one year's rows and
  aggregating in Python takes milliseconds.
- **Cost of moving it** (what Q4 asks):
  - **To MySQL** (GROUP BY queries, views): less data transferred at very large volumes. But the
    season mapping and the occupancy denominator would have to be written in SQL, either as a
    second definition or as the only one. Testing would need a database, and replacing MySQL would
    mean rewriting the KPIs.
  - **To Tableau** (calculated fields): the frontend and the hotel's booking system would lose the
    figures. The formulas would live in a hand-built workbook outside the repository (FR-017), so
    they would not be versioned or tested, which breaks "one definition".
  - **Staying in the business layer**: costs a row transfer per request. Around a million rows a
    year, the fix is pre-aggregated tables maintained by the business layer, not a move into SQL.
- **Alternatives considered**: the two moves above; and caching KPI results, which was rejected
  because it would make "live" depend on cache invalidation.

## R7. What "live" means in the running system (answers Q9)

- **Decision**: "Live" follows the Clarify answer: on-demand pull.
  - Every write is committed before its 2xx response.
  - KPIs are computed on every request.
  - Every API response carries `Cache-Control: no-store`.
  - The frontend reloads the list after each create, edit or delete.
  - Tableau re-pulls the data when the CFO refreshes the extract (R14). The dashboard shows the
    database state at that moment, well inside the 5-second limit (SC-004).
- **Rationale**: This is the simplest mechanism that meets FR-005 and SC-004, and it is the only
  one Tableau's connector supports (GET plus extract refresh).
- **Alternatives considered**:
  - WebSockets or Server-Sent Events: Tableau cannot consume them.
  - Frontend polling: not needed for a single receptionist.
  - Database triggers maintaining KPI tables: a second definition plus staleness risk.

## R8. Seasons, calendar and attribution

- **Decision**: `business/rules/seasons.py` maps months to seasons: `low` = Jan, Feb, Nov;
  `mid` = Mar, Apr, May, Sep, Oct; `high` = Jun, Jul, Aug, Dec.
  - It also derives the number of days per season from the calendar of the reporting year. For
    2026 that is 89 / 153 / 123 / 365, exactly the spec's figures.
  - A booking (and its revenue and nights) belongs entirely to the season and year of its
    `check_in_date`, even when the stay crosses into another season or year. A review belongs to
    the season and year of its `stay_date`.
  - Season and year are not stored. They are derived when a domain object is built, so the date
    is the only source of truth.
- **Rationale**: Clarify fixed the month mapping. The day counts follow from it. Deriving instead
  of storing means no stored value can disagree with the date.
- **Alternatives considered**:
  - Hard-coding 365 days: rejected. In a leap year February 29 would hold bookings but count no
    available room-nights. This is a refinement of FR-010; see "Spec follow-ups" in the plan.
  - Splitting stays across seasons night by night: more precise, but the spec attributes by
    check-in date.

## R9. Seasonal pricing rule (FR-003 "consistent with the room type's seasonal pricing rules")

- **Decision**: Every room type has three nightly rate bands, one per season, stored as reference
  data in `room_type_rates` (values in [data-model.md](data-model.md)). Each band has a minimum,
  a maximum and a **standard rate** (the midpoint).
  - When `price_dkk` is omitted or `null`, the business layer sets
    `price = standard rate × days_rented`.
  - When `price_dkk` is given, it must be positive with at most 2 decimals, and
    `price_dkk / days_rented` must lie inside the band for that room type and the derived season.
    Otherwise the API returns `422` with a message that names the allowed range.
  - The bands come from the sample data, rounded outward to whole 100 DKK. They start at T1's
    "ca." low-season prices; for the suites they top out at T1's figures.
- **Rationale**: This makes "consistent with the pricing rules" testable, keeps all 1,000
  historical prices valid (checked), and lets the receptionist save without typing a price
  (US1 scenario 2: changing `Days Rented` recalculates the price when the field is left empty).
- **Alternatives considered**:
  - Accepting any positive price: leaves FR-003's "consistent with..." untested.
  - T1's ranges as the only band: 1,000 sample rows exceed them in high season.
  - A strict single price per season: the sample shows real prices vary within a band.

## R10. Numbers: money, rounding and percentages

- **Decision**:
  - Money is `Decimal` in the business layer, `DECIMAL(10,2)` in MySQL and a **JSON number** in
    responses (never a string).
  - Sums of money are exact.
  - Averages and rates are rounded **half-up to 2 decimals**.
  - Percentages are in percent units (0 to 100).
  - Shares inside one breakdown (category, country, room type, season, price tier) use
    **largest-remainder rounding**, so they add up to exactly 100.00.
  - Any ratio with a zero denominator returns `0` (the spec's edge case).
  - Ranks use competition ranking: equal values share a rank, and the next rank skips. Ties are
    listed by name.
- **Rationale**: Exact revenue (spec edge case on decimal prices), numbers Tableau types as
  measures, splits that visibly sum to 100% (US4 scenario 3) and deterministic rankings.
- **Alternatives considered**:
  - Floats in the business layer: rounding drift on drink prices such as 72.47.
  - Pydantic's default `Decimal`-as-string JSON: Tableau would read the values as text.
  - Unrounded percentages: noisy, and SC-003 compares against a 0.01 tolerance anyway.

## R11. Containers, start-up order and schema creation (answers Q8)

- **Decision**: One `docker-compose.yml` at the repository root. `docker compose up` (or
  `docker-compose up`) starts four services:

  | Service | Image | Host port | Starts when |
  |---------|-------|-----------|-------------|
  | `db` | `mysql:8.4` | none (not published) | immediately; healthy once the schema and reference data are queryable over TCP |
  | `api` | built from `backend/` (target `runtime`) | 8000 | `db` is healthy; healthy when `GET /api/v1/health` returns 200 |
  | `frontend` | built from `frontend/` (`nginx:1.30-alpine`) | 8080 | `api` is healthy |
  | `swagger-ui` | `swaggerapi/swagger-ui:v5.33.3` | 8081 | immediately (static contract) |

  - Two more services sit in compose **profiles**, so `up` never starts them: `seed` (profile
    `tools`, R13) and `tests` (profile `test`, R16).
  - The schema and the reference data (8 room types, 214 rooms, 24 rate bands) are created by SQL
    scripts in `db/init/`, which MySQL runs on first start with an empty volume. A third script
    creates the `hotel_test` database for the test suite.
  - The `db` healthcheck runs `SELECT COUNT(*) FROM room_types` over **TCP** (`-h 127.0.0.1`).
    During initialisation MySQL only listens on its socket, so the check cannot pass before the
    init scripts have finished.
  - Containers reach each other by service name: `api` connects to `db:3306`, and nginx proxies
    `/api/` to `http://api:8000`.
  - Configuration ships as development defaults in the compose file (database name, user,
    password, CORS origins, `TZ=Europe/Copenhagen`). None of them is a real secret.
- **Rationale**: Principle VIII asks for explicit start-up order and lookup by service name. Not
  publishing MySQL's port enforces "clients only through the API" physically (Principle IV).
- **Alternatives considered**:
  - The API creating its own tables at start-up: mixes DDL with serving, and has races when
    scaled.
  - A migration tool (Alembic or yoyo): worth it for a long-lived product, but over-sized for two
    weeks. Instead, schema changes are made by `docker compose down -v` plus `up` (documented in
    `CONTRIBUTE.md`).

## R12. Data persistence when containers stop (Principle VI, Q8)

- **Decision**: MySQL data lives in the **named volume `mysql-data`**.
  - `docker compose stop`, `down`, restarts and reboots keep all bookings, reviews and bar sales.
  - `docker compose down -v` deletes the volume. The next `up` recreates the schema and reference
    data, and `seed` reloads the sample data.
  - `README.md` documents this behaviour.
- **Rationale**: Bookings are live operational data. Losing them on `down` would surprise the
  receptionist and make the demo fragile.
- **Alternatives considered**:
  - No volume or tmpfs: data is lost on every `down`.
  - A bind mount to `./data`: file-permission problems across macOS, Windows and Linux, plus the
    risk of committing database files.

## R13. Loading the sample data (`seed`)

- **Decision**: `docker compose run --rm seed` runs
  `python -m hotel_api.presentation.cli.seed` in the API image, with `context/teacher/` mounted
  read-only. The CLI adapter (presentation layer) parses the CSV files and calls
  `SampleDataService.replace_with_sample_data(...)` in the business layer, which writes through the
  repositories. The run is **one transaction**:
  1. Delete all reviews, bookings and bar drink sales (the reference data stays).
  2. Insert the 1,000 bookings with **explicit IDs 1 to 1000**, equal to the CSV row order.
     - The check-in date is deterministic: the *k*-th row of a season gets the *k*-th date
       (cycling) of that season's dates in 2026.
     - Each row passes the same booking rules as the API (all 1,000 do).
  3. Insert 500 synthetic reviews, one for each odd booking ID. The rating is drawn by
     `random.Random(2026)` with weights 5% / 10% / 20% / 35% / 30% for ratings 1 to 5.
  4. Insert the 30 drink sales for year 2026.

  Text and number repairs:
  - The decimal comma becomes a decimal point, and the BOM is ignored.
  - `M�ller` is repaired to `Müller` through a one-entry, documented repair map.
  - Any other U+FFFD stops the seed with an error instead of storing broken text.

  Every run ends in the same state, so the command is idempotent. User-created bookings are removed
  (documented).
- **Rationale**:
  - Clarify Q5 asks for an explicit, idempotent reset/replace command.
  - The single transaction means a failed seed leaves the old data intact.
  - Booking IDs that equal CSV rows make the data traceable.
  - The repair satisfies the spec's edge case on international characters.
  - Seeding through the business layer reuses the season and pricing rules instead of copying
    them.
  - The seed is a backend entry point, not an external client, so Principle IV still holds. It
    cannot go through REST anyway, because bar sales have no write endpoint (out of scope).
- **Alternatives considered**:
  - SQL `LOAD DATA` in `db/init`: runs automatically, which contradicts Clarify Q5. It would also
    duplicate the season rule in SQL.
  - Posting the CSV through the REST API: impossible for bar sales.
  - Random dates: not reproducible.
  - Keeping `M�ller`: breaks the spec's edge case on international characters.

## R14. How Tableau gets current data (team-owned, outside this repository)

- **Decision**: Per FR-017, this repository delivers only the REST API and its contract, with no
  Tableau files and no connector code. The team builds the dashboard by hand. The intended route
  is Tableau Desktop 2023.3+ with Tableau's **REST API Connector** (Tableau Exchange, JDBC REST
  driver), pointed at the `GET` endpoints:
  - JSONPath to records is `$.items[*]` for tables and `$` for summaries.
  - The CFO refreshes the extract (Data → Refresh All Extracts) to pull current data.
  - The connector offers Basic, Bearer or OAuth authentication. The API ignores `Authorization`,
    so any dummy credentials work if the connector insists on one.

  The API makes this route easy:
  - flat rows;
  - `year` repeated in every KPI row;
  - JSON numbers;
  - ISO dates;
  - stable field names fixed by the contract;
  - no pagination (the largest table is about 1,000 rows);
  - no authentication;
  - `Cache-Control: no-store`.

  **Risk**: the team should run the connector once against `GET /api/v1/kpis/hotel/summary` as
  early as possible (quickstart §8).
- **Rationale**: Principle VI requires the plan to describe the route. WDC 3.0, which the
  constitution's Clarify list suggested, is deprecated and excluded by FR-017.
- **Alternatives considered**:
  - Web Data Connector 3.0: deprecated, removed in Tableau 26.3, and code that FR-017 keeps out of
    the repository.
  - JSON file connector with downloaded files: not live.
  - An OData v4 service: Tableau supports it, but it would add a second API style and an XML
    metadata document for one client.
  - Tableau connecting to MySQL directly: violates Principle IV, and the port is not published.

## R15. Browser frontend (F1)

- **Decision**: One static page (`index.html`, ES-module JavaScript, CSS) with no build step,
  served by `nginx:1.30-alpine` in the `frontend` container.
  - nginx also proxies `/api/` to the API, so the page calls `/api/v1/...` on its own origin and
    needs no CORS.
  - The page lists bookings and provides a create/edit form and a delete-with-confirmation action.
  - The room-type list and its rate bands come from `GET /api/v1/room-types`.
  - Season and price come back from the API. JavaScript implements **no** business rule: it never
    maps months to seasons and never calculates prices.
  - Validation messages from Problem Details appear next to the fields.
  - When room type, check-in date or nights change, the price field is cleared, so the API
    recalculates the price unless the user types one.
- **Rationale**: The smallest thing that satisfies F1 inside Docker (OQ-1 resolved toward the
  compose container). No business logic in the client keeps Principle VII true for every client.
- **Alternatives considered**:
  - React or Vite: a build toolchain for one form.
  - GitHub Pages: violates Principle VIII (OQ-1), and would need a public backend URL and CORS.
  - Server-rendered templates in the API: would mix UI into the presentation layer of a
    JSON-only API.

## R16. Test strategy and how tests run (Principle IX)

- **Decision**: pytest 9 with four suites:

  | Suite | Purpose | Needs MySQL |
  |-------|---------|-------------|
  | `tests/unit` | every rule and KPI function in `business/` (seasons, day counts, pricing bands and standard price, booking and review validation, revenue, occupancy, satisfaction, ALOS/ADR, shares that sum to 100, ranking, price tiers, zero-division rules, seed transformation) | no |
  | `tests/contract` | every operation in the contract, success and error statuses, validated with openapi-core; route parity; contract file validity | yes (`hotel_test`) |
  | `tests/integration` | repositories against MySQL; seed idempotency (run twice, same counts and totals); the sample data's KPIs match the golden values in [quickstart.md](quickstart.md) | yes (`hotel_test`) |
  | `tests/architecture` | the import rules from R3, and a scan proving the repository contains no Tableau files (`.twb`, `.twbx`, `.tbm`, `.tds`, `.tdsx`, `.hyper`; FR-017) | no |

  - Tests run in Docker: `docker compose run --rm tests`. This uses the `test` image target, mounts
    the repository at `/repo` (backend sources, contract, `db/init`, sample CSVs and the whole tree
    for the FR-017 scan), and reaches the `db` service.
  - Fixtures rebuild the `hotel_test` schema from `db/init/` once per session and empty the
    operational tables before each test, so dev data in `hotel` is never touched.
  - Unit and architecture tests also run on any local Python ≥ 3.13.
  - `CONTRIBUTE.md` documents both ways.
- **Rationale**: Tests behave the same on every laptop. Contract tests hit real SQL, so they prove
  the whole stack against the contract (Q7).
- **Alternatives considered**:
  - SQLite for tests: a different SQL dialect gives false confidence.
  - Testcontainers: needs the Docker socket inside a container.
  - In-memory fake repositories for contract tests: duplicate repository behaviour and skip the
    SQL.

## R17. Validation limits the spec does not state (flagged for the team)

- **Decision**:
  - `days_rented` ≤ 365.
  - `check_in_date`, `stay_date` and the `year` parameter lie between 2000 and 2100.
  - Name and country are trimmed, non-empty and at most 100 characters.
  - `price_dkk` has at most 2 decimals.
  - `rating` is a whole number from 1 to 5.
- **Rationale**: These bounds keep values inside the database column types, so an extreme value
  becomes a clear `422` instead of a `500`, and keep KPIs meaningful (one booking cannot cover more
  than a reporting year).
- **Alternatives considered**: no upper bounds, which lets values such as 70,000 nights reach the
  database and fail with errors the user cannot understand. The team should confirm these bounds
  and add them to FR-003 (see "Spec follow-ups" in the plan).

---

## Architecture decision log (Principle X)

| # | Decision | Proposed by | Team status |
|---|----------|-------------|-------------|
| 1 | Python + FastAPI, synchronous endpoints (R1) | Team plan (TM), framework picked by AI | Kept |
| 2 | KPIs as pure functions in the business layer (R6) | Team plan (TM: service layer) | Kept |
| 3 | Design-first OpenAPI 3.0.3, FastAPI docs off, three-part sync check (R4) | AI (this plan) | Kept |
| 4 | Named volume `mysql-data`; `down -v` resets (R12) | AI (this plan) | Kept |
| 5 | Tableau via the REST API only; no Tableau files or connector code in the repository (R14, FR-017) | **AI proposed a Web Data Connector** (constitution, Clarify list) | **Changed by the team** on 2026-10-27: REST API only, dashboard built manually |
| 6 | Sample data by explicit `seed` command, not on `up` (R13) | AI asked in Clarify | Decided by the team (Clarify Q5) |
| 7 | Pricing bands plus standard rate (R9) | AI (this plan) | Kept |
| 8 | Repair M�ller → Müller while seeding (R13) | AI (this plan) | Kept |

Row 5 is the decision Principle X asks for: one the AI proposed and the team changed. The team
should fill in "Kept" or "Changed" for the pending rows during the plan review.

## Biggest weakness if this went to production

**There is no authentication or authorisation.** Anyone who can reach port 8000 can create,
change or delete bookings, and nothing records who did it. The spec puts this out of scope for the
prototype; production would need at least an identity provider, roles (Receptionist, CFO, booking
system), TLS and an audit log.

Two runner-up weaknesses are worth naming in Q10:

- **No room-level availability check**: overbooking beyond 214 rooms is possible.
- **Last-write-wins on concurrent edits**: there is no ETag or version check.

## Sources

- Tableau, *Web Data Connector 3.0* repository (deprecation notice):
  <https://github.com/tableau/wdc3>
- Tableau Exchange, *REST API Connector*: <https://exchange.tableau.com/products/1111>
- Tableau Help, *Web Data Connector*: <https://help.tableau.com/current/api/webdataconnector/en-us>
- Tableau Help, *OData* connector: <https://help.tableau.com/current/pro/desktop/en-us/examples_odata.htm>
- PyPI metadata (versions as of 2026-10-27): fastapi 0.162.0, pydantic 2.14.1, uvicorn 0.54.0,
  PyMySQL 1.2.3, openapi-core 0.23.1, openapi-spec-validator 0.9.0, pytest 9.2.0, httpx 0.28.1.
- Docker Hub tags (2026-10-27): `mysql:8.4`, `python:3.13-slim`, `nginx:1.30-alpine`,
  `swaggerapi/swagger-ui:v5.33.3`.
