"""Shared test harness (T034, research R16).

- `client`: FastAPI TestClient bound to the separate `hotel_test` database, whose schema is rebuilt
  from `db/init/*.sql` once per session and whose operational tables are emptied before each test.
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
from pymysql.connections import Connection

from hotel_api.config import Settings, get_settings
from hotel_api.data.connection import open_connection
from hotel_api.main import create_app

# /repo/backend/tests/conftest.py -> /repo (also inside the tests container, which mounts the repo at /repo)
REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "specs" / "001-hotel-analytics-platform" / "contracts" / "openapi.yaml"
INIT_DIR = REPO_ROOT / "db" / "init"
TEST_DATABASE = "hotel_test"
CONTRACT_HOST = "http://localhost:8000"

_TABLES_DEPENDENT_FIRST = (
    "reviews",
    "bookings",
    "bar_drink_sales",
    "room_type_rates",
    "room_types",
)
_OPERATIONAL_TABLES = ("reviews", "bookings", "bar_drink_sales")


def _run_sql_file(conn: Connection[Any], path: Path) -> None:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if not line.strip().startswith("--")]
    statements = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]
    with conn.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)
    conn.commit()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return get_settings().with_db_name(TEST_DATABASE)


@pytest.fixture(scope="session")
def hotel_test_schema(test_settings: Settings) -> None:
    """Rebuild schema and reference data in `hotel_test` from db/init (never touches `hotel`)."""
    conn = open_connection(test_settings)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table in _TABLES_DEPENDENT_FIRST:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
        _run_sql_file(conn, INIT_DIR / "01_schema.sql")
        _run_sql_file(conn, INIT_DIR / "02_reference_data.sql")
    finally:
        conn.close()


@pytest.fixture()
def clean_db(test_settings: Settings, hotel_test_schema: None) -> Iterator[Connection[Any]]:
    """A connection to `hotel_test` with empty operational tables; also emptied afterwards."""
    conn = open_connection(test_settings)

    def empty() -> None:
        with conn.cursor() as cursor:
            for table in _OPERATIONAL_TABLES:
                cursor.execute(f"DELETE FROM {table}")
        conn.commit()

    empty()
    try:
        yield conn
    finally:
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
