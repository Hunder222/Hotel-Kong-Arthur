"""Data layer repositories implementing the business layer's repository Protocols."""

from hotel_api.data.repositories.bar_sales import BarSalesRepo, PostgresBarSalesRepository
from hotel_api.data.repositories.bookings import BookingRepo, PostgresBookingRepository
from hotel_api.data.repositories.health import HealthRepo, PostgresHealthRepository
from hotel_api.data.repositories.reviews import PostgresReviewRepository, ReviewRepo
from hotel_api.data.repositories.room_types import PostgresRoomTypeRepository, RoomTypeRepo

__all__ = [
    "BarSalesRepo",
    "BookingRepo",
    "HealthRepo",
    "PostgresBarSalesRepository",
    "PostgresBookingRepository",
    "PostgresHealthRepository",
    "PostgresReviewRepository",
    "PostgresRoomTypeRepository",
    "ReviewRepo",
    "RoomTypeRepo",
]
