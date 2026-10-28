"""Use case: is the system able to reach its data store?"""

from __future__ import annotations

from hotel_api.business.ports import HealthRepository


class HealthService:
    def __init__(self, health: HealthRepository) -> None:
        self._health = health

    def check(self) -> None:
        """Returns normally if the database answers; raises StorageUnavailable otherwise."""
        self._health.ping()
