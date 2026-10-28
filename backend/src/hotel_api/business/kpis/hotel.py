"""Hotel KPIs, revenue part (K2, A2-A6; FR-006-FR-009; data-model §7). Pure functions, no I/O.

Each function takes bookings and the reporting `year`, and counts only bookings whose `check_in_date`
lies in that year: a booking (with its revenue and nights) belongs entirely to the season and year of
its check-in date (research R8). Rounding and shares follow `rules/numbers.py`; ranks follow
`rules/ranking.py`.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from decimal import Decimal

from hotel_api.business.domain.models import (
    Booking,
    CountryKpi,
    HotelRevenueSummary,
    RoomType,
    RoomTypeRevenue,
    RoomTypeSeasonKpi,
    Season,
    SeasonRevenue,
)
from hotel_api.business.rules.numbers import round_half_up, shares_pct
from hotel_api.business.rules.ranking import rank_descending
from hotel_api.business.rules.seasons import SEASON_ORDER, season_days

_ZERO = Decimal("0.00")


def bookings_of_year(bookings: Iterable[Booking], year: int) -> list[Booking]:
    return [b for b in bookings if b.check_in_date.year == year]


def _totals(bookings: Sequence[Booking]) -> tuple[int, int, Decimal]:
    """(booking count, nights sold, revenue) of a set of bookings."""
    revenue = round_half_up(sum((b.price_dkk for b in bookings), _ZERO))
    return len(bookings), sum(b.days_rented for b in bookings), revenue


def hotel_revenue_summary(bookings: Iterable[Booking], year: int) -> HotelRevenueSummary:
    """Total room revenue for the year (A6, K2) with booking count and nights sold."""
    count, nights, revenue = _totals(bookings_of_year(bookings, year))
    return HotelRevenueSummary(year, count, nights, revenue)


def revenue_by_room_type(
    bookings: Iterable[Booking], room_types: Sequence[RoomType], year: int
) -> list[RoomTypeRevenue]:
    """One row per room type (always all of them), ranked by revenue (A4), revenue shares sum to 100."""
    in_year = bookings_of_year(bookings, year)
    groups: dict[str, list[Booking]] = defaultdict(list)
    for booking in in_year:
        groups[booking.room_type].append(booking)

    rows = [(room_type, *_totals(groups.get(room_type.name, []))) for room_type in room_types]
    ranked = rank_descending(rows, value=lambda r: r[3], name=lambda r: r[0].name)
    shares = shares_pct([row[3] for _, row in ranked])
    return [
        RoomTypeRevenue(
            year=year,
            revenue_rank=rank,
            room_type=room_type.name,
            room_count=room_type.room_count,
            booking_count=count,
            nights_sold=nights,
            revenue_dkk=revenue,
            revenue_share_pct=share,
        )
        for (rank, (room_type, count, nights, revenue)), share in zip(ranked, shares)
    ]


def revenue_by_season(bookings: Iterable[Booking], year: int) -> list[SeasonRevenue]:
    """Three rows in the order low, mid, high; revenue shares sum to 100."""
    in_year = bookings_of_year(bookings, year)
    groups: dict[Season, list[Booking]] = defaultdict(list)
    for booking in in_year:
        groups[booking.season].append(booking)

    days = season_days(year)
    totals = [_totals(groups.get(season, [])) for season in SEASON_ORDER]
    shares = shares_pct([revenue for _, _, revenue in totals])
    return [
        SeasonRevenue(
            year=year,
            season=season,
            season_days=days[season],
            booking_count=count,
            nights_sold=nights,
            revenue_dkk=revenue,
            revenue_share_pct=share,
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
