"""`GET /api/v1/health`."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from hotel_api.business.services.health_service import HealthService
from hotel_api.presentation.api.dependencies import get_health_service
from hotel_api.presentation.api.schemas.health import Health

router = APIRouter(prefix="/api/v1", tags=["Health"])


@router.get("/health", response_model=Health, operation_id="getHealth")
def get_health(service: HealthService = Depends(get_health_service)) -> Health:
    service.check()
    return Health()
