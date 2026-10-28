"""RFC 9457 Problem Details DTOs (contract: `Problem`, `FieldError`)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FieldError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    message: str


class Problem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    title: str
    status: int
    detail: str | None = None
    errors: list[FieldError] | None = None
