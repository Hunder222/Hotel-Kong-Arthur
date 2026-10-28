"""Errors raised by the business layer. Presentation maps them to HTTP; nothing here knows HTTP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class FieldError:
    """One broken rule on one field (or parameter)."""

    field: str
    message: str


class BusinessError(Exception):
    """Base class for every error the business layer raises on purpose."""


class ValidationFailed(BusinessError):
    """A well-formed request broke one or more field or business rules."""

    def __init__(self, field_errors: Sequence[FieldError]) -> None:
        self.field_errors: list[FieldError] = list(field_errors)
        count = len(self.field_errors)
        super().__init__(f"{count} field{'s are' if count != 1 else ' is'} invalid.")


class NotFound(BusinessError):
    """The requested resource does not exist."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class StorageUnavailable(BusinessError):
    """The data store cannot be reached."""

    def __init__(self, message: str = "The database is not reachable. Try again shortly.") -> None:
        self.message = message
        super().__init__(message)
