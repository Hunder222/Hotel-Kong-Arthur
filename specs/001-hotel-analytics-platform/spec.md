# Feature Specification: Hotel Kong Arthur Operations & Analytics Platform

**Feature Branch**: `001-hotel-analytics-platform`

**Created**: 2026-10-27 | **Last Updated**: 2026-11-02 (Week 2 Demands — `Tillægsopgave_uge_2.md`)

**Status**: Active (v1.0.0 released for Week 1; Week 2 enhancements specified)

**Input**: User description: "Full system spec: cover all mandatory requirements (F1 Booking CRUD, F2 Frontend Analytics View, G1 Git v1.0.0 baseline, A1-A7 Hotel KPIs, B1-B3 Cocktail Bar, K1-K3 calculations, PostgreSQL database migration, raw API endpoints preserved for Tableau, and new 'Hotel Analytics' filtered GET endpoints) derived from constitution.md, tværfaglig_opgave_hotel_kong_arthur.md, and Tillægsopgave_uge_2.md"

## Clarifications

### Session 2026-10-27

- Q: How should the system deliver "live" data to the analytics dashboard, and which records must be editable at runtime? (FR-005) → A: On-demand REST API pull on dashboard load/refresh (<5s delay); bookings support full runtime CRUD via UI and API (`F1`), while bar sales are seeded in PostgreSQL (formerly MySQL in `v1.0.0`) and queried live via the API.
- Q: How should the three seasons (`low`, `mid`, `high`) be mapped to calendar months and day counts for seasonal pricing and occupancy calculations? (FR-010) → A: `low` = Jan, Feb, Nov (89 days in 2026; 90 in leap years); `mid` = Mar, Apr, May, Sep, Oct (153 days); `high` = Jun, Jul, Aug, Dec (123 days), totaling 365 days in 2026 (366 in leap years).
- Q: Should occupancy rate (`belægningsgrad`) be calculated from room-nights (`214` rooms) or guest capacity (`428` guests), and how are the `214` rooms distributed across the 8 room types? (FR-010) → A: Measured in room-nights across `214` rooms (`78,110` annual room-nights in 2026), with a balanced inventory of `27` rooms each for 6 room types and `26` rooms each for `Suite` and `LOFT Suite` (`6×27 + 2×26 = 214`).
- Q: Since the sample CSV files have no customer satisfaction column, how should satisfaction scores (`kundetilfredshed`) be populated and updated? (FR-011) → A: Store satisfaction in dedicated guest review records (`1`–`5` scale) in a separate `reviews` table/endpoint seeded with synthetic reviews, separate from the booking form.
- Q: Since the sample CSV files contain no calendar dates, how should the system represent "the year" when calculating annual hotel revenue (`A6`) and annual bar sales (`B1`)? (FR-007) → A: Require a calendar `check_in_date` (`YYYY-MM-DD`) on every booking (generating deterministic `2026` dates matching each CSV row's season during seeding) and derive both `Season` and the reporting year from `check_in_date`.
- Q: Should `docker compose up` automatically seed historical bookings and sales data on startup? (FR-004, SC-005) → A: No; `docker compose up` MUST start the system with the database schema and 8 static room types (`214` rooms) ready, but with zero booking history, bar sales, or reviews. A separate idempotent command MUST be used to seed (reset/replace) the database with the sample inspiration data.
- Q: Should this repository produce the Tableau dashboard itself (workbooks, data sources, extracts or connector code), or only the data Tableau reads? (FR-006, FR-017) → A: Only the REST/JSON API, its OpenAPI contract, and the web frontend prototype. The repository MUST NOT produce Tableau files such as `.twb`, `.twbx` or `.tbm`.

### Amendments after planning, 2026-10-28 & 2026-10-29

- `FR-003` lists the value limits the plan introduced (research R17): at most `365` nights, dates between `2000` and `2100`, text up to `100` characters, prices with at most `2` decimals.
- `FR-010` derives the available room-nights and the season day counts from the calendar of the reporting year instead of a fixed 365-day year (`78,110` and `89` / `153` / `123` for `2026`; `366` days in a leap year).
- **Receptionist Frontend UX Enhancements (2026-10-29)**:
  - `FR-018`: The booking interface MUST display a dynamic price breakdown preview (standard nightly rate, selected days rented, and calculated total standard price in DKK) before the user creates or saves a booking.
  - `FR-019`: The booking interface form MUST allow setting a custom fixed price per night (`price_per_night_dkk`) alongside the total price field (`price_dkk`), enforcing mutual exclusivity (only one manual price field may be active at a time, automatically computing the corresponding other field for convenience).
  - `FR-020`: The booking interface MUST provide a distinct, visually separated "Edit Mode" when modifying existing bookings (prominent styling, dedicated banner/status, clear cancel-edit action) to clearly distinguish editing from new booking creation.
- **Tableau Raw API Release (`v1.0.0`, 2026-10-29)**:
  - Released as `v1.0.0` with a parameterless 11-operation REST API (`health`, `room-types`, `bookings`, `reviews`, `bar/drink-sales`) backed by MySQL so Tableau could ingest the raw tables directly.

### Week 2 Demands (`Tillægsopgave_uge_2.md`, 2026-11-02)

Per `context/teacher/Tillægsopgave_uge_2.md` (`T4`) and team architectural decisions:

1. **Git Baseline Preservation (`v1.0.0`, `G1` / `FR-023`)**:
   - The Week 1 commit (`018396b`) has been released in Git as `v1.0.0` prior to Week 2 development so the original MySQL + raw-Tableau-API solution remains accessible for the presentation.
2. **Database Layer Migration to PostgreSQL (`FR-004`, `FR-005`)**:
   - Hotel Kong Arthur requested that the solution **not** use MySQL. The database layer is migrated to **PostgreSQL** (`postgres:17-alpine`, `psycopg[binary]` in `backend/src/hotel_api/data/`, and PostgreSQL DDL in `db/init/*.sql`), demonstrating strict 3-layer isolation (`T2 › Q5`).
3. **Existing Raw API Preserved As-Is for Tableau (`FR-006`, `FR-017`)**:
   - All 11 existing operations across the 5 existing Swagger UI headers (`Health`, `Reference data`, `Bookings`, `Reviews`, `Bar`) MUST continue to work as-is (with parameterless raw collection `GET` endpoints) so raw data can still feed into Tableau without changes.
4. **Backend Analytics Processing & New `"Hotel Analytics"` Swagger UI Header with Filter Attributes (`FR-007`–`FR-016`, `FR-021`)**:
   - To allow clients to skip the Tableau step and read data analytics directly from the REST API, all hotel and bar KPI calculations (`A1`–`A7`, `B1`–`B3`, `K1`–`K3`) are processed in the backend business layer (`business/kpis/`).
   - In Swagger UI, the 5 current section headers are kept untouched, and a new header called **`Hotel Analytics`** is added containing 9 `GET` endpoints with filter attributes:
     - `GET /api/v1/kpis/hotel/summary` (filters: `year`, `season`, `room_type`, `country`)
     - `GET /api/v1/kpis/hotel/by-room-type` (filters: `year`, `season`, `room_type`, `country`)
     - `GET /api/v1/kpis/hotel/by-season` (filters: `year`, `season`, `room_type`, `country`)
     - `GET /api/v1/kpis/hotel/by-room-type-and-season` (filters: `year`, `season`, `room_type`, `country`)
     - `GET /api/v1/kpis/hotel/by-country` (filters: `year`, `season`, `room_type`, `country`)
     - `GET /api/v1/kpis/bar/summary` (filters: `year`, `category`, `price_tier`)
     - `GET /api/v1/kpis/bar/by-drink` (filters: `year`, `category`, `price_tier`)
     - `GET /api/v1/kpis/bar/by-category` (filters: `year`, `category`, `price_tier`)
     - `GET /api/v1/kpis/bar/by-price-tier` (filters: `year`, `category`, `price_tier`)
5. **Frontend Prototype Displays API Analytics (`F2`, `FR-022`)**:
   - The browser frontend prototype (`frontend/`) MUST display these hotel and bar analytics calculations (`A1`–`A7`, `B1`–`B3`, `K1`–`K3`) read directly from the **`Hotel Analytics`** REST API endpoints, with interactive filter controls and live updates when bookings change.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage Room Bookings (Priority: P1)

> **User Story (T1 format)**: *"Som Receptionist ønsker jeg at kunne oprette, redigere og slette bookinger, så systemet altid viser de aktuelle reservationer og nøgletal uden forsinkelse."*

**Mandatory Scope Covered**: `F1` (and live PostgreSQL data foundation for `A1`–`A7`, `K1`–`K3`)

The Receptionist uses a browser-based booking interface to view existing room reservations, register new guest bookings, update details on existing bookings (such as guest name, country of origin, room type, check-in date, stay duration, or price), and cancel/remove bookings. Any booking change is immediately persisted in the central PostgreSQL database so that both direct REST API analytics (`Hotel Analytics` endpoints and the frontend analytics view) and external Tableau dashboards reflect current reservations rather than static historical snapshots. External booking systems used by the hotel can also submit the same create, update, and delete operations through the system's central service interface.

**Why this priority**: Without the ability to create, edit, and delete bookings and persist them centrally in PostgreSQL, the platform cannot satisfy the core requirement of moving from static historical data to live operational data (`F1`). It is also the foundational data source for all hotel KPIs.

**Independent Test**: Can be fully tested by opening the booking interface, creating a new booking for a specific room type and country, editing its stay duration, verifying that the updated booking appears in the booking list and updates hotel revenue/occupancy totals in the API and frontend analytics view, and finally deleting the booking and confirming its removal.

**Acceptance Scenarios**:

1. **Given** the Receptionist has the booking interface open, **When** they submit a valid new booking with guest first name, family name, country, room type (one of the 8 valid room types), check-in date (`YYYY-MM-DD`), days rented (positive integer), and price in DKK, **Then** the system derives the season (`low`, `mid`, or `high`) and reporting year from the check-in date, stores the booking in PostgreSQL, assigns it a unique identifier, displays it in the active booking list, and includes it in subsequent KPI calculations.
2. **Given** an existing booking in the system, **When** the Receptionist modifies one or more booking fields (e.g., changing `Days Rented` from `3` to `5` or updating the `Room Type`) and saves, **Then** the system validates and persists the changes in PostgreSQL and updates all dependent revenue and occupancy figures.
3. **Given** an existing booking in the system, **When** the Receptionist selects to delete that booking, **Then** the booking is removed from PostgreSQL and excluded from subsequent KPI calculations.
4. **Given** the Receptionist attempts to create or update a booking with invalid or missing mandatory data (such as an unknown room type, an invalid check-in date, zero or negative days rented, or a negative price), **When** they submit the form, **Then** the system rejects the change, preserves existing data unchanged, and displays a clear validation message explaining which field is invalid.

---

### User Story 2 - Room & Country Revenue Overview by Season via API & Frontend (Priority: P1)

> **User Story (T1 format)**: *"Som Hotel CFO ønsker jeg at se hotellets samlede årsindtjening samt indtjening fordelt på værelsestype, sæson og gæsternes hjemland direkte via REST API'et og i frontend-prototypen (samt i Tableau), så jeg kan identificere hvilke værelsestyper og lande Hotel Kong Arthur tjener flest penge på."*

**Mandatory Scope Covered**: `A2`, `A3`, `A4`, `A5`, `A6`, `K2`, `F2`

The Hotel CFO queries the backend's **`Hotel Analytics`** REST API endpoints (and views the frontend prototype's analytics section or Tableau dashboard) to inspect total hotel room revenue (`A6`, `K2`), revenue broken down by room type and season (`A2`), revenue broken down by guest country (`A3`), rankings of the highest-earning room types (`A4`), and rankings of the highest-earning guest countries (`A5`), with optional query filters (`year`, `season`, `room_type`, `country`). When bookings are added, modified, or deleted in User Story 1, querying the API or refreshing the frontend analytics view immediately reflects the updated revenue figures.

**Why this priority**: Revenue analysis across room types, seasons, and countries is the primary executive decision-making capability requested by Hotel Kong Arthur (`A2`–`A6`, `K2`), and `Tillægsopgave_uge_2.md` requires these calculations to be served directly by the REST API and displayed in the frontend prototype.

**Independent Test**: Can be independently tested by calling `/api/v1/kpis/hotel/summary`, `/api/v1/kpis/hotel/by-room-type`, `/api/v1/kpis/hotel/by-season`, `/api/v1/kpis/hotel/by-room-type-and-season`, and `/api/v1/kpis/hotel/by-country` (with and without filter attributes) and inspecting the frontend analytics view against a known set of seeded and newly created bookings.

**Acceptance Scenarios**:

1. **Given** bookings exist across multiple room types, seasons (`low`, `mid`, `high`), and guest countries, **When** the Hotel CFO queries the `Hotel Analytics` endpoints or opens the frontend analytics view, **Then** the backend calculates and returns the exact revenue per room type per season (`A2`) and revenue per country (`A3`) matching the authoritative revenue calculation (`K2`).
2. **Given** revenue data across all 8 room types and guest countries, **When** the Hotel CFO inspects `/api/v1/kpis/hotel/by-room-type` and `/api/v1/kpis/hotel/by-country`, **Then** room types (`A4`) and countries (`A5`) are ranked in descending order of total revenue generated in DKK (`revenue_rank`), and support filtering by `year`, `season`, `room_type`, and `country`.
3. **Given** bookings recorded for a reporting year (or across all years when `year=all` or omitted), **When** the Hotel CFO queries `/api/v1/kpis/hotel/summary`, **Then** the API and frontend display the hotel's total room revenue (`A6`).
4. **Given** a Receptionist creates, edits, or deletes a booking in the system, **When** the Hotel CFO queries the `Hotel Analytics` API or views the frontend analytics section, **Then** the annual revenue, room-type revenue, and country revenue figures immediately reflect the change.

---

### User Story 3 - Guest Origin, Occupancy Rate & Customer Satisfaction via API & Frontend (Priority: P2)

> **User Story (T1 format)**: *"Som Hotel CFO ønsker jeg at se hvor gæsterne kommer fra, hotellets belægningsgrad og kundetilfredshed direkte via REST API'et og i frontend-prototypen, så jeg kan vurdere kapacitetsudnyttelsen, gæstesammensætningen og gæsternes oplevelse."*

**Mandatory Scope Covered**: `A1`, `K1`, `K3`, `F2`

The Hotel CFO uses the **`Hotel Analytics`** REST API endpoints and the frontend analytics view to inspect the geographic distribution of guests by country of origin (`A1`), monitor the hotel's occupancy rate (`belægningsgrad`, `K1`) relative to Hotel Kong Arthur's capacity of 214 rooms, and track customer satisfaction (`kundetilfredshed`, `K3`) across stays, seasons, and room types.

**Why this priority**: Understanding who visits the hotel (`A1`), how well the 214 rooms are utilized (`K1`), and how satisfied guests are (`K3`) completes the core operational health indicators calculated in the backend.

**Independent Test**: Can be tested independently by verifying that `/api/v1/kpis/hotel/by-country`, `/api/v1/kpis/hotel/summary`, `/api/v1/kpis/hotel/by-room-type`, and `/api/v1/kpis/hotel/by-season` calculate and expose guest count/share per country (`A1`), occupancy rate percentage based on the hotel's 214-room capacity (`K1`), and average customer satisfaction score (`K3`), and that all three metrics render in the frontend analytics view.

**Acceptance Scenarios**:

1. **Given** bookings with guest countries of origin recorded in the system, **When** the Hotel CFO queries `/api/v1/kpis/hotel/by-country` (with optional `year`, `season`, `room_type`, `country` filters) or views the frontend analytics panel, **Then** the system returns and displays the number (`booking_count`) and proportion (`booking_share_pct`) of bookings from each country (`A1`).
2. **Given** Hotel Kong Arthur's fixed capacity of 214 rooms and the recorded room-nights (`Days Rented`) across bookings, **When** the Hotel CFO queries the hotel KPI endpoints (`summary`, `by-room-type`, `by-season`, `by-room-type-and-season`), **Then** the backend presents the calculated occupancy rate (`belægningsgrad`, `K1`) and `available_room_nights` overall and per season/room type, scaled accurately to any active filter.
3. **Given** guest review records with satisfaction ratings (`1` to `5` scale) in the system, **When** the Hotel CFO queries the hotel KPI endpoints (`summary`, `by-room-type`, `by-season`), **Then** the backend presents `review_count`, average satisfaction score (`average_satisfaction`, `K3`), and `satisfied_share_pct` (ratings $\ge 4$) overall, by room type, and by season.

---

### User Story 4 - Cocktail Bar Sales & Drink Category Split via API & Frontend (Priority: P2)

> **User Story (T1 format)**: *"Som Hotel CFO ønsker jeg at se Helene Christines samlede årlige barsalg, omsætningen pr. drink og procentfordelingen mellem cocktails og kaffe direkte via REST API'et og i frontend-prototypen, så jeg kan vurdere indtjeningen og kategorifordelingen i lobbybaren."*

**Mandatory Scope Covered**: `B1`, `B2`, `B3`, `F2`

The Hotel CFO queries the **`Hotel Analytics`** bar endpoints (`/api/v1/kpis/bar/summary`, `/api/v1/kpis/bar/by-drink`, `/api/v1/kpis/bar/by-category`) and views the dedicated lobby bar analytics section in the frontend prototype covering Helene Christine's bar operations (20 cocktail types and 10 coffee types). The API and frontend display Helene Christine's total bar sales revenue for the year (`B1`), calculated revenue and ranking per individual drink (`B2`), and the percentage split between `Cocktail` and `Coffee` sales (`B3`), while keeping the raw `GET /api/v1/bar/drink-sales` endpoint intact under `Bar` for Tableau.

**Why this priority**: Lobby bar performance (`B1`–`B3`) is a mandatory business analytics deliverable that must now be calculated in the backend API and shown in the frontend prototype (`Tillægsopgave_uge_2.md`).

**Independent Test**: Can be tested independently by seeding the 30 menu items (20 cocktails and 10 coffees) and verifying that `/api/v1/kpis/bar/summary` (`B1`), `/api/v1/kpis/bar/by-drink` (`Price × Units Sold`, `B2`), and `/api/v1/kpis/bar/by-category` (`B3`, summing to 100%) return the exact golden figures with optional `year`, `category`, and `price_tier` filters, and render in the frontend prototype.

**Acceptance Scenarios**:

1. **Given** bar sales records for Helene Christine's 20 cocktails and 10 coffee types, **When** the Hotel CFO queries `GET /api/v1/kpis/bar/summary` or views the frontend bar analytics section, **Then** the system returns and displays Helene Christine's total bar revenue in DKK (`total_revenue_dkk`), `drink_count`, and total `units_sold` (`B1`).
2. **Given** each drink's unit price in DKK and units sold, **When** the Hotel CFO queries `GET /api/v1/kpis/bar/by-drink` (with optional `year`, `category`, `price_tier` filters), **Then** the backend returns the exact calculated revenue (`revenue_dkk = unit_price_dkk × units_sold`) for each drink along with `revenue_rank`, `units_rank`, and `price_tier` (`B2`).
3. **Given** sales across the `Cocktail` and `Coffee` categories, **When** the Hotel CFO queries `GET /api/v1/kpis/bar/by-category`, **Then** the backend returns and the frontend displays the percentage split between cocktails and coffee (`revenue_share_pct` and `unit_share_pct`, summing to `100%` when unfiltered) (`B3`).

---

### User Story 5 - Self-Chosen KPI: Stay Length, Revenue per Booking & Bar Price-Tier Demand (Priority: P3)

> **User Story (T1 format)**: *"Som Hotel CFO ønsker jeg at analysere gennemsnitlig opholdslængde og gennemsnitlig indtjening pr. booking på tværs af sæsoner samt efterspørgslen fordelt på prisklasser i baren direkte via REST API'et og i frontend-prototypen, så jeg kan optimere prissætning og varesortiment."*

**Mandatory Scope Covered**: `A7`, `F2` (and refines team `US4` into an independent analytical story)

To fulfill the requirement for a team-selected KPI (`A7`) and address the team's interest in price-tier purchasing behavior (`US4`), the backend calculates and exposes via **`Hotel Analytics`** (and renders in the frontend prototype):
1. **Average Length of Stay (ALOS), Average Daily Rate (ADR), and Average Revenue per Booking** overall and segmented by room type, season, and room type × season (`A7` hotel KPI).
2. **Bar Demand by Price Tier & Popularity** (`US4` / `A7` bar KPI via `GET /api/v1/kpis/bar/by-price-tier` and `GET /api/v1/kpis/bar/by-drink`), classifying drinks into `budget` (`< 70` DKK), `standard` (`70 ≤ price < 110` DKK), and `premium` (`≥ 110` DKK) tiers and ranking top-selling drinks by unit volume alongside their unit price.

**Why this priority**: Provides high-value pricing and assortment insights (`A7`, `US4`) computed directly by the backend API and rendered in the frontend prototype.

**Independent Test**: Can be tested independently by verifying that the hotel KPI endpoints return `average_length_of_stay_nights`, `average_daily_rate_dkk`, and `average_revenue_per_booking_dkk`, and that `/api/v1/kpis/bar/by-price-tier` returns unit volume, revenue, and percentage shares across the 3 price tiers.

**Acceptance Scenarios**:

1. **Given** bookings with `Days Rented` and `Price` across seasons and room types, **When** the Hotel CFO queries the hotel analytics endpoints or views the frontend KPI panel (`A7`), **Then** the system returns and displays Average Length of Stay (in nights), Average Daily Rate (DKK per night), and Average Revenue per Booking (DKK).
2. **Given** bar sales with unit prices and units sold, **When** the Hotel CFO queries `GET /api/v1/kpis/bar/by-price-tier` and `GET /api/v1/kpis/bar/by-drink`, **Then** the system groups sales into `budget`, `standard`, and `premium` price tiers and ranks items by `units_sold` so the CFO can see whether customers buy more expensive or cheaper products and which items sell the most units.

---

### Edge Cases

- **Invalid or out-of-bounds booking inputs**: What happens when a user or external client submits a booking with `0` or negative `Days Rented`, a negative `Price`, an unrecognized `Room Type` (outside the 8 hotel room types), an invalid or missing `Check-In Date` (not in `YYYY-MM-DD` format), or empty guest name/country fields? The system MUST reject the request with a descriptive `422` validation error and leave stored data untouched.
- **Invalid filter query parameters on `"Hotel Analytics"` endpoints**: What happens when a client calls a `/api/v1/kpis/*` endpoint with an invalid query parameter (e.g., `?year=abc`, `?year=1999`, `?season=winter`, `?room_type=Penthouse`, `?category=Tea`, `?price_tier=luxury`, or an empty `?country=`)? The system MUST return `400 Bad Request` (`application/problem+json`) naming the invalid query parameter.
- **Non-existent booking on edit or delete**: What happens when a user or external client attempts to edit or delete a booking ID that does not exist (or was already deleted)? The system MUST return a clear `404 Not Found` error without affecting other records.
- **Division by zero on empty datasets or filtered slices**: How does the system handle KPI calculations (`belægningsgrad`, average satisfaction, percentage split between cocktails and coffee, or average length of stay/ADR) if the database or a filtered slice has zero bookings, zero reviews, or zero sales? The system MUST return `0` (or `0.0`) safely rather than failing or producing `NaN`/null errors.
- **Character encoding in international guest names**: The baseline guest dataset includes international characters (e.g., `Müller`, `Johansson`, `Dubois`). The system MUST preserve and display international characters and diacritics accurately across booking creation, PostgreSQL UTF-8 storage, API retrieval, and frontend/dashboard display.
- **Decimal formatting in baseline drink prices**: Historical bar sample records use comma decimal separators (e.g., `72,47` DKK). Initial data seeding MUST normalize prices into standard numeric decimals without rounding loss so revenue calculations (`Price × Units Sold`) are exact.

## Requirements *(mandatory)*

### Mandatory Scope Traceability

Per Constitution Phase Gate 1 (*Specify*), the table below maps every mandatory requirement from the Constitution (`A1`–`A7`, `B1`–`B3`, `K1`–`K3`, `F1`, `F2`, `G1`) to the User Stories and Functional Requirements in this specification:

| Scope ID | Description | User Story | Functional Requirements |
|----------|-------------|------------|-------------------------|
| `F1` | Browser frontend that creates, edits, and deletes bookings in the backend | US1 | FR-001, FR-002, FR-003, FR-004, FR-005, FR-018, FR-019, FR-020 |
| `F2` | Browser frontend prototype displays the calculated hotel and bar analytics read from the REST API (`T4`) | US2, US3, US4, US5 | FR-022 |
| `G1` | Week 1 work preserved and accessible via Git (`v1.0.0`) prior to Week 2 changes (`T4`) | All | FR-023 |
| `A1` | Where the guests come from (countries) | US3 | FR-006, FR-009, FR-021, FR-022 |
| `A2` | Revenue per room type, per season | US2 | FR-006, FR-007, FR-008, FR-021, FR-022 |
| `A3` | Revenue per country | US2 | FR-006, FR-007, FR-009, FR-021, FR-022 |
| `A4` | The room types that earn the most | US2 | FR-007, FR-008, FR-021, FR-022 |
| `A5` | The countries that earn the most | US2 | FR-007, FR-009, FR-021, FR-022 |
| `A6` | The hotel's revenue for the year | US2 | FR-007, FR-021, FR-022 |
| `A7` | One interesting KPI chosen by the team (ALOS, ADR, Revenue per Booking & Bar Price-Tier Demand) | US5 | FR-015, FR-016, FR-021, FR-022 |
| `B1` | Helene Christine's total bar sales for the year | US4 | FR-012, FR-013, FR-021, FR-022 |
| `B2` | Revenue per drink | US4 | FR-012, FR-013, FR-021, FR-022 |
| `B3` | Percentage split between cocktails and coffee for Helene Christine | US4 | FR-014, FR-021, FR-022 |
| `K1` | Calculate occupancy rate (`belægningsgrad`) | US3 | FR-010, FR-021, FR-022 |
| `K2` | Calculate revenue (`indtjening`) | US2 | FR-007, FR-021, FR-022 |
| `K3` | Calculate customer satisfaction (`kundetilfredshed`) | US3 | FR-011, FR-021, FR-022 |

### Functional Requirements

#### Booking Management & Live PostgreSQL Data (`F1`, `T4`)

- **FR-001**: The system MUST provide a browser-based user interface allowing the Receptionist to view all bookings, create a new booking, edit an existing booking, and delete an existing booking.
- **FR-002**: The system MUST expose booking create, read, update, and delete operations through its central service interface so that both the browser user interface and the hotel's external booking system can manage bookings using the same rules.
- **FR-003**: The system MUST validate every booking on creation and update, requiring:
  - Non-empty `First Name`, `Family Name`, and `Country`.
  - A `Room Type` belonging to Hotel Kong Arthur's 8 room types (`Standard Single`, `Grand Lit`, `Standard Double`, `Superior Double`, `Junior Suite`, `Spa Executive`, `Suite`, `LOFT Suite`).
  - `Days Rented` as a whole number greater than or equal to `1`.
  - A valid `Check-In Date` (`YYYY-MM-DD`), from which the business layer derives the booking's `Season` (`low` = Jan, Feb, Nov; `mid` = Mar, Apr, May, Sep, Oct; `high` = Jun, Jul, Aug, Dec) and reporting year.
  - `Price` (total booking price in DKK) as a positive number consistent with the room type's seasonal pricing rules (or automatically calculated from the room type's seasonal nightly rate multiplied by `Days Rented` when not manually overridden).
  - Value limits that keep every value inside what the data store can hold and every KPI meaningful: `Days Rented` at most `365`; `Check-In Date` (and a review's stay date) between `2000-01-01` and `2100-12-31`, written exactly as `YYYY-MM-DD`; guest names and country trimmed and at most `100` characters; `Price` with at most `2` decimals. A value outside these limits is rejected like any other invalid value.
  - Booking records and the booking form exclude satisfaction ratings (which are stored separately in `reviews` per `FR-011`).
- **FR-004**: Starting the system via `docker compose up` MUST initialize the **PostgreSQL** database schema (`postgres:17-alpine`) and the 8 static hotel room types (`214` rooms) with **no booking history, bar sales, or guest review data** (`0` bookings, `0` bar sales, `0` reviews) so new bookings can be created immediately. The system MUST NOT use MySQL (`T4`). The system MUST provide a separate explicit, idempotent command (`docker compose run --rm seed`, which resets/replaces sample records without duplicates and synchronises identity sequences) to seed PostgreSQL with the sample inspiration data: the baseline guest booking records (`1,000` bookings seeded with deterministic `2026` `Check-In Date` values within each row's corresponding season months), synthetic guest review records (`500` reviews on a `1`–`5` scale in the `reviews` table), and Helene Christine's lobby bar sales records (`30` drinks: `20` cocktails and `10` coffee types for reporting year `2026`).
- **FR-005**: All changes to bookings (create, edit, delete) MUST be persisted immediately in the central **PostgreSQL** data store so that subsequent on-demand REST API queries from the browser interface, direct API analytics consumers, or the Tableau dashboard return the updated live state within 5 seconds on load/refresh. Runtime CRUD is required for bookings (`F1`), whereas lobby bar sales are seeded into PostgreSQL and queried dynamically through the REST API.

#### Raw Endpoints Preserved for Tableau + Backend `"Hotel Analytics"` Endpoints (`A1`–`A7`, `B1`–`B3`, `K1`–`K3`)

- **FR-006**: The system MUST preserve all 11 existing REST operations across the 5 existing Swagger UI headers (`Health`, `Reference data`, `Bookings`, `Reviews`, `Bar`) as-is — including the parameterless raw collection endpoints `GET /api/v1/bookings`, `GET /api/v1/room-types`, `GET /api/v1/reviews`, and `GET /api/v1/bar/drink-sales` — so that raw data can still feed into Tableau without modification. In addition, the system MUST add a new Swagger UI header (OpenAPI tag) called **`Hotel Analytics`** exposing 9 `GET` endpoints with filter query parameters (`/api/v1/kpis/hotel/{summary,by-room-type,by-season,by-room-type-and-season,by-country}` and `/api/v1/kpis/bar/{summary,by-drink,by-category,by-price-tier}`) so clients can skip the Tableau step and retrieve backend-calculated analytics directly via the REST API.
- **FR-007**: The system MUST calculate hotel room revenue (`indtjening`, `K2`) in the backend business layer (`business/kpis/hotel.py`) and expose via **`Hotel Analytics`**:
  - Total room revenue across bookings (`A6`) in `GET /api/v1/kpis/hotel/summary`.
  - Revenue grouped by `Room Type` and `Season` (`A2`, `24` rows when unfiltered by room type/season) in `GET /api/v1/kpis/hotel/by-room-type-and-season` and by `Season` (`3` rows when unfiltered by season) in `GET /api/v1/kpis/hotel/by-season`.
  - Revenue grouped by guest `Country` (`A3`) in `GET /api/v1/kpis/hotel/by-country`.
- **FR-008**: The system MUST rank the room types by total revenue generated (`A4`, competition ranking `revenue_rank`) in `GET /api/v1/kpis/hotel/by-room-type`, showing `revenue_rank`, `room_type`, `room_count`, `booking_count`, `nights_sold`, `revenue_dkk`, and `revenue_share_pct`.
- **FR-009**: The system MUST calculate guest origin distribution (`A1`) and rank countries by total revenue generated (`A5`, competition ranking `revenue_rank`) in `GET /api/v1/kpis/hotel/by-country`, showing for each country `revenue_rank`, `country`, `booking_count`, `booking_share_pct` (`%`), `nights_sold`, `revenue_dkk`, and `revenue_share_pct` (`%`).
- **FR-010**: The system MUST calculate the hotel's occupancy rate (`belægningsgrad`, `K1`) in the backend business layer using Hotel Kong Arthur's binding capacity of **214 rooms** (available room-nights = rooms in scope × calendar days in scope: `78,110` for full year `2026`, `78,324` for a leap year):
  - $\text{Occupancy Rate (\%)} = \left(\frac{\sum \text{Days Rented}}{\text{Available Room-Nights}}\right) \times 100$
  - Exposed in `GET /api/v1/kpis/hotel/summary`, `GET /api/v1/kpis/hotel/by-room-type`, `GET /api/v1/kpis/hotel/by-season`, and `GET /api/v1/kpis/hotel/by-room-type-and-season` (using `low` = 89 days / 90 in leap year, `mid` = 153 days, `high` = 123 days, and the room inventory of `27` rooms each for 6 types and `26` rooms each for `Suite` and `LOFT Suite`).
- **FR-011**: The system MUST store guest satisfaction ratings (`1` to `5` integer scale) in a dedicated `reviews` table exposed via `GET/POST /api/v1/reviews` and `GET /api/v1/reviews/{review_id}` and calculate customer satisfaction (`kundetilfredshed`, `K3`) in the backend business layer as `review_count`, arithmetic mean `average_satisfaction`, and `satisfied_share_pct` (percentage of reviews with rating $\ge 4$) in `GET /api/v1/kpis/hotel/summary`, `GET /api/v1/kpis/hotel/by-room-type`, and `GET /api/v1/kpis/hotel/by-season`.
- **FR-012**: The system MUST store and expose Helene Christine's lobby bar catalogue of `20` cocktails and `10` coffee types both as raw rows via `GET /api/v1/bar/drink-sales` (under tag `Bar`, no query parameters) and as enriched analytical rows via `GET /api/v1/kpis/bar/by-drink` (under tag `Hotel Analytics`, with filter parameters `year`, `category`, `price_tier`).
- **FR-013**: The system MUST calculate in the backend business layer (`business/kpis/bar.py`):
  - Revenue per drink (`B2`) as $\text{Unit Price (DKK)} \times \text{Units Sold}$ (`revenue_dkk`), plus `revenue_rank`, `units_rank`, and `price_tier` in `GET /api/v1/kpis/bar/by-drink`.
  - Helene Christine's total bar sales (`B1`) as `drink_count`, `units_sold`, and `total_revenue_dkk` in `GET /api/v1/kpis/bar/summary`.
- **FR-014**: The system MUST calculate the percentage split between `Cocktail` and `Coffee` for Helene Christine (`B3`) in `GET /api/v1/kpis/bar/by-category`, returning both `revenue_share_pct` and `unit_share_pct`:
  - $\text{Category Revenue Share (\%)} = \left(\frac{\text{Category Revenue}}{\text{Total Bar Revenue in Scope}}\right) \times 100$
  - $\text{Category Unit Share (\%)} = \left(\frac{\text{Category Units Sold}}{\text{Total Bar Units Sold in Scope}}\right) \times 100$
- **FR-015**: For the team-selected hotel KPI (`A7`), the system MUST calculate in the backend business layer **Average Length of Stay (ALOS)** ($\frac{\sum \text{Days Rented}}{\text{Booking Count}}$), **Average Daily Rate (ADR)** ($\frac{\sum \text{Price}}{\sum \text{Days Rented}}$), and **Average Revenue per Booking** ($\frac{\sum \text{Price}}{\text{Booking Count}}$) and include them in `GET /api/v1/kpis/hotel/summary`, `GET /api/v1/kpis/hotel/by-room-type`, `GET /api/v1/kpis/hotel/by-season`, and `GET /api/v1/kpis/hotel/by-room-type-and-season`.
- **FR-016**: For the lobby bar price-tier and popularity analysis (`US4` / `A7`), the system MUST classify drinks into price tiers (`budget` `< 70` DKK, `standard` `70 ≤ price < 110` DKK, `premium` `≥ 110` DKK), expose per-drink `units_rank` and `price_tier` in `GET /api/v1/kpis/bar/by-drink`, and expose tier-level aggregates (`drink_count`, `units_sold`, `unit_share_pct`, `revenue_dkk`, `revenue_share_pct`) in `GET /api/v1/kpis/bar/by-price-tier`.

#### Tableau Boundary, Frontend UX & Analytics View, Filter Attributes & Git Preservation

- **FR-017**: The repository MUST NOT contain or generate Tableau files (e.g. `.twb`, `.twbx`, `.tbm`, `.tds`, `.tdsx`, `.hyper`) or Tableau-specific connector code. The API supports both direct analytics consumption via the 9 **`Hotel Analytics`** `GET` endpoints and raw data extraction for Tableau via the 4 parameterless raw collection `GET` endpoints (`bookings`, `room-types`, `reviews`, `bar/drink-sales`), totaling 20 operations across 15 paths in `contracts/openapi.yaml`.
- **FR-018**: The receptionist booking form (`frontend/`) MUST display a live price breakdown preview (derived season, standard nightly rate, number of nights, standard total price, allowed seasonal nightly band, and—when a manual price is entered—the manual per-night and total price) before the receptionist submits the form.
- **FR-019**: Next to `Total Price (DKK)` (`price_dkk`), the receptionist booking form MUST provide a `Price per Night (DKK)` (`price_per_night_dkk`) input field. Only one of the two fields may be filled at a time in the UI (typing in one locks the other and shows the computed counterpart). `POST /api/v1/bookings` and `PUT /api/v1/bookings/{booking_id}` MUST accept either `price_dkk` or `price_per_night_dkk` (storing `round_half_up(price_per_night_dkk * days_rented)` when `price_per_night_dkk` is supplied and lies within the seasonal nightly band) or neither (using the standard seasonal rate), and MUST return `422 Unprocessable Entity` on `price_per_night_dkk` if both are supplied.
- **FR-020**: When a receptionist clicks `Edit` on an existing booking, the web UI MUST switch into a visually unmistakable **Edit mode** (distinct colour scheme across page header and form card, prominent banner naming the booking ID and guest being edited, and an explicit cancel/exit button in both the banner and form actions) so editing can never be mistaken for creating a new booking.
- **FR-021**: All 9 **`Hotel Analytics`** `GET` endpoints MUST support optional filter query parameters:
  - Hotel KPI endpoints (`/api/v1/kpis/hotel/summary`, `/by-room-type`, `/by-season`, `/by-room-type-and-season`, `/by-country`) MUST accept optional `year` (integer `2000`–`2100` or `'all'`, defaulting to `'all'` when omitted), `season` (`low`, `mid`, `high`), `room_type` (one of the 8 room type names), and `country` (non-empty trimmed string up to 100 chars, case-exact match on booking country; when `country` is specified, hotel satisfaction fields that are not country-attributed report over reviews matching the `year`/`season`/`room_type` scope).
  - Bar KPI endpoints (`/api/v1/kpis/bar/summary`, `/by-drink`, `/by-category`, `/by-price-tier`) MUST accept optional `year` (integer `2000`–`2100` or `'all'`, defaulting to `'all'` when omitted), `category` (`Cocktail`, `Coffee`), and `price_tier` (`budget`, `standard`, `premium`).
  - Any invalid filter parameter value MUST return `400 Bad Request` with RFC 9457 Problem Details naming the parameter in `errors[].field`.
- **FR-022**: Per `Tillægsopgave_uge_2.md` (`F2`), the browser frontend prototype (`frontend/public/`) MUST include a **Hotel Analytics** dashboard view that fetches and displays the backend-calculated hotel and bar KPIs (`A1`–`A7`, `B1`–`B3`, `K1`–`K3`) from the `/api/v1/kpis/*` REST API endpoints, provides filter controls (e.g., `year`, `season`, `room_type`, `country`, `category`, `price_tier`), and refreshes automatically whenever bookings are created, edited, or deleted.
- **FR-023**: Per `Tillægsopgave_uge_2.md` (`G1`), the Week 1 implementation (MySQL + parameterless raw-data API) MUST be preserved in Git as tag/release `v1.0.0` so both the initial Week 1 architecture and the Week 2 PostgreSQL + `Hotel Analytics` architecture can be demonstrated at the presentation.

### Key Entities *(include if feature involves data)*

- **RoomType**: Represents one of Hotel Kong Arthur's 8 room categories (`Standard Single`, `Grand Lit`, `Standard Double`, `Superior Double`, `Junior Suite`, `Spa Executive`, `Suite`, `LOFT Suite`). Key attributes: room type name, Danish name (`name_da`), standard seasonal nightly price ranges (`low`, `mid`, `high` in DKK), guest capacity per room (`1–4` persons), and allocated room count out of the hotel's `214` total rooms.
- **Booking**: Represents a guest reservation at Hotel Kong Arthur stored in PostgreSQL. Key attributes: unique booking ID, guest first name, guest family name, guest country of origin, room type (referencing `RoomType`), check-in date (`YYYY-MM-DD`), days rented (nights), derived season (`low`, `mid`, `high`) and reporting year, and total booking price in DKK.
- **GuestReview**: Represents a guest satisfaction review stored in a dedicated `reviews` table in PostgreSQL and exposed via `/api/v1/reviews`. Key attributes: unique review ID, optional booking reference, room type, stay date, derived season (`low`, `mid`, `high`) and year, and satisfaction rating (`1`–`5` integer scale).
- **BarDrinkSale**: Represents a product on Helene Christine's lobby bar menu and its annual sales performance stored in PostgreSQL. Key attributes: unique drink ID, sales year, drink name, category (`Cocktail` or `Coffee`), unit price in DKK, units sold, and (in `Hotel Analytics`) calculated `revenue_dkk`, `revenue_rank`, `units_rank`, and `price_tier`.
- **KPIReport (`HotelSummary`, `RoomTypeKpi`, `SeasonKpi`, `RoomTypeSeasonKpi`, `CountryKpi`, `BarSummary`, `RankedDrinkSale`, `BarCategoryKpi`, `BarPriceTierKpi`)**: Represents the authoritative business metrics computed in the backend's `business/kpis/` layer and served under the **`Hotel Analytics`** Swagger UI tag, including total hotel revenue, revenue by room type/season/country, top-earning room types and countries, guest country distribution, occupancy rate (`belægningsgrad`), customer satisfaction (`kundetilfredshed`), ALOS/ADR/average revenue per booking, total bar sales, per-drink revenue and ranks, cocktail-vs-coffee percentage split, and bar demand by price tier.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A Receptionist can create, edit, or delete a booking through the browser interface in under 30 seconds, with 100% of valid changes persisted in PostgreSQL and reflected immediately in subsequent raw and `Hotel Analytics` API queries.
- **SC-002**: 100% of mandatory analytics views (`A1`–`A7`, `B1`–`B3`, `K1`–`K3`) are calculated in the backend business layer, exposed via filtered `GET` endpoints under the **`Hotel Analytics`** Swagger UI header, and displayed in the browser frontend prototype (`F2`), while the 11 raw API operations remain 100% compatible with `v1.0.0` for Tableau.
- **SC-003**: KPI figures returned by the **`Hotel Analytics`** API endpoints (and displayed in the frontend prototype and Tableau dashboard) match the system's authoritative golden reference values with 100% numerical accuracy (within `0.01` DKK / `0.01%` rounding tolerance).
- **SC-004**: After a booking is created, updated, or deleted, querying the **`Hotel Analytics`** endpoints or refreshing the frontend analytics view / Tableau extract reflects the updated hotel KPIs within 5 seconds.
- **SC-005**: The complete platform (PostgreSQL database container with empty operational tables and 8 seeded room types, backend API service, Swagger UI container, and browser frontend container) starts from a fresh checkout using a single `docker compose up` command and becomes ready to serve requests within 60 seconds without manual setup steps, while `docker compose run --rm seed` loads the sample inspiration data on demand.
- **SC-006**: The Week 1 release (`v1.0.0`) remains intact and retrievable via Git tags/releases alongside the Week 2 PostgreSQL + `Hotel Analytics` implementation.

## Assumptions

The following working assumptions and clarified decisions provide concrete, testable rules for areas where the assignment briefs (`T1` and `T4`) left room for interpretation:

- **Live Data Mechanism & Scope**: "Live data" means all runtime data is stored in the central PostgreSQL data store (`postgres-data` volume), `docker compose up` starts with an empty operational state (only the 8 room types configured, `0` bookings/sales/reviews), bookings can be created/updated/deleted continuously via the browser UI and REST API (`F1`), and both the frontend analytics view (`F2`), direct API consumers, and Tableau fetch current data from the REST API on load/refresh (within 5 seconds) rather than reading static historical files. A separate idempotent seed command loads the sample inspiration dataset (`1,000` bookings, `30` bar drink sales, and `500` synthetic guest reviews) on demand.
- **Season Definition**: Bookings derive their season (`low`, `mid`, `high`) from the month of their `Check-In Date`, matching the baseline dataset and totaling 365 days in `2026` (`low` = 89 days, `mid` = 153 days, `high` = 123 days; `low` = 90 days / 366 total in leap years):
  - `low` (Lavsæson — winter: January, February, November)
  - `mid` (Mellemsæson — spring and autumn: March, April, May, September, October)
  - `high` (Højsæson — summer and Christmas: June, July, August, December)
- **Occupancy Rate (`belægningsgrad`) Formula**: Because the baseline booking dataset records `Days Rented` per room booking (and does not record guest headcount per booking), occupancy rate (`K1`) is measured in **room-nights**: $\text{Occupancy Rate} = \frac{\sum \text{Days Rented}}{214 \times 365} \times 100$ for the full year `2026`, and scaled by season days (`89` / `153` / `123`) and room-type inventory (`27` rooms each for 6 types and `26` rooms each for `Suite` and `LOFT Suite` = `214` rooms) when segmented or filtered.
- **Customer Satisfaction (`kundetilfredshed`) Data Source**: Since the historical booking sample dataset does not include a satisfaction column, guest satisfaction ratings (`1`–`5` scale) are stored in a dedicated `reviews` table and exposed via a separate REST endpoint seeded with synthetic guest reviews, keeping the booking form strictly aligned with the CSV booking fields (`K3`).
- **Reporting Year (`A6`, `B1`)**: Every booking requires a `Check-In Date` (`YYYY-MM-DD`). Because the baseline historical CSV records do not contain calendar dates, initial seeding generates deterministic `2026` `Check-In Date` values within each row's season months, and both `Season` and reporting year (`2026`) are derived from `Check-In Date` (with bar sales representing reporting year `2026`).
- **Room Type Naming Alignment**: The 8 English room type names in the baseline dataset (`Standard Single`, `Grand Lit`, `Standard Double`, `Superior Double`, `Junior Suite`, `Spa Executive`, `Suite`, `LOFT Suite`) map 1-to-1 to the 8 Danish room type descriptions in the assignment brief (`Standard enkeltværelse`, `Grand lit værelse`, `Standard dobbeltværelse`, `Superior dobbeltværelse`, `Junior suite`, `Spa executive`, `Suite`, `LOFT suite`).
- **Dual Analytics Ownership (API/Frontend + Tableau)**: Under `Tillægsopgave_uge_2.md` (`T4`), all KPIs (`A1`–`A7`, `B1`–`B3`, `K1`–`K3`) are computed by the backend under **`Hotel Analytics`** and displayed in the frontend prototype (`F2`), while the raw endpoints remain unchanged for Tableau (`FR-017`). No Tableau files (`.twb`, `.twbx`, `.tbm`, etc.) are stored in this repository.
- **Authentication**: User authentication and role-based access control are out of scope for this prototype; both the Receptionist browser interface, the frontend analytics view, and CFO analytics clients access the service interface directly within the local environment.
