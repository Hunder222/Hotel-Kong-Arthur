# Contributing to Hotel Kong Arthur Operations & Analytics Platform

How to set up, run, test and change the system. For what the system is and how it fits together, read
[README.md](README.md). The rules every change must follow are in the
[constitution](.specify/memory/constitution.md).

## 1. Prerequisites

- Docker Desktop or Docker Engine with **Compose v2** (`docker compose version` or `docker-compose version`). Everything the project runs
  (database, API, frontend, Swagger UI, tests) runs in containers.
- Optional: **Python 3.13 or newer**, to run the unit and architecture tests without Docker.
- Free host ports **8080** (frontend), **8000** (API) and **8081** (Swagger UI).

## 2. Run the system

```bash
docker compose up --build -d      # db (PostgreSQL 17), api, frontend, swagger-ui
docker compose ps                 # db, api, frontend should be "healthy"
docker compose run --rm seed      # optional: load the sample data (1,000 bookings, 500 reviews, 30 drink sales)
docker compose logs -f api        # follow the API logs
docker compose down               # stop (keeps the data)
```

| What | URL |
|------|-----|
| Booking page & Analytics | http://localhost:8080 |
| REST API | http://localhost:8000/api/v1/ |
| Swagger UI | http://localhost:8081 |

After code changes in `backend/` or `frontend/`, run `docker compose up --build -d` again (the images contain the
code). The `tests` service mounts the repository, so it always runs your current files without a rebuild.

## 3. Run the tests

Four suites, selected by folder (each module is also marked `unit`, `contract`, `integration` or `architecture`):

| Suite | What it checks | Needs PostgreSQL |
|-------|----------------|------------------|
| `tests/unit` | every business rule and KPI formula, with fake repositories | no |
| `tests/architecture` | the three-layer import rules; no Tableau files or connector code in the repository (FR-017); frontend price preview mirror | no |
| `tests/contract` | every API operation against `openapi.yaml` (status, content type, headers, body); the contract is valid OpenAPI 3.0.3; implemented routes equal the contract's 20 operations | yes |
| `tests/integration` | repositories, the booking use cases, seed idempotence, all-time queries, and the golden KPI values from the sample data | yes |

In Docker (works everywhere, and is what must pass before you push):

```bash
docker compose run --rm tests                        # all four suites
docker compose run --rm tests pytest tests/unit      # one suite
docker compose run --rm tests pytest tests/contract -k bookings -x    # any pytest arguments
```

The tests use a separate **`hotel_test`** database, created in `db/init/03_test_database.sql` at the start of a run and emptied
between tests. The `hotel` database that the running system uses is never touched.

Without Docker, the two suites that need no database:

```bash
cd backend
python3.13 -m venv .venv && source .venv/bin/activate
pip install ".[dev]"
pytest tests/unit tests/architecture
```

The contract and integration suites need PostgreSQL, whose port is deliberately not published, so run them in Docker.

## 4. Where to change what

- **A business rule or KPI** goes in `backend/src/hotel_api/business/` (`rules/` or `kpis/`) as a pure function, with
  a unit test. It is defined **once**: neither routers, SQL, the frontend nor Tableau may repeat it.
- **An endpoint** touches all of: the router and DTO (`presentation/`), the service (`business/services/`), the
  contract (`specs/001-hotel-analytics-platform/contracts/openapi.yaml`), and a contract test. The contract and the
  code must agree; the contract tests and the route-parity test fail when they do not.
- **SQL** lives only in `backend/src/hotel_api/data/repositories/` using parameterized PostgreSQL queries (`psycopg`).
- **A new service** is wired in `backend/src/hotel_api/main.py` (the composition root) and declared as a provider in
  `presentation/api/dependencies.py`.
- **The layer rules** (checked by `tests/architecture`): `presentation` may import `business` but never `data`;
  `business` never imports `presentation`, `data`, `fastapi`, `starlette` or `psycopg`; `data` never imports
  `presentation` or `business.services`.
- A contract change must be checked against all consumers: the web frontend, direct API analytics consumers, Tableau, and the hotel's booking system.

## 5. Database and sample data

- **Schema and reference data** are in `db/init/` (`01_schema.sql`, `02_reference_data.sql`,
  `03_test_database.sql`). PostgreSQL executes them only on an **empty** volume. To apply a change:

  ```bash
  docker compose down -v           # deletes the volume, and with it ALL data
  docker compose up --build -d
  docker compose run --rm seed     # reload the sample data
  ```

- **Sample data**: `docker compose run --rm seed` replaces all bookings, reviews and bar sales with the sample set in
  one transaction. It is idempotent and removes anything created through the API.
- **Persistence**: data lives in the named volume `postgres-data`. `down` keeps it, `down -v` deletes it.
- Connect to PostgreSQL for debugging (port is not published):
  `docker compose exec db psql -U hotel -d hotel`.

## 6. Working with Spec Kit

All features follow the Spec Kit process located in `.specify/` and `specs/`. Check `tasks.md` for current progress and execute implementations phase-by-phase.
