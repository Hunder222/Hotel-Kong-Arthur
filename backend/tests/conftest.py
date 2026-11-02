"""Shared test harness (T034, research R16).

- `client`: FastAPI TestClient bound to the separate PostgreSQL `hotel_test` database, whose schema and
  reference data are rebuilt from `db/init/01_schema.sql` and `02_reference_data.sql` once per session, and
  whose operational tables are truncated (identity sequences restarted) before each test.
- `contract`: openapi-core loader for the one authoritative contract, plus `check_contract` to
  validate a response (status, content type, headers, body) against it.

Unit and architecture tests need none of this and never touch the database.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl

import pytest
from fastapi.testclient import TestClient
from openapi_core import Config, OpenAPI
from openapi_core.testing import MockRequest, MockResponse
import psycopg
from psycopg import Connection

from hotel_api.business.errors import StorageUnavailable
from hotel_api.config import Settings, get_settings
from hotel_api.data.connection import open_connection
from hotel_api.main import create_app

# /repo/backend/tests/conftest.py -> /repo (also inside the tests container, which mounts the repo at /repo)
REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "specs" / "001-hotel-analytics-platform" / "contracts" / "openapi.yaml"
INIT_DIR = REPO_ROOT / "db" / "init"
TEST_DATABASE = "hotel_test"
CONTRACT_HOST = "http://localhost:8000"

_OPERATIONAL_TABLES = ("reviews", "bookings", "bar_drink_sales")
# 03_test_database.sql creates hotel_test itself, so only the schema and reference data are replayed in it.
_SCHEMA_SCRIPTS = ("01_schema.sql", "02_reference_data.sql")


def _run_sql_file(conn: Connection[Any], path: Path) -> None:
    """Run a whole SQL script (several statements, no parameters) in one go."""
    with conn.cursor() as cursor:
        cursor.execute(path.read_text(encoding="utf-8"))
    conn.commit()


def _ensure_test_database(settings: Settings) -> None:
    """Create `hotel_test` if the compose init script has not (an older volume, or a manual setup)."""
    try:
        open_connection(settings).close()
        return
    except StorageUnavailable:
        pass
    admin = psycopg.connect(
        host=settings.db_host, port=settings.db_port, dbname="postgres",
        user=settings.db_user, password=settings.db_password, autocommit=True, connect_timeout=5,
    )
    try:
        with admin.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.db_name,))
            if cursor.fetchone() is None:
                cursor.execute(f'CREATE DATABASE "{settings.db_name}" WITH ENCODING \'UTF8\'')
    finally:
        admin.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return get_settings().with_db_name(TEST_DATABASE)


@pytest.fixture(scope="session")
def hotel_test_schema(test_settings: Settings) -> None:
    """Rebuild schema and reference data in `hotel_test` from db/init (never touches `hotel`)."""
    _ensure_test_database(test_settings)
    conn = open_connection(test_settings)
    try:
        with conn.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS reviews, bookings, bar_drink_sales, room_type_rates, room_types CASCADE")
        conn.commit()
        for script in _SCHEMA_SCRIPTS:
            _run_sql_file(conn, INIT_DIR / script)
    finally:
        conn.close()


@pytest.fixture()
def clean_db(test_settings: Settings, hotel_test_schema: None) -> Iterator[Connection[Any]]:
    """A connection to `hotel_test` with empty operational tables and restarted ids; emptied afterwards too."""
    conn = open_connection(test_settings)

    def empty() -> None:
        with conn.cursor() as cursor:
            cursor.execute(f"TRUNCATE {', '.join(_OPERATIONAL_TABLES)} RESTART IDENTITY")
        conn.commit()

    empty()
    try:
        yield conn
    finally:
        conn.rollback()
        empty()
        conn.close()


@pytest.fixture()
def client(test_settings: Settings, clean_db: Connection[Any]) -> TestClient:
    app = create_app(test_settings)
    # raise_server_exceptions=False: an unexpected error must come back as a 500 Problem, as in production.
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="session")
def contract() -> OpenAPI:
    # openapi-core only knows application/json by default; the contract's errors are problem+json.
    config = Config(extra_media_type_deserializers={"application/problem+json": json.loads})
    return OpenAPI.from_file_path(str(CONTRACT_PATH), config=config)


@pytest.fixture(scope="session")
def check_contract(contract: OpenAPI) -> Callable[[Any], None]:
    """Validate an `httpx.Response` (status, content type, headers, body) against openapi.yaml.

    Raises an openapi-core error when the response, or its request, does not match the contract.
    """

    def check(response: Any) -> None:
        request = response.request
        body = request.content or None
        content_type = request.headers.get("content-type", "application/json")
        mock_request = MockRequest(
            CONTRACT_HOST,
            request.method,
            request.url.path,
            args=dict(parse_qsl(request.url.query.decode())),
            data=body,
            content_type=content_type,
        )
        mock_response = MockResponse(
            response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            content_type=response.headers.get("content-type", "application/json").split(";")[0],
        )
        contract.validate_response(mock_request, mock_response)

    return check
