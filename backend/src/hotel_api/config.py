"""Application settings loaded from environment variables with development defaults (T019, R3, R11).

No real secrets are stored here; all defaults are for local Docker Compose development.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, replace

DEFAULT_CORS_ORIGINS: tuple[str, ...] = (
    "http://localhost:8080",
    "http://localhost:8081",
)


def _parse_cors_origins(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return DEFAULT_CORS_ORIGINS
    origins = tuple(origin.strip() for origin in raw.split(",") if origin.strip())
    return origins or DEFAULT_CORS_ORIGINS


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the Hotel Kong Arthur API and CLI tools."""

    db_host: str = "db"
    db_port: int = 3306
    db_name: str = "hotel"
    db_user: str = "hotel"
    db_password: str = "hotel"
    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS
    tz: str = "Europe/Copenhagen"

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from environment variables, falling back to development defaults."""
        host = os.environ.get("DB_HOST") or os.environ.get("MYSQL_HOST") or "db"
        port_raw = os.environ.get("DB_PORT") or os.environ.get("MYSQL_PORT") or "3306"
        name = os.environ.get("DB_NAME") or os.environ.get("MYSQL_DATABASE") or "hotel"
        user = os.environ.get("DB_USER") or os.environ.get("MYSQL_USER") or "hotel"
        password = (
            os.environ.get("DB_PASSWORD")
            if "DB_PASSWORD" in os.environ
            else os.environ.get("MYSQL_PASSWORD", "hotel")
        )
        cors_origins = _parse_cors_origins(os.environ.get("CORS_ORIGINS"))
        tz = os.environ.get("TZ") or "Europe/Copenhagen"
        return cls(
            db_host=host,
            db_port=int(port_raw),
            db_name=name,
            db_user=user,
            db_password=password,
            cors_origins=cors_origins,
            tz=tz,
        )

    def with_db_name(self, db_name: str) -> Settings:
        """Return a copy of these settings targeting a different database (e.g. `hotel_test`)."""
        return replace(self, db_name=db_name)


def get_settings() -> Settings:
    """Return settings read from the current environment."""
    return Settings.from_env()

