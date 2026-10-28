# Feature Specification: Hotel Kong Arthur Operations & Analytics Platform

**Feature Branch**: `001-hotel-analytics-platform`

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "Full system spec: cover all mandatory requirements (F1 Booking CRUD, A1-A7 Hotel KPIs, B1-B3 Cocktail Bar, K1-K3 calculations, and Tableau REST API integration) derived from constitution.md and context/"

## Clarifications

### Session 2026-10-27

- Q: How should the system deliver "live" data to the analytics dashboard, and which records must be editable at runtime? (FR-005) → A: On-demand REST API pull on dashboard load/refresh (<5s delay); bookings support full runtime CRUD via UI and API (`F1`), while bar sales are seeded in MySQL and queried live via the API.
- Q: How should the three seasons (`low`, `mid`, `high`) be mapped to calendar months and day counts for seasonal pricing and occupancy calculations? (FR-010) → A: `low` = Jan, Feb, Nov (89 days); `mid` = Mar, Apr, May, Sep, Oct (153 days); `high` = Jun, Jul, Aug, Dec (123 days), totaling 365 days.
- Q: Should occupancy rate (`belægningsgrad`) be calculated from room-nights (`214` rooms) or guest capacity (`428` guests), and how are the `214` rooms distributed across the 8 room types? (FR-010) → A: Measured in room-nights across `214` rooms (`78,110` annual room-nights), with a balanced inventory of `27` rooms each for 6 room types and `26` rooms each for `Suite` and `LOFT Suite` (`6×27 + 2×26 = 214`).
- Q: Since the sample CSV files have no customer satisfaction column, how should satisfaction scores (`kundetilfredshed`) be populated and updated? (FR-011) → A: Store satisfaction in dedicated guest review records (`1`–`5` scale) in a separate `reviews` table/endpoint seeded with synthetic reviews, separate from the booking form.
- Q: Since the sample CSV files contain no calendar dates, how should the system represent "the year" when calculating annual hotel revenue (`A6`) and annual bar sales (`B1`)? (FR-007) → A: Require a calendar `check_in_date` (`YYYY-MM-DD`) on every booking (generating deterministic `2026` dates matching each CSV row's season during seeding) and derive both `Season` and the reporting year from `check_in_date`.
- Q: Should `docker compose up` automatically seed historical bookings and sales data on startup? (FR-004, SC-005) → A: No; `docker compose up` MUST start the system with the database schema and 8 static room types (`214` rooms) ready, but with zero booking history, bar sales, or reviews. A separate idempotent command MUST be used to seed (reset/replace) the database with the sample inspiration data.
- Q: Should this repository produce the Tableau dashboard itself (workbooks, data sources, extracts or connector code), or only the data Tableau reads? (FR-006, FR-017) → A: Only the data. For KPI data in Tableau, the repository's scope is exclusively the REST/JSON API and its OpenAPI contract. The repository MUST NOT produce Tableau files such as `.twb`, `.twbx` or `.tbm`; the team builds the Tableau dashboard manually against the API.

### Amendments after planning, 2026-10-28

- `FR-003` now lists the value limits the plan introduced (research R17): at most `365` nights, dates between `2000` and `2100`, text up to `100` characters, prices with at most `2` decimals.
- `FR-010` now derives the available room-nights and the season day counts from the calendar of the reporting year instead of a fixed 365-day year. The figures for `2026` are unchanged (`78,110`; `89` / `153` / `123`); a leap year has `366` days.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage Room Bookings (Priority: P1)

> **User Story (T1 format)**: *"Som Receptionist ønsker jeg at kunne oprette, redigere og slette bookinger, så systemet altid viser de aktuelle reservationer og nøgletal uden forsinkelse."*

**Mandatory Scope Covered**: `F1` (and live data foundation for `A1`–`A7`, `K1`–`K3`)

The Receptionist uses a browser-based booking interface to view existing room reservations, register new guest bookings, update details on existing bookings (such as guest name, country of origin, room type, check-in date, stay duration, or price), and cancel/remove bookings. Any booking change is immediately persisted in the central system so that operational reports and executive analytics reflect current reservations rather than static historical snapshots. External booking systems used by the hotel can also submit the same create, update, and delete operations through the system's central service interface.

**Why this priority**: Without the ability to create, edit, and delete bookings and persist them centrally, the platform cannot satisfy the core requirement of moving from static historical data to live operational data (`F1`). It is also the foundational data source for all hotel KPIs.

**Independent Test**: Can be fully tested by opening the booking interface, creating a new booking for a specific room type and country, editing its stay duration, verifying that the updated booking appears in the booking list and updates hotel revenue/occupancy totals, and finally deleting the booking and confirming its removal.

**Acceptance Scenarios**:

1. **Given** the Receptionist has the booking interface open, **When** they submit a valid new booking with guest first name, family name, country, room type (one of the 8 valid room types), check-in date (`YYYY-MM-DD`), days rented (positive integer), and price in DKK, **Then** the system derives the season (`low`, `mid`, or `high`) and reporting year from the check-in date, stores the booking, assigns it a unique identifier, displays it in the active booking list, and includes it in subsequent KPI calculations.
2. **Given** an existing booking in the system, **When** the Receptionist modifies one or more booking fields (e.g., changing `Days Rented` from `3` to `5` or updating the `Room Type`) and saves, **Then** the system validates and persists the changes and updates all dependent revenue and occupancy figures.
3. **Given** an existing booking in the system, **When** the Receptionist selects to delete that booking, **Then** the booking is removed from the system and excluded from subsequent KPI calculations.
4. **Given** the Receptionist attempts to create or update a booking with invalid or missing mandatory data (such as an unknown room type, an invalid check-in date, zero or negative days rented, or a negative price), **When** they submit the form, **Then** the system rejects the change, preserves existing data unchanged, and displays a clear validation message explaining which field is invalid.

---

### User Story 2 - Room & Country Revenue Overview by Season (Priority: P1)

> **User Story (T1 format)**: *"Som Hotel CFO ønsker jeg at se hotellets samlede årsindtjening samt indtjening fordelt på værelsestype, sæson og gæsternes hjemland, så jeg kan identificere hvilke værelsestyper og lande Hotel Kong Arthur tjener flest penge på."*

**Mandatory Scope Covered**: `A2`, `A3`, `A4`, `A5`, `A6`, `K2`

The Hotel CFO views an interactive analytics dashboard connected to the central system that presents total annual hotel room revenue (`A6`, `K2`), revenue broken down by room type and season (`A2`), revenue broken down by guest country (`A3`), rankings of the highest-earning room types (`A4`), and rankings of the highest-earning guest countries (`A5`). When bookings are added, modified, or deleted in User Story 1, refreshing the dashboard reflects the updated revenue figures.

**Why this priority**: Revenue analysis across room types, seasons, and countries is the primary executive decision-making capability requested by Hotel Kong Arthur (`A2`–`A6`, `K2`) and directly informs pricing and marketing strategy.

**Independent Test**: Can be independently tested by querying the revenue views in the analytics dashboard against a known set of seeded and newly created bookings, verifying that total annual revenue equals the sum of booking revenue and that breakdowns by the 8 room types, 3 seasons, and guest countries rank highest earners accurately.

**Acceptance Scenarios**:

1. **Given** bookings exist across multiple room types, seasons (`low`, `mid`, `high`), and guest countries, **When** the Hotel CFO opens the revenue overview on the dashboard, **Then** the dashboard displays the exact revenue per room type per season (`A2`) and revenue per country (`A3`) matching the system's authoritative revenue calculation (`K2`).
2. **Given** revenue data across all 8 room types and guest countries, **When** the Hotel CFO inspects the top-earner views, **Then** room types (`A4`) and countries (`A5`) are ranked in descending order of total revenue generated in DKK.
3. **Given** all bookings recorded for the active reporting year, **When** the Hotel CFO views the annual summary, **Then** the dashboard displays the hotel's total room revenue for the year (`A6`).
4. **Given** a Receptionist creates or deletes a booking in the system, **When** the Hotel CFO refreshes the analytics dashboard, **Then** the annual revenue, room-type revenue, and country revenue figures update to include the change.

---

### User Story 3 - Guest Origin, Occupancy Rate & Customer Satisfaction (Priority: P2)

> **User Story (T1 format)**: *"Som Hotel CFO ønsker jeg at se hvor gæsterne kommer fra, hotellets belægningsgrad og kundetilfredshed, så jeg kan vurdere kapacitetsudnyttelsen, gæstesammensætningen og gæsternes oplevelse."*

**Mandatory Scope Covered**: `A1`, `K1`, `K3`

The Hotel CFO uses the analytics dashboard to inspect the geographic distribution of guests by country of origin (`A1`), monitor the hotel's occupancy rate (`belægningsgrad`, `K1`) relative to Hotel Kong Arthur's capacity of 214 rooms (and up to ~428 guests), and track customer satisfaction (`kundetilfredshed`, `K3`) across stays and room types.

**Why this priority**: Understanding who visits the hotel (`A1`), how well the 214 rooms are utilized (`K1`), and how satisfied guests are (`K3`) completes the core operational health indicators required alongside revenue.

**Independent Test**: Can be tested independently by verifying that the system calculates and exposes guest count/share per country (`A1`), occupancy rate percentage based on the hotel's 214-room capacity (`K1`), and average customer satisfaction score (`K3`), and that all three metrics render accurately in the dashboard.

**Acceptance Scenarios**:

1. **Given** bookings with guest countries of origin recorded in the system, **When** the Hotel CFO views the guest origin distribution (`A1`), **Then** the dashboard shows the number and proportion of bookings/guests from each country.
2. **Given** Hotel Kong Arthur's fixed capacity of 214 rooms and the recorded room-nights (`Days Rented`) across bookings, **When** the Hotel CFO views the occupancy KPI (`K1`), **Then** the system presents the calculated occupancy rate (`belægningsgrad`) as a percentage overall and per season/room type.
3. **Given** guest review records with satisfaction ratings (`1` to `5` scale) in the system, **When** the Hotel CFO views customer satisfaction (`K3`), **Then** the system presents the average satisfaction score overall, by room type, and by season.

---

### User Story 4 - Cocktail Bar Sales & Drink Category Split (Priority: P2)

> **User Story (T1 format)**: *"Som Hotel CFO ønsker jeg at se Helene Christines samlede årlige barsalg, omsætningen pr. drink og procentfordelingen mellem cocktails og kaffe, så jeg kan vurdere indtjeningen og kategorifordelingen i lobbybaren."*

**Mandatory Scope Covered**: `B1`, `B2`, `B3`

The Hotel CFO views a dedicated lobby bar analytics section on the dashboard covering Helene Christine's bar operations (20 cocktail types and 10 coffee types). The dashboard displays Helene Christine's total bar sales revenue for the year (`B1`), total revenue and units sold per individual drink (`B2`), and the percentage split between `Cocktail` and `Coffee` sales (`B3`).

**Why this priority**: Lobby bar performance (`B1`–`B3`) is a mandatory business analytics deliverable representing a distinct revenue stream managed by Helene Christine.

**Independent Test**: Can be tested independently by loading the 30 menu items (20 cocktails and 10 coffees) and their sales figures in the system and verifying that total annual bar revenue (`B1`), per-drink revenue (`Price × Units Sold`, `B2`), and the percentage split between cocktails and coffee (`B3`, summing to 100%) match the system's authoritative calculations.

**Acceptance Scenarios**:

1. **Given** bar sales records for Helene Christine's 20 cocktails and 10 coffee types, **When** the Hotel CFO opens the cocktail bar view on the dashboard, **Then** the dashboard shows Helene Christine's total bar revenue in DKK and total units sold for the year (`B1`).
2. **Given** each drink's unit price in DKK and units sold, **When** the Hotel CFO inspects the drink breakdown (`B2`), **Then** the dashboard displays the exact revenue (`Price × Units Sold`) for each of the 30 drinks and allows ranking drinks from highest to lowest revenue.
3. **Given** sales across the `Cocktail` and `Coffee` categories, **When** the Hotel CFO views the category distribution (`B3`), **Then** the dashboard displays the percentage split between cocktails and coffee (both by revenue share and by unit volume share, each summing to `100%`).

---

### User Story 5 - Self-Chosen KPI: Stay Length, Revenue per Booking & Bar Price-Tier Demand (Priority: P3)

> **User Story (T1 format)**: *"Som Hotel CFO ønsker jeg at analysere gennemsnitlig opholdslængde og gennemsnitlig indtjening pr. booking på tværs af sæsoner samt efterspørgslen fordelt på prisklasser i baren, så jeg kan optimere prissætning og varesortiment."*

**Mandatory Scope Covered**: `A7` (and refines team `US4` into an independent analytical story)

To fulfill the requirement for a team-selected KPI (`A7`) and address the team's interest in price-tier purchasing behavior (`US4`), the Hotel CFO can inspect:
1. **Average Length of Stay (ALOS), Average Daily Rate (ADR), and Average Revenue per Booking** segmented by season and room type (`A7` hotel KPI).
2. **Bar Demand by Price Tier & Popularity** (`US4` bar KPI), showing whether guests primarily purchase higher-priced or lower-priced items and ranking the top-selling drinks by unit volume alongside their unit price.

**Why this priority**: Provides high-value pricing and assortment insights (`A7`, `US4`) built on top of the core room and bar data without blocking `P1`/`P2` foundational capabilities.

**Independent Test**: Can be tested independently by verifying that the system calculates Average Length of Stay (`total Days Rented / booking count`), Average Daily Rate (`total room revenue / total Days Rented`), Average Revenue per Booking (`total room revenue / booking count`), and bar volume/revenue grouped by price tier, and presents them on the dashboard.

**Acceptance Scenarios**:

1. **Given** bookings with `Days Rented` and `Price` across seasons and room types, **When** the Hotel CFO views the custom KPI panel (`A7`), **Then** the dashboard displays Average Length of Stay (in days), Average Daily Rate (DKK per night), and Average Revenue per Booking (DKK).
2. **Given** bar sales with unit prices and units sold, **When** the Hotel CFO views the bar price-vs-popularity analysis, **Then** the dashboard shows unit sales volume against unit price and groups sales into price tiers so the CFO can see whether customers buy more expensive or cheaper products and which items sell the most units.

---

### Edge Cases

- **Invalid or out-of-bounds booking inputs**: What happens when a user or external client submits a booking with `0` or negative `Days Rented`, a negative `Price`, an unrecognized `Room Type` (outside the 8 hotel room types), an invalid or missing `Check-In Date` (not in `YYYY-MM-DD` format), or empty guest name/country fields? The system MUST reject the request with a descriptive validation error and leave stored data untouched.
- **Non-existent booking on edit or delete**: What happens when a user or external client attempts to edit or delete a booking ID that does not exist (or was already deleted)? The system MUST return a clear "not found" error without affecting other records.
- **Division by zero on empty datasets or filtered slices**: How does the system handle KPI calculations (`belægningsgrad`, average satisfaction, percentage split between cocktails and coffee, or average length of stay) if a filtered category has zero bookings or zero sales? The system MUST return `0` (or `0.0%`) safely rather than failing or producing invalid numbers.
- **Character encoding in international guest names**: The baseline guest dataset includes international characters (e.g., `Müller`, `Johansson`, `Dubois`). The system MUST preserve and display international characters and diacritics accurately across booking creation, storage, retrieval, and dashboard display.
- **Decimal formatting in baseline drink prices**: Historical bar sample records use comma decimal separators (e.g., `72,47` DKK). Initial data seeding MUST normalize prices into standard numeric decimals without rounding loss so revenue calculations (`Price × Units Sold`) are exact.

## Requirements *(mandatory)*

### Mandatory Scope Traceability

Per Constitution Phase Gate 1 (*Specify*), the table below maps every mandatory requirement from the Constitution (`A1`–`A7`, `B1`–`B3`, `K1`–`K3`, `F1`) to the User Stories and Functional Requirements in this specification:

| Scope ID | Description | User Story | Functional Requirements |
|----------|-------------|------------|-------------------------|
| `F1` | Browser frontend that creates, edits, and deletes bookings in the backend | US1 | FR-001, FR-002, FR-003, FR-004, FR-005 |
| `A1` | Where the guests come from (countries) | US3 | FR-006, FR-009 |
| `A2` | Revenue per room type, per season | US2 | FR-006, FR-007, FR-008 |
| `A3` | Revenue per country | US2 | FR-006, FR-007, FR-009 |
| `A4` | The room types that earn the most | US2 | FR-007, FR-008 |
| `A5` | The countries that earn the most | US2 | FR-007, FR-009 |
| `A6` | The hotel's revenue for the year | US2 | FR-007 |
| `A7` | One interesting KPI chosen by the team (ALOS, ADR, Revenue per Booking & Bar Price-Tier Demand) | US5 | FR-015, FR-016 |
| `B1` | Helene Christine's total bar sales for the year | US4 | FR-012, FR-013 |
| `B2` | Revenue per drink | US4 | FR-012, FR-013 |
| `B3` | Percentage split between cocktails and coffee for Helene Christine | US4 | FR-014 |
| `K1` | Calculate occupancy rate (`belægningsgrad`) | US3 | FR-010 |
| `K2` | Calculate revenue (`indtjening`) | US2 | FR-007 |
| `K3` | Calculate customer satisfaction (`kundetilfredshed`) | US3 | FR-011 |

### Functional Requirements

#### Booking Management & Live Operational Data (`F1`)

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
- **FR-004**: Starting the system via `docker compose up` MUST initialize the database schema and the 8 static hotel room types (`214` rooms) with **no booking history, bar sales, or guest review data** (`0` bookings, `0` bar sales, `0` reviews) so new bookings can be created immediately. The system MUST provide a separate explicit, idempotent command (which resets/replaces sample records without duplicates) to seed the database with the sample inspiration data: the baseline guest booking records (`1,000` bookings seeded with deterministic `2026` `Check-In Date` values within each row's corresponding season months), synthetic guest review records (`1`–`5` scale in the `reviews` table), and Helene Christine's lobby bar sales records (`30` drinks: `20` cocktails and `10` coffee types for reporting year `2026`).
- **FR-005**: All changes to bookings (create, edit, delete) MUST be persisted immediately in the central MySQL data store so that subsequent on-demand REST API queries from the browser interface or the analytics dashboard return the updated live state within 5 seconds on load/refresh. Runtime CRUD is required for bookings (`F1`), whereas lobby bar sales are seeded into MySQL and queried dynamically through the REST API.

#### Hotel Revenue & Geographic KPIs (`A1`–`A6`, `K2`)

- **FR-006**: The system MUST expose both detailed booking records and pre-calculated KPI summaries through its central service interface so the analytics dashboard never reads static files or accesses storage directly.
- **FR-007**: The system MUST calculate hotel room revenue (`indtjening`, `K2`) in the central business logic and expose:
  - Total annual room revenue across all bookings (`A6`).
  - Revenue grouped by `Room Type` and `Season` (`A2`).
  - Revenue grouped by guest `Country` (`A3`).
- **FR-008**: The system MUST rank the 8 room types by total revenue generated (`A4`), showing total revenue, booking count, and total nights rented per room type.
- **FR-009**: The system MUST calculate guest origin distribution (`A1`) and rank countries by total revenue generated (`A5`), showing for each country the booking count, share of total bookings (`%`), total nights rented, and total revenue in DKK.

#### Capacity, Occupancy Rate & Customer Satisfaction KPIs (`K1`, `K3`)

- **FR-010**: The system MUST calculate the hotel's occupancy rate (`belægningsgrad`, `K1`) in the central business logic using Hotel Kong Arthur's binding capacity of **214 rooms** (available room-nights = rooms × the days of the reporting year, taken from the calendar: `78,110` for a 365-day year such as `2026`, `78,324` for a leap year):
  - $\text{Occupancy Rate (\%)} = \left(\frac{\sum \text{Days Rented}}{\text{Available Room-Nights}}\right) \times 100$
  - The system MUST provide overall annual occupancy rate as well as occupancy rate segmented by `Season` (for `2026`: `low` = 89 days / `19,046` room-nights; `mid` = 153 days / `32,742` room-nights; `high` = 123 days / `26,322` room-nights; in a leap year February has 29 days, so `low` has 90) and by `Room Type` (using the balanced 214-room inventory: `27` rooms each for `Standard Single`, `Grand Lit`, `Standard Double`, `Superior Double`, `Junior Suite`, and `Spa Executive`; `26` rooms each for `Suite` and `LOFT Suite`).
- **FR-011**: The system MUST store guest satisfaction ratings (`1` to `5` integer scale) in a dedicated `reviews` table exposed via its own REST API endpoint (separate from the booking form) and calculate customer satisfaction (`kundetilfredshed`, `K3`) in the central business logic as the arithmetic mean of review scores overall, per `Room Type`, and per `Season`, along with the percentage of satisfied guests (score $\ge 4$).

#### Cocktail Bar Operations & KPIs (`B1`–`B3`)

- **FR-012**: The system MUST store and expose Helene Christine's lobby bar catalogue of `20` cocktails and `10` coffee types, including each drink's `Drink Name`, `Category` (`Cocktail` or `Coffee`), unit `Price (DKK)`, and `Units Sold`.
- **FR-013**: The system MUST calculate in the central business logic:
  - Revenue per drink (`B2`) as $\text{Unit Price (DKK)} \times \text{Units Sold}$.
  - Helene Christine's total bar sales for the year (`B1`) as the sum of revenue (and sum of units sold) across all 30 drinks.
- **FR-014**: The system MUST calculate the percentage split between `Cocktail` and `Coffee` for Helene Christine (`B3`) both by revenue share and by unit volume share:
  - $\text{Category Revenue Share (\%)} = \left(\frac{\text{Category Revenue}}{\text{Total Bar Revenue}}\right) \times 100$
  - $\text{Category Unit Share (\%)} = \left(\frac{\text{Category Units Sold}}{\text{Total Bar Units Sold}}\right) \times 100$

#### Team-Selected KPIs (`A7`, `US4`)

- **FR-015**: For the team-selected hotel KPI (`A7`), the system MUST calculate **Average Length of Stay (ALOS)** ($\frac{\sum \text{Days Rented}}{\text{Booking Count}}$), **Average Daily Rate (ADR)** ($\frac{\sum \text{Price}}{\sum \text{Days Rented}}$), and **Average Revenue per Booking** ($\frac{\sum \text{Price}}{\text{Booking Count}}$) overall, per `Room Type`, and per `Season`.
- **FR-016**: For the lobby bar price-tier and popularity analysis (`US4` / `A7`), the system MUST rank drinks by `Units Sold` and classify drinks into price tiers so the Hotel CFO can compare demand for lower-priced versus higher-priced items.

#### Tableau Integration Boundary

- **FR-017**: The system's deliverable for the analytics dashboard MUST be limited to the REST/JSON API and its OpenAPI contract, which together expose every record and KPI the dashboard needs (`A1`–`A7`, `B1`–`B3`, `K1`–`K3`). The repository MUST NOT contain or generate Tableau files (e.g. `.twb`, `.twbx`, `.tbm`, `.tds`, `.tdsx`, `.hyper`) or Tableau-specific connector code such as a Web Data Connector. The team builds the Tableau dashboard manually against the API.

### Key Entities *(include if feature involves data)*

- **RoomType**: Represents one of Hotel Kong Arthur's 8 room categories (`Standard Single`, `Grand Lit`, `Standard Double`, `Superior Double`, `Junior Suite`, `Spa Executive`, `Suite`, `LOFT Suite`). Key attributes: room type name, standard seasonal nightly price ranges (`low`, `mid`, `high` in DKK), guest capacity per room (`1–4` persons), and allocated room count out of the hotel's `214` total rooms.
- **Booking**: Represents a guest reservation at Hotel Kong Arthur. Key attributes: unique booking ID, guest first name, guest family name, guest country of origin, room type (referencing `RoomType`), check-in date (`YYYY-MM-DD`), days rented (nights), derived season (`low`, `mid`, `high`) and reporting year, and total booking price in DKK.
- **GuestReview**: Represents a guest satisfaction review stored in a dedicated `reviews` table and exposed via a reviews endpoint. Key attributes: unique review ID, optional booking reference, room type, season (`low`, `mid`, `high`), and satisfaction rating (`1`–`5` integer scale).
- **BarDrinkSale**: Represents a product on Helene Christine's lobby bar menu and its annual sales performance. Key attributes: unique drink ID, drink name, category (`Cocktail` or `Coffee`), unit price in DKK, units sold, and calculated total drink revenue in DKK.
- **KPIReport**: Represents the authoritative business metrics computed by the system's business logic, including total annual hotel revenue, revenue by room type/season/country, top-earning room types and countries, guest country distribution, occupancy rate (`belægningsgrad`), customer satisfaction (`kundetilfredshed`), ALOS/ADR, total annual bar sales, per-drink revenue, and cocktail-vs-coffee percentage split.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A Receptionist can create, edit, or delete a booking through the browser interface in under 30 seconds, with 100% of valid changes persisted and reflected immediately in subsequent system queries.
- **SC-002**: 100% of mandatory analytics views (`A1`–`A7`, `B1`–`B3`, `K1`–`K3`) are backed by REST API endpoints that return live data from the central service interface, with zero direct connections to raw data files or underlying storage, so the team can build every view of the interactive dashboard manually in Tableau without further backend changes.
- **SC-003**: KPI figures displayed on the dashboard (total annual hotel revenue, room-type/season/country revenue, occupancy rate, customer satisfaction, total bar sales, per-drink revenue, and cocktail/coffee percentage split) match the system's authoritative business calculations with 100% numerical accuracy (within `0.01` DKK / `0.01%` rounding tolerance).
- **SC-004**: After a booking is created, updated, or deleted, refreshing the analytics dashboard reflects the updated hotel KPIs within 5 seconds.
- **SC-005**: The complete platform (central data store with empty booking/sales tables, backend service, contract documentation interface, and booking web interface) starts from a fresh checkout using a single `docker compose up` command and becomes ready to serve requests within 60 seconds without manual setup steps, while a separate command seeds the sample inspiration data on demand.

## Assumptions

The following working assumptions and clarified decisions provide concrete, testable rules for areas where the assignment brief (`T1`) left room for interpretation:

- **Live Data Mechanism & Scope**: "Live data" means all runtime data is stored in the central MySQL data store, `docker compose up` starts with an empty operational state (only the 8 room types configured, `0` bookings/sales/reviews), bookings can be created/updated/deleted continuously via the browser UI and REST API (`F1`), and the analytics dashboard fetches current data from the REST API on load/refresh (within 5 seconds) rather than reading static historical files. A separate idempotent seed command loads the sample inspiration dataset (`1,000` bookings, `30` bar drink sales, and synthetic guest reviews) on demand.
- **Season Definition**: Bookings derive their season (`low`, `mid`, `high`) from the month of their `Check-In Date`, matching the baseline dataset and totaling 365 days (`low` = 89 days, `mid` = 153 days, `high` = 123 days):
  - `low` (Lavsæson — winter: January, February, November)
  - `mid` (Mellemsæson — spring and autumn: March, April, May, September, October)
  - `high` (Højsæson — summer and Christmas: June, July, August, December)
- **Occupancy Rate (`belægningsgrad`) Formula**: Because the baseline booking dataset records `Days Rented` per room booking (and does not record guest headcount per booking), occupancy rate (`K1`) is measured in **room-nights**: $\text{Occupancy Rate} = \frac{\sum \text{Days Rented}}{214 \times 365} \times 100$ for the full year, and scaled by season days (`89` / `153` / `123`) and room-type inventory (`27` rooms each for 6 types and `26` rooms each for `Suite` and `LOFT Suite` = `214` rooms) when segmented.
- **Customer Satisfaction (`kundetilfredshed`) Data Source**: Since the historical booking sample dataset does not include a satisfaction column, guest satisfaction ratings (`1`–`5` scale) are stored in a dedicated `reviews` table and exposed via a separate REST endpoint seeded with synthetic guest reviews, keeping the booking form strictly aligned with the CSV booking fields (`K3`).
- **Reporting Year (`A6`, `B1`)**: Every booking requires a `Check-In Date` (`YYYY-MM-DD`). Because the baseline historical CSV records do not contain calendar dates, initial seeding generates deterministic `2026` `Check-In Date` values within each row's season months, and both `Season` and reporting year (`2026`) are derived from `Check-In Date` (with bar sales representing reporting year `2026`).
- **Room Type Naming Alignment**: The 8 English room type names in the baseline dataset (`Standard Single`, `Grand Lit`, `Standard Double`, `Superior Double`, `Junior Suite`, `Spa Executive`, `Suite`, `LOFT Suite`) map 1-to-1 to the 8 Danish room type descriptions in the assignment brief (`Standard enkeltværelse`, `Grand lit værelse`, `Standard dobbeltværelse`, `Superior dobbeltværelse`, `Junior suite`, `Spa executive`, `Suite`, `LOFT suite`).
- **Tableau Dashboard Ownership**: For KPI data in Tableau, this repository delivers only the REST API (`FR-017`). The team builds the Tableau dashboard by hand from the API, and no Tableau files (`.twb`, `.twbx`, `.tbm`, etc.) are produced in this repository. Acceptance scenarios and success criteria that describe what the dashboard displays (US2–US5, `SC-003`, `SC-004`) are therefore verified in two parts: automated tests in this repository check the API responses, and the team checks the manually built dashboard against those responses.
- **Authentication**: User authentication and role-based access control are out of scope for this prototype; both the Receptionist browser interface and the CFO dashboard access the service interface directly within the local environment.
