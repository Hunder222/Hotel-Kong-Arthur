# Contributing to Hotel Kong Arthur Operations & Analytics Platform

How to set up, run, test and change the system. For what the system is and how it fits together, read
[README.md](README.md). The rules every change must follow are in the
[constitution](.specify/memory/constitution.md).

## 1. Prerequisites

- Docker Desktop or Docker Engine with **Compose v2** (`docker compose version`). Everything the project runs
  (database, API, frontend, Swagger UI, tests) runs in containers.
- Optional: **Python 3.13 or newer**, to run the unit and architecture tests without Docker.
- Free host ports **8080** (frontend), **8000** (API) and **8081** (Swagger UI).

## 2. Run the system

```bash
docker compose up --build -d      # db, api, frontend, swagger-ui
docker compose ps                 # db, api, frontend should be "healthy"
docker compose run --rm seed      # optional: load the sample data
docker compose logs -f api        # follow the API logs
docker compose down               # stop (keeps the data)
```

| What | URL |
|------|-----|
| Booking page | http://localhost:8080 |
| REST API | http://localhost:8000/api/v1/ |
| Swagger UI | http://localhost:8081 |

After code changes in `backend/` or `frontend/`, run `docker compose up --build -d` again (the images contain the
code). The `tests` service mounts the repository, so it always runs your current files without a rebuild.

## 3. Run the tests

Four suites, selected by folder (each module is also marked `unit`, `contract`, `integration` or `architecture`):

| Suite | What it checks | Needs MySQL |
|-------|----------------|-------------|
| `tests/unit` | every business rule and KPI formula, with fake repositories | no |
| `tests/architecture` | the three-layer import rules; no Tableau files or connector code in the repository (FR-017) | no |
| `tests/contract` | every API operation against `openapi.yaml` (status, content type, headers, body); the contract is valid OpenAPI 3.0.3; implemented routes equal the contract's 19 operations | yes |
| `tests/integration` | repositories, the booking use cases, the seed command, and the golden KPI values from the sample data | yes |

In Docker (works everywhere, and is what must pass before you push):

```bash
docker compose run --rm tests                        # all four suites
docker compose run --rm tests pytest tests/unit      # one suite
docker compose run --rm tests pytest tests/contract -k bookings -x    # any pytest arguments
```

The tests use a separate **`hotel_test`** database, rebuilt from `db/init/*.sql` at the start of a run and emptied
between tests. The `hotel` database that the running system uses is never touched.

Without Docker, the two suites that need no database:

```bash
cd backend
python3.13 -m venv .venv && source .venv/bin/activate
pip install ".[dev]"
pytest tests/unit tests/architecture
```

The contract and integration suites need MySQL, whose port is deliberately not published, so run them in Docker.

## 4. Where to change what

- **A business rule or KPI** goes in `backend/src/hotel_api/business/` (`rules/` or `kpis/`) as a pure function, with
  a unit test. It is defined **once**: neither routers, SQL, the frontend nor Tableau may repeat it.
- **An endpoint** touches all of: the router and DTO (`presentation/`), the service (`business/services/`), the
  contract (`specs/001-hotel-analytics-platform/contracts/openapi.yaml`), and a contract test. The contract and the
  code must agree; the contract tests and the route-parity test fail when they do not.
- **SQL** lives only in `backend/src/hotel_api/data/repositories/`.
- **A new service** is wired in `backend/src/hotel_api/main.py` (the composition root) and declared as a provider in
  `presentation/api/dependencies.py`.
- **The layer rules** (checked by `tests/architecture`): `presentation` may import `business` but never `data`;
  `business` never imports `presentation`, `data`, `fastapi`, `starlette` or `pymysql`; `data` never imports
  `presentation` or `business.services`.
- A contract change must be checked against all three consumers: the web frontend, Tableau and the hotel's booking
  system. Adding an optional field or an endpoint is non-breaking. Removing or renaming a field, or changing its
  type or meaning, is breaking and needs a new `/api/v2` path and team agreement.

## 5. Database and sample data

- **Schema and reference data** are in `db/init/` (`01_schema.sql`, `02_reference_data.sql`,
  `03_test_database.sql`). MySQL runs them only on an **empty** volume. To apply a change:

  ```bash
  docker compose down -v           # deletes the volume, and with it ALL data
  docker compose up --build -d
  docker compose run --rm seed     # reload the sample data if you want it
  ```

- **Sample data**: `docker compose run --rm seed` replaces all bookings, reviews and bar sales with the sample set in
  one transaction. It is idempotent and removes anything created through the API.
- **Persistence**: data lives in the named volume `mysql-data`. `down` keeps it, `down -v` deletes it.
- Connect to the database for debugging (its port is not published):
  `docker compose exec db mysql -uhotel -photel hotel`.

## 6. Working with Spec Kit

The system is built spec-driven: Constitution → Specify → Clarify → Plan → Tasks → Implement → Converge. The artefacts
are in `specs/001-hotel-analytics-platform/`. Code that disagrees with the spec is wrong until the spec is amended.

- Pick tasks from `tasks.md`; tick a task `[X]` only when its code **and** its tests exist and pass.
- Implement one task at a time with the code agent (`/speckit-implement T0xx`), and review the whole change yourself
  before committing: every member must be able to explain any part of the system, including AI-written parts.
- Changing a requirement means amending `spec.md` first. Changing a principle means `/speckit-constitution`
  (committed to `main` with the version bump and the reason in the commit message).

## 7. Commits and review

- Work is committed **directly to `main`**; pull requests are not required.
- Before each commit: review the agent's whole diff, and run `docker compose run --rm tests`. A change to a
  Dockerfile, `docker-compose.yml` or the database schema must also be checked with a clean
  `docker compose down -v && docker compose up --build -d`.
- Reference the task ID in the commit message when the commit implements a task, for example
  `T061: hotel KPI endpoints`.
- Every member authors commits to the source code. Code written by an agent is committed by the member who ran and
  reviewed it. Use one consistent Git identity (`git config user.name` and `user.email`) so contributions can be
  attributed.
- The team reviews recent commits on `main` together at check-ins.

## 8. Definition of done for a user story

- Every acceptance criterion is met.
- The story's unit and contract tests pass, and `docker compose run --rm tests` is green.
- The OpenAPI contract matches the implementation, and Swagger UI shows it.
- The system starts from a fresh clone with `docker compose up`.
- `README.md` and this file are updated if the story changed them.
- Every member can explain the change.

## 9. Out of scope

- **No Tableau files or connector code** (`.twb`, `.twbx`, `.tbm`, `.tds`, `.tdsx`, `.hyper`) may be committed. The
  Tableau dashboard is built by hand by the team from the REST API (FR-017). The architecture tests fail if one
  appears.
- Authentication and role-based access control are out of scope for this prototype.

## 10. Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| `api` never becomes healthy | `db` is not healthy yet (first start initialises the schema, about 20 seconds). Check `docker compose logs db` |
| A change to `db/init/*.sql` has no effect | The scripts only run on an empty volume: `docker compose down -v`, then `up --build -d` |
| Port already in use | Stop the other process, or change the host port in `docker-compose.yml` |
| Contract tests fail after you edited the code | The code and `openapi.yaml` disagree: fix whichever is wrong, they must match exactly |
