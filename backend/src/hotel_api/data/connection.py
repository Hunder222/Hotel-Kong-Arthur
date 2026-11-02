"""psycopg connection factory and transaction helper for the data layer (T007, R2).

Each HTTP request or CLI run opens one connection (UTF-8, `autocommit=False`, rows as dicts). Driver errors
about reaching the database are translated into `StorageUnavailable`, so upper layers never depend on
psycopg exceptions.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg import Connection, Cursor
from psycopg.rows import dict_row

from hotel_api.business.errors import BusinessError, StorageUnavailable
from hotel_api.config import Settings, get_settings

# Errors that mean "the database cannot be reached or the connection broke". Constraint violations and
# other SQL errors are programming or data errors and are not hidden behind a 503.
_UNREACHABLE = (psycopg.OperationalError, psycopg.InterfaceError, OSError)

CONNECT_TIMEOUT_SECONDS = 5


def open_connection(settings: Settings | None = None) -> Connection[dict[str, Any]]:
    """Open one psycopg connection: UTF-8, `autocommit=False`, `dict_row` rows."""
    cfg = settings or get_settings()
    try:
        return psycopg.connect(
            host=cfg.db_host,
            port=cfg.db_port,
            dbname=cfg.db_name,
            user=cfg.db_user,
            password=cfg.db_password,
            autocommit=False,
            row_factory=dict_row,
            client_encoding="UTF8",
            connect_timeout=CONNECT_TIMEOUT_SECONDS,
        )
    except (psycopg.Error, OSError) as exc:
        raise StorageUnavailable() from exc


create_connection = open_connection


@contextmanager
def db_cursor(conn: Connection[Any]) -> Iterator[Cursor[dict[str, Any]]]:
    """Yield a cursor from `conn`, translating "database unreachable" driver errors into `StorageUnavailable`."""
    try:
        with conn.cursor() as cursor:
            yield cursor
    except BusinessError:
        raise
    except _UNREACHABLE as exc:
        raise StorageUnavailable() from exc


def _rollback(conn: Connection[Any]) -> None:
    try:
        conn.rollback()
    except (psycopg.Error, OSError):
        pass


@contextmanager
def connection_scope(settings: Settings | None = None) -> Iterator[Connection[dict[str, Any]]]:
    """Open one connection for a request or CLI run; commit on success, rollback on error, then close."""
    conn = open_connection(settings)
    try:
        yield conn
        conn.commit()
    except BusinessError:
        _rollback(conn)
        raise
    except _UNREACHABLE as exc:
        _rollback(conn)
        raise StorageUnavailable() from exc
    except Exception:
        _rollback(conn)
        raise
    finally:
        try:
            conn.close()
        except (psycopg.Error, OSError):
            pass
