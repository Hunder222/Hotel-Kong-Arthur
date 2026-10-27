<!--
Sync Impact Report (temporary review aid; delete this comment before committing)
- Version change: unversioned template → 1.0.0 (initial ratification)
- Bump rationale: first concrete constitution; every template placeholder replaced
- Principles (template slot → new title):
  - PRINCIPLE_1 → I. Spec-Driven Development with GitHub Spec Kit
  - PRINCIPLE_2 → II. User Stories with Acceptance Criteria
  - PRINCIPLE_3 → III. Three-Layer Backend
  - PRINCIPLE_4 → IV. The REST/JSON API Is the Only Way In
  - PRINCIPLE_5 → V. The OpenAPI Contract Matches the Code
  - added       → VI. MySQL Holds the Data, and the Data Is Live
  - added       → VII. KPIs Are Business Logic
  - added       → VIII. One Command: docker-compose up
  - added       → IX. Tested Business Rules and API Contract
  - added       → X. Human Ownership and Visible Contribution
- Sections: SECTION_2 → Mandatory Scope & Deliverables; SECTION_3 → Development Workflow &
  Quality Gates; added: source key (preamble) and Open Questions (at the end, as requested)
- Removed sections: none
- Dependent templates: not modified (command scope guard)
  - plan-template.md: Constitution Check is derived from this file at runtime; gates I–X apply
  - tasks-template.md: tasks MUST now include unit and contract tests (Principle IX)
- Deferred placeholders: none. Open Questions OQ-1 to OQ-5 and the Clarify list need answers.
-->
# Hotel Kong Arthur Constitution

This constitution governs every spec, plan, task and line of code in this repository. The system
analyses and presents operational data from Hotel Kong Arthur to decision makers
(T1 › Systemkrav › Formål). Teacher requirements are binding; team agreements apply wherever they
do not conflict with them (TM › Planen: "Vi skal overholde alle krav beskrevet i filerne i
context/teacher/"). MUST, SHOULD and MAY are used as in RFC 2119.

Every rule cites its source with the IDs below, followed by the section headings of that file:

| ID | Source | Status |
|----|--------|--------|
| T1 | `context/teacher/tværfaglig_opgave_hotel_kong_arthur.md` (assignment) | Binding |
| T2 | `context/teacher/tillægsspørgsmål_swa.md` (SWA questions for the presentation) | Binding |
| T3 | `context/teacher/*.csv` (sample data from the hotel's current systems) | Sample data; T1 calls it inspiration |
| TM | `context/team/project-plan.md` (team plan) | Team agreement |
| TD | Team decisions given in the constitution session on 2026-10-27: conflict rule, commit flow, amendments, testing, language. Not yet written in `context/team/` | Team agreement |

Each principle ends with its sources and whom it binds (teacher or team). Governance explains what
that means for waivers and amendments.

## Core Principles

### I. Spec-Driven Development with GitHub Spec Kit

- The system MUST be built with GitHub Spec Kit in this order: Constitution → Specify → Clarify →
  Plan → Tasks → Implement → Converge.
- Application code for a feature MUST NOT be written before its `spec.md`, `plan.md` and
  `tasks.md` exist. The spec says *what* (functions, users, requirements, success criteria); the
  plan says *how* (language, architecture, main components, data model).
- The spec is what the team steers the AI with and what the result is judged against. Where code
  and spec disagree, the code is treated as wrong until the spec is amended.
- Clarify MUST settle, before Plan, at least: what "live" means, how a season is defined and how
  occupancy rate (belægningsgrad) is calculated.
- Implement → Converge MUST repeat until the code matches spec, plan and tasks. Every gap found in
  Converge becomes a new task.

**Rationale:** This is the required working method, and the spec is the yardstick the result is
assessed against.

**Sources:** T1 › Krav: Systemudvikling › Workflowet · TM › Krav Systemudvikling ·
**Binding:** teacher

### II. User Stories with Acceptance Criteria

- Every user story MUST use the teacher's format: `Som <rolle> ønsker jeg <mål>, så <fordel>`.
- Every story MUST meet INVEST (Independent, Negotiable, Valuable, Estimable, Small, Testable).
- Every story MUST have acceptance criteria (the *Confirmation* of "The Three Cs"). Converge uses
  them to decide whether the story is done.
- Primary roles: the **Receptionist** creates, edits and deletes bookings in the web frontend; the
  **Hotel CFO** uses the Tableau dashboard. The spec MAY add a role when a requirement needs one.
- The team's stories US1–US4 are the starting backlog and MUST be refined to meet this principle
  (see OQ-2 and OQ-3).

**Rationale:** Acceptance criteria are what Converge checks; without them "done" is a matter of
opinion.

**Sources:** T1 › Krav: Systemudvikling › User Stories · TM › Overordnet arkitektur (Brugere),
User stories · **Binding:** teacher (format, INVEST, criteria); team (roles, backlog)

### III. Three-Layer Backend

The backend MUST have exactly three layers, each in its own package or module so the boundaries
can be pointed to in the code:

1. **Presentation**: REST endpoints and DTOs (input validation, JSON serialisation). No business
   rules and no SQL.
2. **Business**: services/use cases (KPI calculation, seasonal pricing, booking validation) and
   domain models (Booking, Room, Sale). No HTTP and no SQL.
3. **Data**: repositories with SQL queries, mapping between rows and domain models, and database
   connections. The only layer that talks to MySQL.

- Calls go one way: presentation → business → data. A layer MUST NOT call the layer above it or
  skip the layer below it.
- Replacing MySQL MUST require changes only in the data layer and the deployment configuration.
  Replacing the web frontend with the hotel's own booking system MUST NOT require changes in the
  business or data layer.
- Every plan MUST state which layer each new component belongs to.

**Rationale:** Required architecture. Q3 asks where the layer boundaries are in the code and for a
deliberate placement choice; Q5 asks what a database or frontend swap would touch.

**Sources:** T1 › Systemkrav › Teknologistak; Krav: Softwarearkitektur · T2 › Q3, Q5 ·
TM › Overordnet arkitektur · **Binding:** teacher (three layers); team (what each layer contains)

### IV. The REST/JSON API Is the Only Way In

- The presentation layer MUST expose a REST API with JSON request and response bodies.
- Every client (the browser frontend, the Tableau dashboard and the hotel's existing booking
  system) MUST read and change data only through this API. Clients MUST NOT connect to MySQL.
- Creating, updating and deleting bookings MUST be possible through POST, PUT and DELETE
  endpoints that any client can call, not only the web frontend.
- Resources MUST mirror the domain (e.g. bookings, rooms, bar sales, KPIs), and HTTP methods and
  status codes MUST follow HTTP semantics. The plan MUST explain the URL structure, methods and
  status codes of at least one endpoint as a worked example.

**Rationale:** The dashboard must be built "med udgangspunkt i backendens REST API", and the
hotel's booking system will write to the same API. Q6 asks the team to defend its REST design on a
concrete endpoint.

**Sources:** T1 › Systemkrav › Teknologistak; Krav: Forretningsdesign og Analytics; Krav:
Softwarearkitektur · T2 › Q6, Q9 · TM › Overordnet arkitektur · **Binding:** teacher

### V. The OpenAPI Contract Matches the Code

- The API contract MUST be delivered as an OpenAPI document in the repository. Team choice:
  OpenAPI 3.0.
- Swagger UI MUST serve that contract from a Docker container started by `docker-compose up`.
- Contract and code MUST NOT drift: every implemented endpoint is in the contract, every contract
  endpoint is implemented, and request and response schemas match. The plan MUST name the
  mechanism that keeps them in sync; the contract tests in Principle IX verify it.
- A contract change MUST be checked against all three consumers: the web frontend, Tableau and the
  hotel's booking system.
- If the chosen framework generates OpenAPI 3.1 (FastAPI does by default), the plan MUST record
  whether 3.0 or 3.1 is authoritative.

**Rationale:** The contract is a deliverable, and Q7 asks who its consumers are and how the team
knows the contract and the code agree.

**Sources:** T1 › Systemkrav › Teknologistak; Krav: Softwarearkitektur (incl. Hvad skal
afleveres) · T2 › Q7 · TM › Overordnet arkitektur · **Binding:** teacher; team (version 3.0)

### VI. MySQL Holds the Data, and the Data Is Live

- The database MUST be MySQL. All runtime data (bookings, rooms, bar sales and everything a KPI is
  calculated from) MUST be stored there.
- The CSV files are static, historical samples. They MAY seed the database and inspire the data
  model, but clients MUST NOT read them at runtime and the dashboard MUST NOT be built on them.
- The system MUST accept continuous updates at runtime, at minimum creating, updating and deleting
  bookings through the API. The dashboard MUST show the current state of the database through the
  API, not a historical snapshot.
- The meaning of "live" (mechanism and acceptable delay) MUST be settled in Clarify. The plan MUST
  describe how Tableau gets current data through the REST API.
- The schema and any seed data MUST be created automatically by `docker-compose up`.
- What happens to the data when the containers stop MUST be a deliberate choice, documented in
  `README.md`.

**Rationale:** The brief explicitly moves the system from static CSV files to live data (Q9), and
Q8 asks what happens to the data when the containers shut down.

**Sources:** T1 › Systemkrav; Datagrundlag; Krav: Softwarearkitektur; Krav: Systemudvikling ›
Workflowet (Clarify) · T2 › Q8, Q9 · T3 · TM › Overordnet arkitektur · **Binding:** teacher

### VII. KPIs Are Business Logic

- KPI formulas and business rules MUST live in the business layer and be exposed through the API.
  This covers occupancy rate (belægningsgrad), revenue (indtjening), customer satisfaction
  (kundetilfredshed), every figure in *Mandatory Scope*, seasonal pricing and booking validation.
- Each KPI MUST have exactly one authoritative definition: written in the spec and implemented in
  one place. Tableau MAY filter, group and aggregate API data (sums, counts, shares) for
  interactivity, but MUST NOT re-implement a business rule such as the season mapping, the
  occupancy formula or pricing.
- The plan MUST record why KPIs are calculated in the business layer rather than in MySQL or
  Tableau, and what moving them would cost.
- The hotel facts in T1 are binding inputs to the spec: 214 rooms; 1–4 guests per room and about
  428 guests at most (see the Clarify list); 8 room types with seasonal price ranges; low, mid and
  high season; a lobby bar where Helene Christine makes 20 cocktails and 10 coffee types.

**Rationale:** The team placed KPI calculation in the service layer. One definition per KPI keeps
the API and the dashboard consistent and answers Q4.

**Sources:** T1 › Systemkrav › Beregninger; Data om Hotel Kong Arthur; Krav: Forretningsdesign og
Analytics · T2 › Q4 · TM › Overordnet arkitektur (Service Layer) · **Binding:** teacher (KPIs,
hotel facts); team (placement in the business layer)

### VIII. One Command: `docker-compose up`

- Everything the team builds or runs (MySQL, the backend API, Swagger UI and the browser frontend)
  MUST run in Docker containers defined in one compose file.
- From a fresh clone, one `docker-compose up` (or the Compose V2 form `docker compose up`) MUST
  start the whole system with no other manual step: no manual database import and no hand-made
  config files. Required configuration therefore MUST ship with working development defaults,
  which MUST NOT be real secrets.
- Containers MUST find each other by compose service name, and start-up order MUST be explicit:
  the database is ready before the backend starts (e.g. a healthcheck plus `depends_on`).
- The frontend MUST be served by a container in the compose setup. External hosting such as
  GitHub Pages MUST NOT replace it (see OQ-1).
- Tableau runs outside Docker as an external client of the containerised API (see OQ-5).

**Rationale:** A fixed requirement of the assignment. Q8 asks which containers exist, how they find
each other and how start-up order is handled.

**Sources:** T1 › Systemkrav › Teknologistak; Krav: Softwarearkitektur · T2 › Q8 ·
TM › Overordnet arkitektur (conflict, see OQ-1) · **Binding:** teacher

### IX. Tested Business Rules and API Contract

- Every KPI formula and business rule in the business layer MUST have automated unit tests.
- Every API endpoint MUST have an automated test that checks its status codes and JSON responses
  against the OpenAPI contract.
- Tests MUST pass before code is pushed to `main`, and Converge MUST NOT mark a story done while
  its tests fail. How to run the tests MUST be documented in `CONTRIBUTE.md`.
- Test-first (TDD) is not required. Tests MAY be written in the same task as the code, but the
  task is not done until its tests exist and pass.

**Rationale:** The tests are the team's evidence that the KPIs are calculated correctly (Q4) and
that the contract matches the code (Q7).

**Sources:** TD (testing policy) · T2 › Q4, Q7 · T1 › Krav: Systemudvikling › Workflowet
(Converge) · **Binding:** team

### X. Human Ownership and Visible Contribution

- AI is expected throughout the project. The code agent MUST implement one task at a time, and
  the member running it MUST review the whole change before committing it.
- Every member MUST be able to explain and assess any part of the system, including parts written
  by AI.
- The plan MUST record each architecture decision with its rationale and rejected alternatives: at
  least language and framework, KPI placement, the contract sync mechanism, data persistence and
  the Tableau connection. The record MUST include at least one decision the AI proposed that the
  team changed or deliberately kept, and the biggest weakness of the architecture if it went to
  production.
- The team MUST be able to answer all ten T2 questions from artefacts in the repository.
- Every member MUST author commits to the system's source code. Code written by an agent is
  committed by the member who ran and reviewed it. Each member SHOULD use one consistent Git
  identity so contributions can be attributed.
- The team works in the group formed at the start of the semester.

**Rationale:** Ownership is assessed, and each member's participation is judged from git commits.

**Sources:** T1 › Udvikling af systemet; Grupper; Krav: Systemudvikling › Workflowet (Implement);
Krav: Softwarearkitektur › Hvad skal afleveres · T2 › Q10 and intro · TD (commit flow) ·
**Binding:** teacher; team (commit flow)

## Mandatory Scope & Deliverables

Every item below is a teacher requirement and a Converge checkpoint. "Team coverage" shows which
of the team's user stories (TM › User stories) covers it today.

**Interactive Tableau dashboard built on the REST API** (T1 › Systemkrav › Visualisering; Krav:
Forretningsdesign og Analytics)

| ID | The dashboard shows and calculates | Team coverage |
|----|------------------------------------|---------------|
| A1 | Where the guests come from (countries) | Missing (OQ-2) |
| A2 | Revenue per room type, per season | US2 |
| A3 | Revenue per country | US2 |
| A4 | The room types that earn the most | US2 |
| A5 | The countries that earn the most | US2 |
| A6 | The hotel's revenue for the year | US2 |
| A7 | One interesting KPI chosen by the team | Not chosen (OQ-2); US4 is a candidate |
| B1 | Helene Christine's total bar sales for the year | US3 |
| B2 | Revenue per drink | US3 |
| B3 | Percentage split between cocktails and coffee for Helene Christine | US3 |

**System capabilities** (T1 › Systemkrav › Beregninger; Krav: Softwarearkitektur)

| ID | Requirement | Team coverage |
|----|-------------|---------------|
| K1 | Calculate occupancy rate (belægningsgrad) | Missing (OQ-2) |
| K2 | Calculate revenue (indtjening) | US2 |
| K3 | Calculate customer satisfaction (kundetilfredshed) | Missing, and no data (OQ-2) |
| F1 | Browser frontend that creates, edits and deletes bookings in the backend | US1 |

**Deliverables in the GitHub repository** (T1 › Hvad skal afleveres, in both Systemudvikling and
Softwarearkitektur)

| ID | Deliverable |
|----|-------------|
| D1 | Source code, with commits from every group member |
| D2 | `README.md` with an architecture diagram of the whole system (see OQ-4) |
| D3 | `CONTRIBUTE.md` (exactly this file name) |
| D4 | Swagger UI running in a Docker container |
| D5 | The OpenAPI specification of the API |
| D6 | Spec artefacts: this constitution, plus `spec.md`, `plan.md` and `tasks.md` under `specs/` |
| D7 | User stories with acceptance criteria |
| D8 | The result of the final Converge check: what is implemented and what is missing |

**Presentation** (T1 › Præsentation; T2 › intro): Friday 2026-11-06, in the slot for the group's
number between 12:30 and 15:45. The group presents for 10 minutes, followed by 10 minutes of
questions and feedback, first from the review group and then from Lasse and Claus. The group MUST
also take notes on another group's presentation and then question it and give feedback, and MUST
be ready before entering the room. The T2 questions are the expected basis for the talk and for
Claus's questions.

**Technology stack**

| Concern | Decision | Source |
|---------|----------|--------|
| Backend | Three-layer architecture with a REST API and JSON | T1 |
| API contract | OpenAPI (team: 3.0), Swagger UI in a container | T1, TM |
| Database | MySQL | T1 |
| Runtime | Docker; the whole system starts with `docker-compose up` | T1 |
| Dashboard | Tableau, reading data through the REST API | T1, TM |
| Frontend | Browser UI for bookings, served from a container | T1, TM; see OQ-1 |
| Backend language | Python (the teacher leaves the language free) | TM, T1 |
| Web framework | FastAPI or Flask, chosen in Plan | TM |
| MySQL driver | PyMySQL or mysqlclient, chosen in Plan | TM |

## Development Workflow & Quality Gates

**Phase gates** (T1 › Krav: Systemudvikling › Workflowet; TD)

1. **Specify**: user stories meet Principle II, and the spec names the *Mandatory Scope* items it
   covers.
2. **Clarify**: MUST run before Plan and settle the questions in Principle I and in the Clarify
   list under *Open Questions*.
3. **Plan**: MUST pass the Constitution Check below before research and again after design.
4. **Tasks**: small, concrete tasks grouped by user story with dependencies mapped. They MUST
   include the unit and contract tests required by Principle IX.
5. **Implement**: one task at a time; the member running the agent reviews the whole change.
6. **Converge**: check the code against spec, plan, tasks and acceptance criteria; gaps become new
   tasks; repeat until nothing is missing. The final result is committed (D8).
7. `/speckit-checklist` and `/speckit-analyze` MUST run at least once per feature before
   Implement, to check quality and consistency across spec, plan and tasks.

**Constitution Check**: the plan answers yes to each gate, or records the violation in Complexity
Tracking. Violations of teacher-bound rules are not allowed.

| Gate | Question |
|------|----------|
| I | Is the spec clarified, and do plan and tasks exist before any code? |
| II | Does every story use the teacher's format, meet INVEST and have acceptance criteria? |
| III | Does every component sit in exactly one layer, with calls only going downwards? |
| IV | Do all clients, Tableau included, use only the REST/JSON API? |
| V | Is the OpenAPI contract updated, and is the sync mechanism named? |
| VI | Is all runtime data in MySQL and seeded automatically, with persistence decided? |
| VII | Is each KPI defined once, in the business layer? |
| VIII | Does the whole system start from a fresh clone with `docker-compose up`? |
| IX | Are unit tests for business rules and contract tests for endpoints planned? |
| X | Are architecture decisions recorded with rationale, including one the AI proposed? |

**Commits and review** (TD; T1 › Krav: Systemudvikling › Workflowet (Implement))

- Members commit directly to `main`; pull requests are not required.
- Before each commit the member reviews the agent's whole diff and runs the tests. A change to
  Docker files, the compose file or the database schema MUST also be checked with
  `docker-compose up`.
- The team reviews recent commits on `main` together at team check-ins.
- Commit messages SHOULD reference the task ID (e.g. `T012`) when a commit implements a task.

**Definition of Done for a user story** (T1 › Krav: Systemudvikling › User Stories; Principles V,
VIII, IX and X)

- Every acceptance criterion is met and confirmed in Converge.
- The story's unit and contract tests pass.
- The OpenAPI contract matches the implementation, and Swagger UI shows it.
- The system starts from a fresh clone with `docker-compose up`.
- `README.md`, `CONTRIBUTE.md` and the architecture diagram are updated if the story changed them.
- Every member can explain the change.

## Governance

- **Precedence** (TM › Planen; TD): teacher requirements (T1, T2) come first, then this
  constitution, the team plan (TM), specs, plans and tasks, and finally code. When anything
  conflicts with a teacher requirement, the teacher requirement wins and the conflict is added to
  *Open Questions*; it is never resolved silently.
- **Teacher-bound rules** cannot be waived in a plan's Complexity Tracking or weakened by an
  amendment. Team-bound rules can be changed by amendment.
- **Traceability:** every rule MUST cite its source. Team rules MUST be traceable to a file under
  `context/team/`; the TD decisions MUST be written there before `/speckit-specify` runs for the
  first time.
- **Amendments** (TD): an amendment follows the same flow as code. A member runs
  `/speckit-constitution`, commits the result directly to `main` with the version change and the
  reason in the commit message, and the team reviews it at the next check-in. Closing an Open
  Question is an amendment.
- **Versioning:** semantic versioning. MAJOR: a principle is removed or redefined. MINOR: a
  principle or section is added or materially expanded. PATCH: wording and clarifications.
- **Compliance review:** in every plan's Constitution Check, in every Converge, at team check-ins,
  and once against *Mandatory Scope & Deliverables* before the presentation on 2026-11-06.
- **Language and guidance** (TD): this constitution is written in English; quotations from the
  sources stay in Danish. Day-to-day developer guidance (setup, tests, commit conventions) belongs
  in `CONTRIBUTE.md`.

**Version**: 1.0.0 | **Ratified**: 2026-10-27 | **Last Amended**: 2026-10-27

## Open Questions

For every item below, the teacher requirement is already applied in the principles above. Each
item still needs a decision by the team, or an answer from Lasse or Claus, and is closed by
amendment.

### Conflicts between teacher and team

**OQ-1: Frontend on GitHub Pages vs. "everything in Docker"**

- Team (TM › Overordnet arkitektur): "WebUI køres via browser (og Github Pages)".
- Teacher (T1 › Systemkrav › Teknologistak): "Alt skal køre i Docker-containere"; and
  (T1 › Krav: Softwarearkitektur): "Alt i jeres system skal kunne køres ved hjælp af en enkelt
  `docker-compose up` kommando".
- Applied: the frontend is served from a compose container (Principle VIII).
- To decide: drop GitHub Pages, or keep it only as an extra copy? A Pages copy would also need a
  reachable backend URL and CORS, because the backend runs in Docker on a laptop.

### Gaps where the team plan does not yet cover a teacher requirement

**OQ-2: KPIs missing from the team's user stories**

- T1 requires guest countries (A1), one self-chosen KPI (A7), occupancy rate (K1) and customer
  satisfaction (K3). No story in US1–US4 explicitly covers them; US4 could become A7.
- The T3 CSV files contain no satisfaction data.
- Applied: all four are in *Mandatory Scope*.
- To decide: new or extended stories for A1, A7, K1 and K3, and where satisfaction data comes from
  (e.g. recorded through the API, or generated). Settle in Specify/Clarify, or ask Lasse or Claus.

**OQ-3: The team's user stories do not yet meet Principle II**

- US1–US4 have no acceptance criteria.
- US2 and US3 each bundle several goals (INVEST "Small"); US3 and US4 overlap (INVEST
  "Independent").
- To decide: how to split and refine them in `/speckit-specify`.

**OQ-4: The team's architecture diagram does not show the whole system**

- The TM diagram shows no Docker containers and does not show the hotel's booking system as an
  API client.
- T1 requires a diagram of "jeres samlede system" in `README.md`; T2 › Q1 and Q8 ask about the
  components and containers.
- To decide: extend the diagram before it goes into `README.md` (D2).

### Interpretation of the teacher text used in this constitution

**OQ-5: Tableau cannot run in Docker**

- T1 says "Alt skal køre i Docker-containere" but also requires a Tableau dashboard, which is a
  desktop or cloud application.
- Applied: "everything" means everything the team builds and runs (database, API, Swagger UI,
  frontend); Tableau is an external client of the containerised API (Principle VIII).
- To decide: confirm this reading with Lasse or Claus.

### For `/speckit-clarify` (the teacher assigns these questions to Clarify)

- What does "live" mean: which mechanism, and what delay is acceptable? Must bar sales be live as
  well, or only bookings?
- How is a season defined? T1 gives low = winter, mid = spring and autumn, high = summer and
  Christmas, but no month boundaries.
- Is occupancy measured in rooms or in guests? T1 says 1–4 guests per room, yet about 428 guests
  at most for 214 rooms, which is 2 per room.
- Which year is "the year" in A6 and B1? The T3 CSV files contain no dates.
- Risk for Plan: Tableau's JSON connector reads files, not HTTP endpoints, so prove the route from
  Tableau to the REST API (e.g. a Web Data Connector) early.
