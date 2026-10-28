"""CLI entry point for idempotent sample data seeding (T040, R13, FR-004).

Usage:
    python -m hotel_api.presentation.cli.seed

Parses `context/teacher/international_names_with_rooms_1000.csv` and
`context/teacher/drinks_menu_with_sales.csv`, applies the documented single-entry U+FFFD repair
(`M\ufffdller` -> `Müller`), rejects any other U+FFFD replacement character, and delegates atomic
replacement to `SampleDataService`.
"""

from __future__ import annotations

import csv
import os
import sys
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path

from hotel_api.business.domain.models import DrinkCategory, Season
from hotel_api.business.errors import FieldError, ValidationFailed
from hotel_api.business.services.sample_data_service import (
    DEFAULT_SEED_YEAR,
    SampleBookingRow,
    SampleDataResult,
    SampleDataService,
    SampleDrinkRow,
)
from hotel_api.config import Settings
from hotel_api.main import sample_data_service_scope

BOOKINGS_FILENAME = "international_names_with_rooms_1000.csv"
DRINKS_FILENAME = "drinks_menu_with_sales.csv"
REPLACEMENT_CHAR = "\ufffd"

# Documented one-entry repair map (research R13):
# The teacher-supplied bookings CSV stores U+FFFD in 54 rows of the family name "Müller".
# Only this exact known token is repaired; any other U+FFFD aborts the seed.
REPAIR_MAP: dict[str, str] = {
    "M\ufffdller": "Müller",
}


def default_sample_data_dir() -> Path:
    """Locate `context/teacher` from `SAMPLE_DATA_DIR`, the repository tree, or `/repo`."""
    env_dir = os.environ.get("SAMPLE_DATA_DIR")
    if env_dir:
        return Path(env_dir)
    repo_candidate = Path(__file__).resolve().parents[5] / "context" / "teacher"
    if repo_candidate.is_dir():
        return repo_candidate
    return Path("/repo/context/teacher")


def repair_text(value: str | None, *, field_name: str = "field", row_number: int = 0) -> str:
    """Trim `value`, repair `M\ufffdller` -> `Müller`, and reject any other U+FFFD."""
    if value is None:
        raise ValueError(f"Row {row_number}: missing value for {field_name!r}.")
    trimmed = value.strip()
    repaired = REPAIR_MAP.get(trimmed, trimmed)
    if REPLACEMENT_CHAR in repaired:
        raise ValueError(
            f"Row {row_number} ({field_name}): unexpected Unicode replacement character (U+FFFD) in {trimmed!r}."
        )
    return repaired


def parse_bookings_csv(path: Path) -> list[SampleBookingRow]:
    """Parse `international_names_with_rooms_1000.csv` into `SampleBookingRow` records."""
    rows: list[SampleBookingRow] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=",")
        if reader.fieldnames is None:
            raise ValueError(f"Bookings CSV {path} has no header row.")
        reader.fieldnames = [name.strip() for name in reader.fieldnames]

        for row_number, raw in enumerate(reader, start=1):
            first_name = repair_text(raw.get("First Name"), field_name="First Name", row_number=row_number)
            family_name = repair_text(raw.get("Family Name"), field_name="Family Name", row_number=row_number)
            country = repair_text(raw.get("Country"), field_name="Country", row_number=row_number)
            room_type = repair_text(raw.get("Room Type"), field_name="Room Type", row_number=row_number)
            days_raw = repair_text(raw.get("Days Rented"), field_name="Days Rented", row_number=row_number)
            season_raw = repair_text(raw.get("Season"), field_name="Season", row_number=row_number)
            price_raw = repair_text(raw.get("Price"), field_name="Price", row_number=row_number)

            try:
                days_rented = int(days_raw)
            except ValueError as exc:
                raise ValidationFailed(
                    [FieldError("days_rented", f"Row {row_number}: invalid days_rented {days_raw!r}.")]
                ) from exc

            try:
                season = Season(season_raw)
            except ValueError as exc:
                raise ValidationFailed(
                    [FieldError("season", f"Row {row_number}: invalid season {season_raw!r}.")]
                ) from exc

            try:
                price_dkk = Decimal(price_raw.replace(",", "."))
            except InvalidOperation as exc:
                raise ValidationFailed(
                    [FieldError("price_dkk", f"Row {row_number}: invalid price {price_raw!r}.")]
                ) from exc

            rows.append(
                SampleBookingRow(
                    first_name=first_name,
                    family_name=family_name,
                    country=country,
                    room_type=room_type,
                    days_rented=days_rented,
                    season=season,
                    price_dkk=price_dkk,
                )
            )
    return rows


def parse_drinks_csv(path: Path) -> list[SampleDrinkRow]:
    """Parse `drinks_menu_with_sales.csv` (UTF-8 BOM, `;` delimiter, decimal comma) into `SampleDrinkRow` records."""
    rows: list[SampleDrinkRow] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        if reader.fieldnames is None:
            raise ValueError(f"Drinks CSV {path} has no header row.")
        reader.fieldnames = [name.strip() for name in reader.fieldnames]

        for row_number, raw in enumerate(reader, start=1):
            drink_name = repair_text(raw.get("Drink Name"), field_name="Drink Name", row_number=row_number)
            category_raw = repair_text(raw.get("Category"), field_name="Category", row_number=row_number)
            price_raw = repair_text(raw.get("Price (DKK)"), field_name="Price (DKK)", row_number=row_number)
            units_raw = repair_text(raw.get("Units Sold"), field_name="Units Sold", row_number=row_number)

            try:
                category = DrinkCategory(category_raw)
            except ValueError as exc:
                raise ValidationFailed(
                    [FieldError("category", f"Row {row_number}: invalid category {category_raw!r}.")]
                ) from exc

            try:
                unit_price_dkk = Decimal(price_raw.replace(",", "."))
            except InvalidOperation as exc:
                raise ValidationFailed(
                    [FieldError("unit_price_dkk", f"Row {row_number}: invalid unit price {price_raw!r}.")]
                ) from exc

            try:
                units_sold = int(units_raw)
            except ValueError as exc:
                raise ValidationFailed(
                    [FieldError("units_sold", f"Row {row_number}: invalid units sold {units_raw!r}.")]
                ) from exc

            rows.append(
                SampleDrinkRow(
                    drink_name=drink_name,
                    category=category,
                    unit_price_dkk=unit_price_dkk,
                    units_sold=units_sold,
                )
            )
    return rows


def run_seed(
    *,
    settings: Settings | None = None,
    sample_data_dir: Path | None = None,
    bookings_csv: Path | None = None,
    drinks_csv: Path | None = None,
    service: SampleDataService | None = None,
    year: int = DEFAULT_SEED_YEAR,
) -> SampleDataResult:
    """Parse the sample CSVs and atomically replace all operational data."""
    base_dir = sample_data_dir if sample_data_dir is not None else default_sample_data_dir()
    bookings_path = bookings_csv if bookings_csv is not None else base_dir / BOOKINGS_FILENAME
    drinks_path = drinks_csv if drinks_csv is not None else base_dir / DRINKS_FILENAME

    booking_rows = parse_bookings_csv(bookings_path)
    drink_rows = parse_drinks_csv(drinks_path)

    if service is not None:
        return service.replace_with_sample_data(booking_rows, None, drink_rows, year=year)

    with sample_data_service_scope(settings) as svc:
        return svc.replace_with_sample_data(booking_rows, None, drink_rows, year=year)


def main(
    argv: Sequence[str] | None = None,
    *,
    settings: Settings | None = None,
    sample_data_dir: Path | None = None,
    bookings_csv: Path | None = None,
    drinks_csv: Path | None = None,
) -> SampleDataResult:
    """CLI entry point: runs the seed and prints the summary line."""
    _ = argv
    result = run_seed(
        settings=settings,
        sample_data_dir=sample_data_dir,
        bookings_csv=bookings_csv,
        drinks_csv=drinks_csv,
    )
    print(f"{len(result.bookings)} bookings, {len(result.reviews)} reviews, {len(result.drinks)} drink sales")
    return result


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as exc:  # pragma: no cover - CLI top-level exit
        print(f"Seed failed: {exc}", file=sys.stderr)
        sys.exit(1)

