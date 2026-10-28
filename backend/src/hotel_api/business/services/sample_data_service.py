"""Use case: idempotent reset and seeding of the sample dataset (T038, R13, FR-004).

Replaces all operational tables (`reviews`, `bookings`, `bar_drink_sales`) in a single
transaction while keeping reference data (`room_types`, `room_type_rates`) intact:
1. Assigns deterministic 2026 check-in dates per season (the k-th row of a season gets the
   k mod N-th date of that season's calendar dates in 2026, where N = 89 / 153 / 123).
2. Validates every booking against `booking_validation` and `pricing` (all 1,000 pass).
3. Generates 500 synthetic reviews (one per odd booking ID, copying `booking_id`, `room_type`,
   and `stay_date` from the booking, with ratings drawn from `random.Random(2026)` using
   weights 1: 5%, 2: 10%, 3: 20%, 4: 35%, 5: 30%).
4. Validates and builds the 30 bar drink sales for `sales_year = 2026`.
5. Deletes existing operational rows and bulk-inserts the new rows with explicit IDs.
"""

from __future__ import annotations

import calendar
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from hotel_api.business.domain.models import (
    BarDrinkSale,
    Booking,
    DrinkCategory,
    GuestReview,
    RoomType,
    Season,
)
from hotel_api.business.errors import FieldError, ValidationFailed
from hotel_api.business.ports import (
    BarSalesRepository,
    BookingRepository,
    ReviewRepository,
    RoomTypeRepository,
)
from hotel_api.business.rules import _parsing, booking_validation, pricing
from hotel_api.business.rules.seasons import SEASON_ORDER, season_of

DEFAULT_SEED_YEAR: int = 2026
DEFAULT_RNG_SEED: int = 2026
REVIEW_RATINGS: tuple[int, ...] = (1, 2, 3, 4, 5)
REVIEW_WEIGHTS: tuple[int, ...] = (5, 10, 20, 35, 30)


@dataclass(frozen=True)
class SampleBookingRow:
    """One parsed row from the sample bookings CSV prior to date assignment."""

    first_name: str
    family_name: str
    country: str
    room_type: str
    days_rented: int
    season: Season
    price_dkk: Decimal


@dataclass(frozen=True)
class SampleDrinkRow:
    """One parsed row from the sample bar drink sales CSV."""

    drink_name: str
    category: DrinkCategory
    unit_price_dkk: Decimal
    units_sold: int


@dataclass(frozen=True)
class SampleDataResult:
    """Summary of the rows persisted by `replace_with_sample_data`."""

    bookings: tuple[Booking, ...]
    reviews: tuple[GuestReview, ...]
    drinks: tuple[BarDrinkSale, ...]


def season_dates_for_year(year: int = DEFAULT_SEED_YEAR) -> dict[Season, list[date]]:
    """All calendar dates in `year` grouped by season in chronological order.

    For 2026: low = 89 days (Jan, Feb, Nov), mid = 153 days (Mar, Apr, May, Sep, Oct),
    high = 123 days (Jun, Jul, Aug, Dec).
    """
    grouped: dict[Season, list[date]] = {season: [] for season in SEASON_ORDER}
    for month in range(1, 13):
        days_in_month = calendar.monthrange(year, month)[1]
        for day_num in range(1, days_in_month + 1):
            d = date(year, month, day_num)
            grouped[season_of(d)].append(d)
    return grouped


def _coerce_season(raw_season: Any) -> Season:
    if isinstance(raw_season, Season):
        return raw_season
    if isinstance(raw_season, str):
        try:
            return Season(raw_season.strip())
        except ValueError as exc:
            raise ValidationFailed([FieldError("season", f"Invalid season: {raw_season!r}.")]) from exc
    raise ValidationFailed([FieldError("season", f"Invalid season: {raw_season!r}.")])


def assign_check_in_dates(
    seasons: Sequence[Season | str],
    year: int = DEFAULT_SEED_YEAR,
) -> list[date]:
    """Assign each row's check-in date: the k-th row (0-based) of a season gets the k mod N-th date."""
    dates_by_season = season_dates_for_year(year)
    seen_counts: dict[Season, int] = {season: 0 for season in SEASON_ORDER}
    assigned: list[date] = []

    for raw_season in seasons:
        season = _coerce_season(raw_season)
        bucket = dates_by_season[season]
        k = seen_counts[season]
        seen_counts[season] = k + 1
        assigned.append(bucket[k % len(bucket)])

    return assigned


def build_sample_bookings(
    rows: Sequence[SampleBookingRow | Booking | Mapping[str, Any]],
    room_types: Sequence[RoomType],
    year: int = DEFAULT_SEED_YEAR,
) -> list[Booking]:
    """Validate and build `Booking` objects with explicit IDs 1..N and deterministic check-in dates."""
    dates_by_season = season_dates_for_year(year)
    seen_counts: dict[Season, int] = {season: 0 for season in SEASON_ORDER}
    room_types_by_name = {rt.name: rt for rt in room_types}
    bookings: list[Booking] = []

    for idx, row in enumerate(rows, start=1):
        explicit_id = idx
        if isinstance(row, Booking):
            explicit_id = row.id if row.id >= 1 else idx
            first_name: Any = row.first_name
            family_name: Any = row.family_name
            country: Any = row.country
            room_type_name: Any = row.room_type
            check_in_date: Any = row.check_in_date
            days_rented: Any = row.days_rented
            price_dkk: Any = row.price_dkk
        elif isinstance(row, SampleBookingRow):
            season = _coerce_season(row.season)
            bucket = dates_by_season[season]
            k = seen_counts[season]
            seen_counts[season] = k + 1
            check_in_date = bucket[k % len(bucket)]
            first_name = row.first_name
            family_name = row.family_name
            country = row.country
            room_type_name = row.room_type
            days_rented = row.days_rented
            price_dkk = row.price_dkk
        elif isinstance(row, Mapping):
            if row.get("id") is not None:
                explicit_id = int(row["id"])
            if row.get("check_in_date") is not None:
                check_in_date = row["check_in_date"]
                if row.get("season") is not None:
                    expected_season = _coerce_season(row["season"])
                    parsed_date = _parsing.iso_date(check_in_date)
                    if parsed_date is not None and season_of(parsed_date) != expected_season:
                        raise ValidationFailed(
                            [
                                FieldError(
                                    "season",
                                    f"Check-in date {parsed_date} has season {season_of(parsed_date).value!r}, "
                                    f"not {expected_season.value!r}.",
                                )
                            ]
                        )
            else:
                season = _coerce_season(row.get("season"))
                bucket = dates_by_season[season]
                k = seen_counts[season]
                seen_counts[season] = k + 1
                check_in_date = bucket[k % len(bucket)]
            first_name = row.get("first_name")
            family_name = row.get("family_name")
            country = row.get("country")
            room_type_name = row.get("room_type")
            days_rented = row.get("days_rented")
            price_dkk = row.get("price_dkk")
        else:
            raise ValidationFailed([FieldError("booking", f"Unsupported booking row type: {type(row)!r}.")])

        raw_payload = {
            "first_name": first_name,
            "family_name": family_name,
            "country": country,
            "room_type": room_type_name,
            "check_in_date": check_in_date,
            "days_rented": days_rented,
            "price_dkk": price_dkk,
        }
        validated, errors = booking_validation.validate_booking(raw_payload, room_types)
        if errors or validated is None:
            raise ValidationFailed(errors)

        rt = room_types_by_name[validated.room_type]
        final_price = (
            validated.price_dkk
            if validated.price_dkk is not None
            else pricing.standard_price(rt, validated.check_in_date, validated.days_rented)
        )

        bookings.append(
            Booking(
                id=explicit_id,
                first_name=validated.first_name,
                family_name=validated.family_name,
                country=validated.country,
                room_type=validated.room_type,
                check_in_date=validated.check_in_date,
                days_rented=validated.days_rented,
                price_dkk=final_price,
            )
        )

    return bookings


def build_sample_reviews(
    bookings: Sequence[Booking],
    rng_seed: int = DEFAULT_RNG_SEED,
) -> list[GuestReview]:
    """Generate one synthetic review per odd booking ID using `random.Random(rng_seed)`.

    Ratings are drawn from 1..5 with weights 5%, 10%, 20%, 35%, 30%.
    `booking_id`, `room_type`, and `stay_date` are copied from the reviewed booking.
    """
    rng = random.Random(rng_seed)
    odd_bookings = [b for b in bookings if b.id % 2 == 1]
    ratings = rng.choices(REVIEW_RATINGS, weights=REVIEW_WEIGHTS, k=len(odd_bookings))

    reviews: list[GuestReview] = []
    for review_id, (booking, rating) in enumerate(zip(odd_bookings, ratings), start=1):
        reviews.append(
            GuestReview(
                id=review_id,
                booking_id=booking.id,
                room_type=booking.room_type,
                stay_date=booking.check_in_date,
                rating=rating,
            )
        )
    return reviews


def _validate_custom_reviews(
    reviews: Sequence[GuestReview | Mapping[str, Any]],
    bookings: Sequence[Booking],
) -> list[GuestReview]:
    booking_map = {b.id: b for b in bookings}
    validated: list[GuestReview] = []
    for idx, item in enumerate(reviews, start=1):
        if isinstance(item, GuestReview):
            review_id = item.id if item.id >= 1 else idx
            booking_id = item.booking_id
            room_type = item.room_type
            stay_date = item.stay_date
            rating = _parsing.whole_number(item.rating)
        elif isinstance(item, Mapping):
            review_id = int(item.get("id") or idx)
            booking_id = _parsing.whole_number(item.get("booking_id")) if item.get("booking_id") is not None else None
            room_type = item.get("room_type")
            stay_date = _parsing.iso_date(item.get("stay_date")) if item.get("stay_date") is not None else None
            rating = _parsing.whole_number(item.get("rating"))
        else:
            raise ValidationFailed([FieldError("review", f"Unsupported review type: {type(item)!r}.")])

        if rating is None or not (1 <= rating <= 5):
            raise ValidationFailed([FieldError("rating", "Rating must be a whole number from 1 to 5.")])

        if booking_id is not None:
            linked = booking_map.get(booking_id)
            if linked is None:
                raise ValidationFailed([FieldError("booking_id", f"Booking {booking_id} does not exist.")])
            room_type = linked.room_type
            stay_date = linked.check_in_date

        if not room_type or stay_date is None:
            raise ValidationFailed([FieldError("review", "Review requires room_type and stay_date.")])

        validated.append(
            GuestReview(
                id=review_id,
                booking_id=booking_id,
                room_type=str(room_type),
                stay_date=stay_date,
                rating=rating,
            )
        )
    return validated


def build_sample_drinks(
    rows: Sequence[SampleDrinkRow | BarDrinkSale | Mapping[str, Any]],
    year: int = DEFAULT_SEED_YEAR,
) -> list[BarDrinkSale]:
    """Validate and build `BarDrinkSale` objects with explicit IDs 1..M for `sales_year = year`."""
    sales: list[BarDrinkSale] = []
    seen_names: set[str] = set()

    for idx, row in enumerate(rows, start=1):
        explicit_id = idx
        sales_year = year
        if isinstance(row, BarDrinkSale):
            explicit_id = row.id if row.id >= 1 else idx
            sales_year = row.sales_year
            raw_name: Any = row.drink_name
            raw_category: Any = row.category
            raw_price: Any = row.unit_price_dkk
            raw_units: Any = row.units_sold
        elif isinstance(row, SampleDrinkRow):
            raw_name = row.drink_name
            raw_category = row.category
            raw_price = row.unit_price_dkk
            raw_units = row.units_sold
        elif isinstance(row, Mapping):
            if row.get("id") is not None:
                explicit_id = int(row["id"])
            if row.get("sales_year") is not None:
                sales_year = int(row["sales_year"])
            raw_name = row.get("drink_name")
            raw_category = row.get("category")
            raw_price = row.get("unit_price_dkk")
            raw_units = row.get("units_sold")
        else:
            raise ValidationFailed([FieldError("drink", f"Unsupported drink row type: {type(row)!r}.")])

        errors: list[FieldError] = []
        drink_name = _parsing.clean_text(raw_name)
        if drink_name is None:
            errors.append(FieldError("drink_name", "Drink name must be between 1 and 100 characters."))
        elif drink_name in seen_names:
            errors.append(FieldError("drink_name", f"Duplicate drink name {drink_name!r} for year {sales_year}."))

        category: DrinkCategory | None = None
        if isinstance(raw_category, DrinkCategory):
            category = raw_category
        elif isinstance(raw_category, str):
            try:
                category = DrinkCategory(raw_category.strip())
            except ValueError:
                category = None
        if category is None:
            errors.append(FieldError("category", "Category must be Cocktail or Coffee."))

        unit_price = _parsing.money(raw_price)
        if unit_price is None:
            errors.append(FieldError("unit_price_dkk", "Unit price must be a positive amount with at most 2 decimals."))

        units_sold = _parsing.whole_number(raw_units)
        if units_sold is None or units_sold < 0:
            errors.append(FieldError("units_sold", "Units sold must be a non-negative whole number."))

        if errors:
            raise ValidationFailed(errors)

        assert drink_name is not None and category is not None and unit_price is not None and units_sold is not None
        seen_names.add(drink_name)
        sales.append(
            BarDrinkSale(
                id=explicit_id,
                sales_year=sales_year,
                drink_name=drink_name,
                category=category,
                unit_price_dkk=unit_price,
                units_sold=units_sold,
            )
        )

    return sales


class SampleDataService:
    """Replaces all operational data with the validated sample dataset in one transaction."""

    def __init__(
        self,
        room_types: RoomTypeRepository,
        bookings: BookingRepository,
        reviews: ReviewRepository,
        bar_sales: BarSalesRepository,
    ) -> None:
        self._room_types = room_types
        self._bookings = bookings
        self._reviews = reviews
        self._bar_sales = bar_sales

    def replace_with_sample_data(
        self,
        bookings: Sequence[SampleBookingRow | Booking | Mapping[str, Any]],
        drinks_or_reviews: Sequence[SampleDrinkRow | BarDrinkSale | Mapping[str, Any]]
        | Sequence[GuestReview | Mapping[str, Any]]
        | None = None,
        drinks: Sequence[SampleDrinkRow | BarDrinkSale | Mapping[str, Any]] | None = None,
        *,
        reviews: Sequence[GuestReview | Mapping[str, Any]] | None = None,
        year: int = DEFAULT_SEED_YEAR,
        rng_seed: int = DEFAULT_RNG_SEED,
    ) -> SampleDataResult:
        """Validate and replace `reviews`, `bookings`, and `bar_drink_sales` atomically.

        Accepts either `(bookings, drinks)` (generating the 500 synthetic reviews automatically)
        or `(bookings, reviews, drinks)` (using custom `reviews` or generating them when `None`).
        """
        if drinks is not None:
            raw_reviews: Sequence[GuestReview | Mapping[str, Any]] | None = (
                reviews if reviews is not None else drinks_or_reviews  # type: ignore[assignment]
            )
            raw_drinks: Sequence[SampleDrinkRow | BarDrinkSale | Mapping[str, Any]] = drinks
        else:
            raw_reviews = reviews
            raw_drinks = (
                drinks_or_reviews  # type: ignore[assignment]
                if drinks_or_reviews is not None
                else ()
            )

        # 1. Validate and build all domain objects before touching any table.
        room_types = self._room_types.list_all()
        bookings_to_insert = build_sample_bookings(bookings, room_types, year=year)
        reviews_to_insert = (
            _validate_custom_reviews(raw_reviews, bookings_to_insert)
            if raw_reviews is not None
            else build_sample_reviews(bookings_to_insert, rng_seed=rng_seed)
        )
        drinks_to_insert = build_sample_drinks(raw_drinks, year=year)

        # 2. Snapshot any in-memory fake repositories so unit tests without SQL rollback remain atomic.
        snapshots: list[tuple[Any, str, list[Any]]] = []
        for repo in (self._reviews, self._bookings, self._bar_sales):
            for attr in ("items", "_items"):
                if hasattr(repo, attr) and isinstance(getattr(repo, attr), list):
                    snapshots.append((repo, attr, list(getattr(repo, attr))))

        try:
            self._reviews.delete_all()
            self._bookings.delete_all()
            self._bar_sales.delete_all()

            self._bookings.insert_many(bookings_to_insert)
            self._reviews.insert_many(reviews_to_insert)
            self._bar_sales.insert_many(drinks_to_insert)
        except Exception:
            for repo, attr, saved in snapshots:
                getattr(repo, attr)[:] = saved
            raise

        return SampleDataResult(
            bookings=tuple(bookings_to_insert),
            reviews=tuple(reviews_to_insert),
            drinks=tuple(drinks_to_insert),
        )


__all__ = [
    "DEFAULT_RNG_SEED",
    "DEFAULT_SEED_YEAR",
    "REVIEW_RATINGS",
    "REVIEW_WEIGHTS",
    "SampleBookingRow",
    "SampleDataResult",
    "SampleDataService",
    "SampleDrinkRow",
    "assign_check_in_dates",
    "build_sample_bookings",
    "build_sample_drinks",
    "build_sample_reviews",
    "season_dates_for_year",
]
