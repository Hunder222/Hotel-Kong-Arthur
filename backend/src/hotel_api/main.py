"""Composition root: the only module that knows all three layers (research R3).

It builds the FastAPI app, wires cross-cutting concerns (CORS, `Cache-Control: no-store`, error
handlers) and binds each service provider declared by the presentation layer to a request-scoped
factory that creates the repositories and the service over one database connection. That connection
is committed before the response is sent when the request succeeds, and rolled back on any error.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymysql.connections import Connection
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from hotel_api.business.services.bar_service import BarService
from hotel_api.business.services.booking_service import BookingService
from hotel_api.business.services.health_service import HealthService
from hotel_api.business.services.review_service import ReviewService
from hotel_api.business.services.room_type_service import RoomTypeService
from hotel_api.business.services.sample_data_service import SampleDataService
from hotel_api.config import Settings, get_settings
from hotel_api.data.connection import connection_scope
from hotel_api.data.repositories.bar_sales import MySqlBarSalesRepository
from hotel_api.data.repositories.bookings import MySqlBookingRepository
from hotel_api.data.repositories.health import MySqlHealthRepository
from hotel_api.data.repositories.reviews import MySqlReviewRepository
from hotel_api.data.repositories.room_types import MySqlRoomTypeRepository
from hotel_api.presentation.api import dependencies as deps
from hotel_api.presentation.api.errors import register_error_handlers
from hotel_api.presentation.api.routers import bar, bookings, health, reviews, room_types


@contextmanager
def sample_data_service_scope(settings: Settings | None = None) -> Iterator[SampleDataService]:
    """Open one transactional database connection and yield a wired `SampleDataService` (R3, R13)."""
    with connection_scope(settings) as conn:
        yield SampleDataService(
            room_types=MySqlRoomTypeRepository(conn),
            bookings=MySqlBookingRepository(conn),
            reviews=MySqlReviewRepository(conn),
            bar_sales=MySqlBarSalesRepository(conn),
        )


class NoStoreMiddleware:
    """Adds `Cache-Control: no-store` to every HTTP response (research R7: always live)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_header(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [(k, v) for k, v in message.get("headers", []) if k.lower() != b"cache-control"]
                headers.append((b"cache-control", b"no-store"))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_header)


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or get_settings()
    # FastAPI's generated 3.1 documentation is off: contracts/openapi.yaml is the only contract (R4).
    app = FastAPI(title="Hotel Kong Arthur API", docs_url=None, redoc_url=None, openapi_url=None)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cfg.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Location"],
    )
    app.add_middleware(NoStoreMiddleware)
    register_error_handlers(app)

    # Annotated with the bare `Connection`: FastAPI evaluates these annotations at runtime, and
    # `Connection[...]` is not subscriptable outside type checking.
    def request_connection() -> Iterator[Connection]:
        # One connection and one transaction per request: commit on success, rollback on error.
        with connection_scope(cfg) as conn:
            yield conn

    # scope="function": the transaction ends (commit) before the response is sent to the client.
    connection = Depends(request_connection, scope="function")

    def health_service(conn: Connection = connection) -> HealthService:
        return HealthService(MySqlHealthRepository(conn))

    def room_type_service(conn: Connection = connection) -> RoomTypeService:
        return RoomTypeService(MySqlRoomTypeRepository(conn))

    def booking_service(conn: Connection = connection) -> BookingService:
        return BookingService(MySqlBookingRepository(conn), MySqlRoomTypeRepository(conn))

    def review_service(conn: Connection = connection) -> ReviewService:
        return ReviewService(MySqlReviewRepository(conn), MySqlBookingRepository(conn), MySqlRoomTypeRepository(conn))

    def bar_service(conn: Connection = connection) -> BarService:
        return BarService(MySqlBarSalesRepository(conn))

    app.dependency_overrides[deps.get_health_service] = health_service
    app.dependency_overrides[deps.get_bar_service] = bar_service
    app.dependency_overrides[deps.get_review_service] = review_service
    app.dependency_overrides[deps.get_booking_service] = booking_service
    app.dependency_overrides[deps.get_room_type_service] = room_type_service

    app.include_router(health.router)
    app.include_router(room_types.router)
    app.include_router(bookings.router)
    app.include_router(reviews.router)
    app.include_router(bar.router)
    return app


app = create_app()
