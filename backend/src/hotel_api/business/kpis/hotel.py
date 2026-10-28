"""Hotel KPIs: revenue (K2, A2-A6), occupancy (K1), satisfaction (K3), ALOS / ADR / revenue per booking (A7).
FR-006-FR-011, FR-015, data-model §7.

Pure functions, no I/O. Each function takes the reporting `year` and counts only bookings whose
`check_in_date` lies in that year and reviews whose `stay_date` lies in it: a booking (with its revenue
and nights) belongs entirely to the season and year of its check-in date, a review to those of its stay
date (research R8). Rounding and shares follow `rules/numbers.py`; ranks follow `rules/ranking.py`;
available room-nights follow `rules/seasons.py`.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from decimal import Decimal

from hotel_api.business.domain.models import (
    Booking,
    CountryKpi,
    GuestReview,
    HotelSummary,
    RoomType,
    RoomTypeKpi,
    RoomTypeSeasonKpi,
    Season,
    SeasonKpi,
)
from hotel_api.business.rules.numbers import round_half_up, safe_average, safe_pct, shares_pct
from hotel_api.business.rules.ranking import rank_descending
from hotel_api.business.rules.seasons import SEASON_ORDER, available_room_nights, days_in_year, season_days

_ZERO = Decimal("0.00")


def bookings_of_year(bookings: Iterable[Booking], year: int) -> list[Booking]:
    return [b for b in bookings if b.check_in_date.year == year]


def _totals(bookings: Sequence[Booking]) -> tuple[int, int, Decimal]:
    """(booking count, nights sold, revenue) of a set of bookings."""
    revenue = round_half_up(sum((b.price_dkk for b in bookings), _ZERO))
    return len(bookings), sum(b.days_rented for b in bookings), revenue


def stay_figures(booking_count: int, nights_sold: int, revenue: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    """A7: (ALOS = nights / bookings, ADR = revenue / nights, revenue per booking = revenue / bookings).

    Each rounded half-up to 2 decimals; 0.00 for an empty scope.
    """
    return (
        safe_average(nights_sold, booking_count),
        safe_average(revenue, nights_sold),
        safe_average(revenue, booking_count),
    )


def _stay_named(booking_count: int, nights_sold: int, revenue: Decimal) -> dict[str, Decimal]:
    keys = ("average_length_of_stay_nights", "average_daily_rate_dkk", "average_revenue_per_booking_dkk")
    return dict(zip(keys, stay_figures(booking_count, nights_sold, revenue)))


def reviews_of_year(reviews: Iterable[GuestReview], year: int) -> list[GuestReview]:
    return [r for r in reviews if r.stay_date.year == year]


def occupancy_rate_pct(nights_sold: int, available_nights: int) -> Decimal:
    """K1: nights sold / available room-nights x 100, 2 decimals; 0.00 without capacity."""
    return safe_pct(nights_sold, available_nights)


def satisfaction_figures(reviews: Sequence[GuestReview]) -> tuple[int, Decimal, Decimal]:
    """K3: (review count, mean rating, share of reviews rated 4 or 5 in percent). 0 / 0.00 / 0.00 if none."""
    count = len(reviews)
    mean = safe_average(sum(r.rating for r in reviews), count)
    satisfied = safe_pct(sum(1 for r in reviews if r.rating >= 4), count)
    return count, mean, satisfied


def _capacity_and_satisfaction(
    nights: int, available: int, reviews: Sequence[GuestReview]
) -> tuple[int, Decimal, int, Decimal, Decimal]:
    count, mean, satisfied = satisfaction_figures(reviews)
    return available, occupancy_rate_pct(nights, available), count, mean, satisfied


def _named(figures: tuple[int, Decimal, int, Decimal, Decimal]) -> dict[str, object]:
    keys = ("available_room_nights", "occupancy_rate_pct", "review_count", "average_satisfaction", "satisfied_share_pct")
    return dict(zip(keys, figures))


def hotel_summary(
    bookings: Iterable[Booking], reviews: Iterable[GuestReview], room_types: Sequence[RoomType], year: int
) -> HotelSummary:
    """Year totals: revenue (A6, K2), nights, occupancy over all rooms (K1), satisfaction (K3), ALOS / ADR (A7)."""
    count, nights, revenue = _totals(bookings_of_year(bookings, year))
    available = available_room_nights(sum(r.room_count for r in room_types), days_in_year(year))
    return HotelSummary(
        year=year,
        booking_count=count,
        nights_sold=nights,
        total_revenue_dkk=revenue,
        **_named(_capacity_and_satisfaction(nights, available, reviews_of_year(reviews, year))),
        **_stay_named(count, nights, revenue),
    )


def kpis_by_room_type(
    bookings: Iterable[Booking], reviews: Iterable[GuestReview], room_types: Sequence[RoomType], year: int
) -> list[RoomTypeKpi]:
    """One row per room type (always all of them), ranked by revenue (A4), revenue shares sum to 100.

    Also ALOS / ADR (A7). Occupancy uses the room type's own rooms x days in the year; satisfaction uses the reviews of that room type.
    """
    groups: dict[str, list[Booking]] = defaultdict(list)
    for booking in bookings_of_year(bookings, year):
        groups[booking.room_type].append(booking)
    review_groups: dict[str, list[GuestReview]] = defaultdict(list)
    for review in reviews_of_year(reviews, year):
        review_groups[review.room_type].append(review)

    rows = [(room_type, *_totals(groups.get(room_type.name, []))) for room_type in room_types]
    ranked = rank_descending(rows, value=lambda r: r[3], name=lambda r: r[0].name)
    shares = shares_pct([row[3] for _, row in ranked])
    return [
        RoomTypeKpi(
            year=year,
            revenue_rank=rank,
            room_type=room_type.name,
            room_count=room_type.room_count,
            booking_count=count,
            nights_sold=nights,
            revenue_dkk=revenue,
            revenue_share_pct=share,
            **_named(
                _capacity_and_satisfaction(
                    nights,
                    available_room_nights(room_type.room_count, days_in_year(year)),
                    review_groups.get(room_type.name, []),
                )
            ),
            **_stay_named(count, nights, revenue),
        )
        for (rank, (room_type, count, nights, revenue)), share in zip(ranked, shares)
    ]


def kpis_by_season(
    bookings: Iterable[Booking], reviews: Iterable[GuestReview], room_types: Sequence[RoomType], year: int
) -> list[SeasonKpi]:
    """Three rows in the order low, mid, high; revenue shares sum to 100.

    Also ALOS / ADR (A7). Occupancy uses all rooms x the season's days; a review belongs to the season of its stay date.
    """
    groups: dict[Season, list[Booking]] = defaultdict(list)
    for booking in bookings_of_year(bookings, year):
        groups[booking.season].append(booking)
    review_groups: dict[Season, list[GuestReview]] = defaultdict(list)
    for review in reviews_of_year(reviews, year):
        review_groups[review.season].append(review)
    total_rooms = sum(r.room_count for r in room_types)

    days = season_days(year)
    totals = [_totals(groups.get(season, [])) for season in SEASON_ORDER]
    shares = shares_pct([revenue for _, _, revenue in totals])
    return [
        SeasonKpi(
            year=year,
            season=season,
            season_days=days[season],
            booking_count=count,
            nights_sold=nights,
            revenue_dkk=revenue,
            revenue_share_pct=share,
            **_named(
                _capacity_and_satisfaction(
                    nights, available_room_nights(total_rooms, days[season]), review_groups.get(season, [])
                )
            ),
            **_stay_named(count, nights, revenue),
        )
        for season, (count, nights, revenue), share in zip(SEASON_ORDER, totals, shares)
    ]


def revenue_by_room_type_and_season(
    bookings: Iterable[Booking], room_types: Sequence[RoomType], year: int
) -> list[RoomTypeSeasonKpi]:
    """24 rows (A2): every room type in the given order, then low, mid, high."""
    groups: dict[tuple[str, Season], list[Booking]] = defaultdict(list)
    for booking in bookings_of_year(bookings, year):
        groups[(booking.room_type, booking.season)].append(booking)

    rows = []
    for room_type in room_types:
        for season in SEASON_ORDER:
            count, nights, revenue = _totals(groups.get((room_type.name, season), []))
            rows.append(RoomTypeSeasonKpi(year, room_type.name, season, count, nights, revenue))
    return rows


def revenue_by_country(bookings: Iterable[Booking], year: int) -> list[CountryKpi]:
    """One row per guest country that has bookings (A1 shape, A3, A5), ranked by revenue."""
    groups: dict[str, list[Booking]] = defaultdict(list)
    for booking in bookings_of_year(bookings, year):
        groups[booking.country].append(booking)

    rows = [(country, *_totals(group)) for country, group in groups.items()]
    ranked = rank_descending(rows, value=lambda r: r[3], name=lambda r: r[0])
    revenue_shares = shares_pct([row[3] for _, row in ranked])
    booking_shares = shares_pct([row[1] for _, row in ranked])
    return [
        CountryKpi(
            year=year,
            revenue_rank=rank,
            country=country,
            booking_count=count,
            booking_share_pct=booking_share,
            nights_sold=nights,
            revenue_dkk=revenue,
            revenue_share_pct=revenue_share,
        )
        for (rank, (country, count, nights, revenue)), revenue_share, booking_share in zip(
            ranked, revenue_shares, booking_shares
        )
    ]
