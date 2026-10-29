"""Unit tests for `SampleDataService` and sample CSV transformations (T039, R13).

Uses in-memory fake repository ports (no database). Verifies:
- Deterministic check-in date assignment cycling through each season's 2026 calendar dates
  (89 low / 153 mid / 123 high) and derived season matching the CSV season.
- Reproducible synthetic review generation (odd booking IDs, copied `room_type` and `stay_date`,
  ratings from `random.Random(2026)` with weights 5/10/20/35/30).
- Every one of the 1,000 sample bookings in `international_names_with_rooms_1000.csv` has a
  nightly rate inside its room type and season band (data-model.md §2.2).
- `M\ufffdller` -> `Müller` repair and rejection of any other U+FFFD character.
- Atomic replacement: validation or write failures leave pre-existing rows intact.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from hotel_api.business.domain.models import (
    BarDrinkSale,
    Booking,
    DrinkCategory,
    GuestReview,
    NewBooking,
    NewReview,
    RoomType,
    Season,
)
from hotel_api.business.errors import StorageUnavailable, ValidationFailed
from hotel_api.business.rules.pricing import price_error
from hotel_api.business.rules.seasons import season_of
from hotel_api.business.services.sample_data_service import (
    SampleBookingRow,
    SampleDataService,
    SampleDrinkRow,
    assign_check_in_dates,
    build_sample_reviews,
    season_dates_for_year,
)
from hotel_api.presentation.cli.seed import (
    BOOKINGS_FILENAME,
    DRINKS_FILENAME,
    default_sample_data_dir,
    parse_bookings_csv,
    parse_drinks_csv,
    repair_text,
)

pytestmark = pytest.mark.unit


class FakeRoomTypeRepository:
    def __init__(self, room_types: Sequence[RoomType]) -> None:
        self._room_types = list(room_types)

    def list_all(self) -> list[RoomType]:
        return list(self._room_types)

    def get_by_name(self, name: str) -> RoomType | None:
        return next((rt for rt in self._room_types if rt.name == name), None)


class FakeBookingRepository:
    def __init__(self, initial: Sequence[Booking] = ()) -> None:
        self.items: list[Booking] = list(initial)

    def list(self) -> list[Booking]:
        return list(reversed(self.items))

    def get(self, booking_id: int) -> Booking | None:
        return next((b for b in self.items if b.id == booking_id), None)

    def add(self, booking: NewBooking) -> Booking:
        raise NotImplementedError

    def replace(self, booking_id: int, booking: NewBooking) -> Booking | None:
        raise NotImplementedError

    def delete(self, booking_id: int) -> bool:
        raise NotImplementedError

    def delete_all(self) -> None:
        self.items.clear()

    def insert_many(self, bookings: Sequence[Booking]) -> None:
        self.items.extend(bookings)


class FakeReviewRepository:
    def __init__(self, initial: Sequence[GuestReview] = ()) -> None:
        self.items: list[GuestReview] = list(initial)

    def list(self) -> list[GuestReview]:
        return list(reversed(self.items))

    def get(self, review_id: int) -> GuestReview | None:
        return next((r for r in self.items if r.id == review_id), None)

    def add(self, review: NewReview) -> GuestReview:
        raise NotImplementedError

    def delete_all(self) -> None:
        self.items.clear()

    def insert_many(self, reviews: Sequence[GuestReview]) -> None:
        self.items.extend(reviews)


class FakeBarSalesRepository:
    def __init__(
        self,
        initial: Sequence[BarDrinkSale] = (),
        *,
        fail_on_insert: bool = False,
    ) -> None:
        self.items: list[BarDrinkSale] = list(initial)
        self.fail_on_insert = fail_on_insert

    def list(self) -> list[BarDrinkSale]:
        return list(self.items)

    def delete_all(self) -> None:
        self.items.clear()

    def insert_many(self, sales: Sequence[BarDrinkSale]) -> None:
        if self.fail_on_insert:
            raise StorageUnavailable("Simulated write failure on bar_drink_sales.")
        self.items.extend(sales)


def _sample_dir() -> Path:
    return default_sample_data_dir()


def test_season_dates_for_2026_have_expected_counts_and_first_dates() -> None:
    dates = season_dates_for_year(2026)
    assert len(dates[Season.LOW]) == 89
    assert len(dates[Season.MID]) == 153
    assert len(dates[Season.HIGH]) == 123
    assert dates[Season.LOW][0] == date(2026, 1, 1)
    assert dates[Season.MID][0] == date(2026, 3, 1)
    assert dates[Season.HIGH][0] == date(2026, 6, 1)


def test_date_assignment_is_deterministic_cycles_and_matches_csv_season() -> None:
    # 90 low-season rows: index 0 -> 2026-01-01, index 88 -> 2026-11-30, index 89 wraps to 2026-01-01
    seasons = [Season.LOW] * 90 + [Season.MID, Season.HIGH]
    assigned = assign_check_in_dates(seasons, year=2026)
    assert assigned == assign_check_in_dates(seasons, year=2026)
    assert assigned[0] == date(2026, 1, 1)
    assert assigned[7] == date(2026, 1, 8)
    assert assigned[88] == date(2026, 11, 30)
    assert assigned[89] == date(2026, 1, 1)
    assert assigned[90] == date(2026, 3, 1)
    assert assigned[91] == date(2026, 6, 1)
    for d, expected_season in zip(assigned, seasons):
        assert season_of(d) is expected_season


def test_rating_distribution_is_reproducible_and_copies_odd_bookings() -> None:
    bookings = [
        Booking(
            id=i,
            first_name=f"Guest{i}",
            family_name="Test",
            country="Denmark",
            room_type="Suite" if i % 3 == 0 else "Standard Single",
            check_in_date=date(2026, 3, (i % 28) + 1),
            days_rented=2,
            price_dkk=Decimal("6000.00") if i % 3 == 0 else Decimal("2300.00"),
        )
        for i in range(1, 1001)
    ]
    first_run = build_sample_reviews(bookings, rng_seed=2026)
    second_run = build_sample_reviews(bookings, rng_seed=2026)

    assert first_run == second_run
    assert len(first_run) == 500
    assert [r.id for r in first_run] == list(range(1, 501))
    assert [r.booking_id for r in first_run] == list(range(1, 1000, 2))

    for review, booking in zip(first_run, bookings[::2]):
        assert review.room_type == booking.room_type
        assert review.stay_date == booking.check_in_date
        assert 1 <= review.rating <= 5

    counts = Counter(r.rating for r in first_run)
    assert set(counts.keys()) == {1, 2, 3, 4, 5}
    # Ratings 4 and 5 carry 65% of the weight (35% + 30%)
    assert counts[4] + counts[5] > counts[1] + counts[2]


def test_every_sample_csv_booking_nightly_rate_is_inside_its_band(
    room_types: list[RoomType],
    by_name: dict[str, RoomType],
) -> None:
    bookings_path = _sample_dir() / BOOKINGS_FILENAME
    drinks_path = _sample_dir() / DRINKS_FILENAME
    booking_rows = parse_bookings_csv(bookings_path)
    drink_rows = parse_drinks_csv(drinks_path)

    assert len(booking_rows) == 1000
    assert len(drink_rows) == 30

    bookings_repo = FakeBookingRepository()
    reviews_repo = FakeReviewRepository()
    drinks_repo = FakeBarSalesRepository()
    service = SampleDataService(
        room_types=FakeRoomTypeRepository(room_types),
        bookings=bookings_repo,
        reviews=reviews_repo,
        bar_sales=drinks_repo,
    )

    result = service.replace_with_sample_data(booking_rows, None, drink_rows)
    assert len(result.bookings) == 1000
    assert len(result.reviews) == 500
    assert len(result.drinks) == 30

    for row, booking in zip(booking_rows, result.bookings):
        assert booking.season is row.season
        rt = by_name[booking.room_type]
        assert price_error(rt, booking.check_in_date, booking.days_rented, booking.price_dkk) is None

    assert result.bookings[0].id == 1
    assert result.bookings[0].first_name == "Liam"
    assert result.bookings[0].family_name == "Nguyen"
    assert result.bookings[0].room_type == "Spa Executive"
    assert result.bookings[0].check_in_date == date(2026, 3, 1)
    assert result.bookings[0].price_dkk == Decimal("2577.00")

    assert result.bookings[20].id == 21
    assert result.bookings[20].family_name == "Müller"
    assert result.bookings[20].check_in_date == date(2026, 1, 8)


def test_repair_text_fixes_muller_and_rejects_unknown_replacement_char() -> None:
    assert repair_text("  M\ufffdller ", field_name="Family Name", row_number=21) == "Müller"
    with pytest.raises(ValueError, match="U\\+FFFD"):
        repair_text("S\ufffdrensen", field_name="Family Name", row_number=99)


def test_replace_with_sample_data_is_atomic_when_validation_or_write_fails(
    room_types: list[RoomType],
) -> None:
    existing_booking = Booking(
        id=1,
        first_name="Existing",
        family_name="Guest",
        country="Denmark",
        room_type="Standard Single",
        check_in_date=date(2026, 1, 5),
        days_rented=2,
        price_dkk=Decimal("2100.00"),
    )
    existing_review = GuestReview(
        id=1,
        booking_id=1,
        room_type="Standard Single",
        stay_date=date(2026, 1, 5),
        rating=5,
    )
    existing_drink = BarDrinkSale(
        id=1,
        sales_year=2026,
        drink_name="Espresso",
        category=DrinkCategory.COFFEE,
        unit_price_dkk=Decimal("69.10"),
        units_sold=100,
    )

    bookings_repo = FakeBookingRepository([existing_booking])
    reviews_repo = FakeReviewRepository([existing_review])
    drinks_repo = FakeBarSalesRepository([existing_drink])
    service = SampleDataService(
        room_types=FakeRoomTypeRepository(room_types),
        bookings=bookings_repo,
        reviews=reviews_repo,
        bar_sales=drinks_repo,
    )

    # 1. Validation failure (price outside band) leaves existing rows untouched
    bad_row = SampleBookingRow(
        first_name="Bad",
        family_name="Price",
        country="Denmark",
        room_type="Standard Single",
        days_rented=3,
        season=Season.LOW,
        price_dkk=Decimal("4500.00"),
    )
    with pytest.raises(ValidationFailed):
        service.replace_with_sample_data([bad_row], None, [])

    assert bookings_repo.items == [existing_booking]
    assert reviews_repo.items == [existing_review]
    assert drinks_repo.items == [existing_drink]

    # 2. Write failure during final insert_many restores existing rows
    drinks_repo.fail_on_insert = True
    valid_row = SampleBookingRow(
        first_name="Liam",
        family_name="Nguyen",
        country="China",
        room_type="Spa Executive",
        days_rented=1,
        season=Season.MID,
        price_dkk=Decimal("2577.00"),
    )
    valid_drink = SampleDrinkRow(
        drink_name="Margarita",
        category=DrinkCategory.COCKTAIL,
        unit_price_dkk=Decimal("72.47"),
        units_sold=2361,
    )
    with pytest.raises(StorageUnavailable):
        service.replace_with_sample_data([valid_row], None, [valid_drink])

    assert bookings_repo.items == [existing_booking]
    assert reviews_repo.items == [existing_review]
    assert drinks_repo.items == [existing_drink]

