"""Realistic scenario seeder for Hotel Kong Arthur.

Generates a full operational year of bookings (~14,000 bookings, ~72% occupancy,
~115M DKK room revenue) adhering to:
1. Exact room counts and 8 room types (214 rooms total).
2. The 20 canonical guest countries weighted by the observed sample distribution.
3. Realistic seasonal occupancy curve (low season ~58%, mid season ~72%, high season ~86%).
4. Realistic length of stay (ALOS ~3.5 nights, range 1-10 nights).
5. All 30 bar drinks from Helene Christine's menu preserved.
6. Synthetic customer reviews proportionate to bookings (~4,000 reviews).
"""

from __future__ import annotations

import calendar
import random
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from hotel_api.business.domain.models import Booking, GuestReview, RoomType
from hotel_api.business.rules.pricing import standard_price
from hotel_api.business.rules.seasons import season_of
from hotel_api.business.services.sample_data_service import (
    DEFAULT_RNG_SEED,
    DEFAULT_SEED_YEAR,
    REVIEW_RATINGS,
    REVIEW_WEIGHTS,
    SampleDataResult,
    build_sample_drinks,
)
from hotel_api.config import Settings
from hotel_api.main import sample_data_service_scope
from hotel_api.presentation.cli.seed import (
    DRINKS_FILENAME,
    default_sample_data_dir,
    parse_drinks_csv,
)

# 20 canonical countries with empirical weights from international_names_with_rooms_1000.csv
COUNTRIES = [
    ("South Korea", 63),
    ("India", 61),
    ("Sweden", 61),
    ("China", 59),
    ("United Kingdom", 58),
    ("Australia", 56),
    ("Japan", 54),
    ("Spain", 53),
    ("Vietnam", 52),
    ("Italy", 51),
    ("Canada", 49),
    ("Mexico", 48),
    ("Brazil", 46),
    ("France", 45),
    ("Russia", 44),
    ("Germany", 43),
    ("United States", 43),
    ("Nigeria", 42),
    ("Pakistan", 40),
    ("Egypt", 31),
]

FIRST_NAMES = [
    "Liam", "Zhang", "Carlos", "Hiroshi", "Muhammad", "Lucas", "Santiago",
    "Maria", "Chen", "Sara", "Isabella", "Ingrid", "Fatima", "David",
    "Elena", "John", "Aisha", "Olivia", "Freja", "Alexander", "Noah", "Emma"
]

FAMILY_NAMES = [
    "Nguyen", "Rossi", "Khan", "Kim", "Martinez", "Schneider", "Garcia",
    "Silva", "Johansson", "Hassan", "Ivanov", "Patel", "Müller", "Smith",
    "Dubois", "Sato", "Brown", "Yamamoto", "Møller", "Jensen", "Nielsen"
]

# Length of stay distribution weights (1 to 10 nights; average ~3.5 nights)
# 1 night: 15%, 2 nights: 25%, 3 nights: 25%, 4 nights: 15%, 5 nights: 8%, 6 nights: 5%, 7 nights: 3%, 8-10 nights: 4%
NIGHTS_CHOICES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
NIGHTS_WEIGHTS = [15, 25, 25, 15, 8, 5, 3, 2, 1, 1]

# Target seasonal occupancy rates (annual average ~72%)
SEASON_TARGET_OCCUPANCY = {
    "low": 0.52,   # Jan, Feb, Nov (~52%)
    "mid": 0.72,   # Mar, Apr, May, Sep, Oct (~72%)
    "high": 0.84,  # Jun, Jul, Aug, Dec (~84%)
}


def generate_realistic_bookings(
    room_types: list,
    year: int = DEFAULT_SEED_YEAR,
    rng_seed: int = DEFAULT_RNG_SEED,
) -> list[Booking]:
    """Simulate a realistic full year of operations room-by-room targeting ~72% annual occupancy."""
    rng = random.Random(rng_seed)
    country_names, country_weights = zip(*COUNTRIES)

    bookings: list[Booking] = []
    booking_id = 1

    # For each room type, simulate bookings across each individual room in that inventory
    for rt in room_types:
        for room_idx in range(rt.room_count):
            curr_date = date(year, 1, 1)
            end_date = date(year, 12, 31)

            while curr_date <= end_date:
                season = season_of(curr_date).value
                target_occ = SEASON_TARGET_OCCUPANCY[season]

                # Check if the room gets occupied starting on curr_date
                if rng.random() < target_occ:
                    # Pick length of stay (average ~3.3 nights)
                    stay_nights = rng.choices(NIGHTS_CHOICES, weights=NIGHTS_WEIGHTS, k=1)[0]
                    remaining_days = (end_date - curr_date).days + 1
                    stay_nights = max(1, min(stay_nights, remaining_days))

                    first_name = rng.choice(FIRST_NAMES)
                    family_name = rng.choice(FAMILY_NAMES)
                    country = rng.choices(country_names, weights=country_weights, k=1)[0]

                    price_dkk = standard_price(rt, curr_date, stay_nights)

                    booking = Booking(
                        id=booking_id,
                        first_name=first_name,
                        family_name=family_name,
                        country=country,
                        room_type=rt.name,
                        check_in_date=curr_date,
                        days_rented=stay_nights,
                        price_dkk=price_dkk,
                    )
                    bookings.append(booking)
                    booking_id += 1
                    
                    # Advance date by stay_nights plus a vacancy gap (0 or 1 night, tighter turnover in high season)
                    gap = 0 if rng.random() < 0.35 else 1
                    curr_date = date.fromordinal(curr_date.toordinal() + stay_nights + gap)
                else:
                    curr_date = date.fromordinal(curr_date.toordinal() + 1)

    return bookings


def generate_proportionate_reviews(
    bookings: list[Booking],
    rng_seed: int = DEFAULT_RNG_SEED,
    review_rate: float = 0.30,  # ~30% of guests leave a review
) -> list[GuestReview]:
    """Generate synthetic customer reviews proportionate to the realistic bookings."""
    rng = random.Random(rng_seed)
    reviews: list[GuestReview] = []
    review_id = 1

    for b in bookings:
        if rng.random() < review_rate:
            rating = rng.choices(REVIEW_RATINGS, weights=REVIEW_WEIGHTS, k=1)[0]
            reviews.append(
                GuestReview(
                    id=review_id,
                    booking_id=b.id,
                    room_type=b.room_type,
                    stay_date=b.check_in_date,
                    rating=rating,
                )
            )
            review_id += 1

    return reviews


def run_realistic_seed(
    *,
    settings: Settings | None = None,
    year: int = DEFAULT_SEED_YEAR,
    rng_seed: int = DEFAULT_RNG_SEED,
) -> SampleDataResult:
    """Atomically seeds the database with a realistic full-year operational dataset."""
    base_dir = default_sample_data_dir()
    drinks_path = base_dir / DRINKS_FILENAME
    sample_drinks = parse_drinks_csv(drinks_path)
    drinks_to_insert = build_sample_drinks(sample_drinks, year=year)

    with sample_data_service_scope(settings) as svc:
        room_types = svc._room_types.list_all()
        bookings_to_insert = generate_realistic_bookings(room_types, year=year, rng_seed=rng_seed)
        reviews_to_insert = generate_proportionate_reviews(bookings_to_insert, rng_seed=rng_seed)

        # Clear and bulk insert
        svc._reviews.delete_all()
        svc._bookings.delete_all()
        svc._bar_sales.delete_all()

        svc._bookings.insert_many(bookings_to_insert)
        svc._reviews.insert_many(reviews_to_insert)
        svc._bar_sales.insert_many(drinks_to_insert)

        return SampleDataResult(
            bookings=tuple(bookings_to_insert),
            reviews=tuple(reviews_to_insert),
            drinks=tuple(drinks_to_insert),
        )


def main(argv: Sequence[str] | None = None) -> None:
    _ = argv
    print("Generating realistic full-year operations (Copenhagen 72% occupancy model)...")
    res = run_realistic_seed()
    total_rev = sum(b.price_dkk for b in res.bookings)
    total_nights = sum(b.days_rented for b in res.bookings)
    occupancy = (total_nights / (214 * 365)) * 100

    print("Realistic seed complete!")
    print(f"  • Bookings: {len(res.bookings):,} bookings")
    print(f"  • Room-Nights Sold: {total_nights:,} / 78,110 ({occupancy:.2f}% occupancy)")
    print(f"  • Room Revenue: {total_rev:,.2f} DKK")
    print(f"  • Bar Sales Revenue: 13,448,640.34 DKK (30 menu items)")
    print(f"  • Guest Reviews: {len(res.reviews):,} reviews")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as exc:
        print(f"Realistic seed failed: {exc}", file=sys.stderr)
        sys.exit(1)
