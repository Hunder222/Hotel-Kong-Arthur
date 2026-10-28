"""Maps errors to RFC 9457 Problem Details (`application/problem+json`), as the contract defines.

400 malformed JSON, or an invalid query/path parameter
404 NotFound, or an unknown route
422 ValidationFailed, or a well-formed body that breaks the DTO shape
503 StorageUnavailable
500 anything unexpected (details are logged, never returned)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from hotel_api.business.errors import NotFound, StorageUnavailable, ValidationFailed
from hotel_api.presentation.api.schemas.problem import FieldError, Problem

logger = logging.getLogger(__name__)

PROBLEM_JSON = "application/problem+json"
_URN = "urn:hotel-kong-arthur:problem:"
MALFORMED = _URN + "malformed-request"
NOT_FOUND = _URN + "not-found"
VALIDATION = _URN + "validation-error"
UNAVAILABLE = _URN + "service-unavailable"
INTERNAL = _URN + "internal-error"


def problem_response(
    status: int,
    type_: str,
    title: str,
    detail: str | None = None,
    errors: list[FieldError] | None = None,
) -> JSONResponse:
    body = Problem(type=type_, title=title, status=status, detail=detail, errors=errors)
    return JSONResponse(
        status_code=status,
        content=body.model_dump(mode="json", exclude_none=True),
        media_type=PROBLEM_JSON,
    )


def _count(n: int) -> str:
    return f"{n} field{' is' if n == 1 else 's are'} invalid."


def _field_of(loc: tuple[Any, ...]) -> str:
    names = [str(part) for part in loc[1:] if not isinstance(part, int)]
    return names[-1] if names else (str(loc[0]) if loc else "body")


def _message_of(error: dict[str, Any]) -> str:
    message = str(error.get("msg", "Invalid value."))
    message = message.removeprefix("Value error, ")
    return message[:1].upper() + message[1:] + ("" if message.endswith(".") else ".")


async def _validation_failed(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ValidationFailed)
    errors = [FieldError(field=e.field, message=e.message) for e in exc.field_errors]
    return problem_response(422, VALIDATION, "Validation failed", _count(len(errors)), errors)


async def _not_found(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, NotFound)
    return problem_response(404, NOT_FOUND, "Not found", exc.message)


async def _storage_unavailable(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StorageUnavailable)
    return problem_response(503, UNAVAILABLE, "Service unavailable", exc.message)


async def _request_invalid(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    raw = exc.errors()
    errors = [FieldError(field=_field_of(tuple(e["loc"])), message=_message_of(e)) for e in raw]
    malformed = any(
        e["loc"] and (e["loc"][0] in ("query", "path", "header") or e.get("type") == "json_invalid")
        for e in raw
    )
    if malformed:
        json_broken = any(e.get("type") == "json_invalid" for e in raw)
        title, detail = "Malformed request", (
            "The request body is not valid JSON." if json_broken else "A query or path parameter is invalid."
        )
        return problem_response(400, MALFORMED, title, detail, errors)
    return problem_response(422, VALIDATION, "Validation failed", _count(len(errors)), errors)


async def _http_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    if exc.status_code == 404:
        return problem_response(404, NOT_FOUND, "Not found", "No such resource.")
    title = "Malformed request" if exc.status_code < 500 else "Server error"
    type_ = MALFORMED if exc.status_code < 500 else INTERNAL
    return problem_response(exc.status_code, type_, title, str(exc.detail))


async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error", exc_info=exc)
    return problem_response(500, INTERNAL, "Internal server error", "An unexpected error occurred.")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ValidationFailed, _validation_failed)
    app.add_exception_handler(NotFound, _not_found)
    app.add_exception_handler(StorageUnavailable, _storage_unavailable)
    app.add_exception_handler(RequestValidationError, _request_invalid)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(Exception, _unexpected)
