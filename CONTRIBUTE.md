# Contributing to Hotel Kong Arthur Operations & Analytics Platform

This guide describes local development setup, how to run tests, how to reset the database, and the project commit conventions.

## 1. Development Prerequisites

- Docker Desktop / Docker Engine with Compose v2+
- Python 3.13 (optional for running unit tests directly without Docker)

## 2. Running the System

Start the full stack (database, API, frontend, Swagger UI):

```bash
docker compose up --build -d
```

- Frontend: [http://localhost:8080](http://localhost:8080)
- API: [http://localhost:8000](http://localhost:8000)
- Swagger UI: [http://localhost:8081](http://localhost:8081)

## 3. Running Automated Tests

Tests are grouped into four suites: `unit`, `contract`, `integration`, and `architecture`.

Run all test suites inside Docker:

```bash
docker compose run --rm tests
```

Run specific test suites:

```bash
# Unit tests only (fast, no database required)
docker compose run --rm tests pytest tests/unit

# Contract tests (verifies OpenAPI contract sync against hotel_test)
docker compose run --rm tests pytest tests/contract

# Architecture tests (verifies strict 3-layer imports and no Tableau files)
docker compose run --rm tests pytest tests/architecture
```

## 4. Loading Sample Data & Database Reset

- **Seed sample data** (1,000 bookings, 500 reviews, 30 drink sales):
  ```bash
  docker compose run --rm seed
  ```
- **Reset database completely** (wipes volume and restarts empty with fresh schema and reference data):
  ```bash
  docker compose down -v
  docker compose up --build -d
  ```

## 5. Commit Conventions & Governance

- All work is committed to `main` following the project constitution.
- **Rule**: Tests must pass before code is pushed to `main`.
- **Architectural boundaries**:
  - `presentation` calls `business`
  - `business` calls `data` via repository ports (`Protocol`s)
  - `business` must **never** import `presentation`, `data`, `fastapi`, or `pymysql`
  - **No Tableau artifacts** (`.twb`, `.twbx`, `.hyper`, etc.) or connector code may be committed to the repository (FR-017).

