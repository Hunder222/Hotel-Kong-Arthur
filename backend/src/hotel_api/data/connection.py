"""PyMySQL connection factory and transaction helper for the data layer (T020, R2).

Each HTTP request or CLI run opens one connection with `utf8mb4`, `autocommit=False`, and
`DictCursor`. Driver errors are translated into `StorageUnavailable` so upper layers never
depend on PyMySQL exceptions.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor

from hotel_api.business.errors import BusinessError, StorageUnavailable
from hotel_api.config import Settings, get_settings


def open_connection(settings: Settings | None = None) -> Connection[DictCursor]:
    """Open a single PyMySQL connection configured with `utf8mb4`, `autocommit=False`, and `DictCursor`."""
    cfg = settings or get_settings()
    try:
        return pymysql.connect(
            host=cfg.db_host,
            port=cfg.db_port,
            user=cfg.db_user,
            password=cfg.db_password,
            database=cfg.db_name,
            charset="utf8mb4",
            autocommit=False,
            cursorclass=DictCursor,
        )
    except (pymysql.MySQLError, OSError) as exc:
        raise StorageUnavailable() from exc


create_connection = open_connection


@contextmanager
def db_cursor(conn: Connection[Any]) -> Iterator[DictCursor]:
    """Yield a `DictCursor` from `conn`, translating any `pymysql.MySQLError` into `StorageUnavailable`."""
    try:
        with conn.cursor(DictCursor) as cursor:
            yield cursor
    except BusinessError:
        raise
    except (pymysql.MySQLError, OSError) as exc:
        raise StorageUnavailable() from exc


@contextmanager
def connection_scope(settings: Settings | None = None) -> Iterator[Connection[DictCursor]]:
    """Open one connection for a request or CLI run; commit on success, rollback on error, then close."""
    conn = open_connection(settings)
    try:
        yield conn
        conn.commit()
    except BusinessError:
        try:
            conn.rollback()
        except (pymysql.MySQLError, OSError):
            pass
        raise
    except (pymysql.MySQLError, OSError) as exc:
        try:
            conn.rollback()
        except (pymysql.MySQLError, OSError):
            pass
        raise StorageUnavailable() from exc
    except Exception:
        try:
            conn.rollback()
        except (pymysql.MySQLError, OSError):
            pass
        raise
    finally:
        try:
            conn.close()
        except (pymysql.MySQLError, OSError):
            pass

