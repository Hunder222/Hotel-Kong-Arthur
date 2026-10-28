"""DTO for `GET /api/v1/health` (contract: `Health`)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class Health(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = "ok"
    database: Literal["ok"] = "ok"
