"""Hotel KPI calculations (data-model §7): revenue, shares, ranks, occupancy and satisfaction (A1-A7, K1-K3).

Pure functions over already-loaded bookings, reviews and room types. The caller filters the records
to the requested scope with `filter_bookings` / `filter_reviews` and passes the room types, seasons and
calendar years in scope, which is what the available room-nights (K1) are counted over.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Iterable, Sequence

from hotel_api.business.domain.models import (
    Booking,
    CountryKpi,
    GuestReview,
    HotelFilters,
    HotelSummary,
    ReportYear,
    RoomType,
    RoomTypeKpi,
    RoomTypeSeasonKpi,
    SatisfactionMetrics,
    Season,
    SeasonKpi,
    StayMetrics,
)
from hotel_api.business.rules.numbers import largest_remainder_shares, round_half_up, safe_ratio
from hotel_api.business.rules.ranking import competition_ranks
from hotel_api.business.rules.seasons import SEASON_ORDER, days_in_season

ZERO = Decimal("0.00")


# ---------- scope ----------


def filter_bookings(bookings: Iterable[Booking], filters: HotelFilters) -> list[Booking]:
    return [
        b
        for b in bookings
        if (filters.year == "all" or b.year == filters.year)
        and (filters.season is None or b.season is filters.season)
        and (filters.room_type is None or b.room_type == filters.room_type)
        and (filters.country is None or b.country == filters.country)
    ]


def filter_reviews(
    reviews: Iterable[GuestReview],
    filters: HotelFilters,
    country_booking_ids: frozenset[int] | None = None,
) -> list[GuestReview]:
    """Reviews in scope. A `country` filter keeps the reviews of that country's bookings (`country_booking_ids`)."""
    return [
        r
        for r in reviews
        if (filters.year == "all" or r.year == filters.year)
        and (filters.season is None or r.season is filters.season)
        and (filters.room_type is None or r.room_type == filters.room_type)
        and (country_booking_ids is None or (r.booking_id is not None and r.booking_id in country_booking_ids))
    ]


def years_in_scope(year: ReportYear, recorded_years: Iterable[int]) -> list[int]:
    """One year, or for `all` every calendar year from the first to the last recorded year."""
    if year != "all":
        return [year]
    recorded = sorted(set(recorded_years))
    return list(range(recorded[0], recorded[-1] + 1)) if recorded else []


def available_room_nights(rooms: int, years: Sequence[int], seasons: Sequence[Season]) -> int:
    """K1 denominator: rooms in scope x calendar days of the seasons in scope, over the years in scope."""
    return rooms * sum(days_in_season(y, s) for y in years for s in seasons)


# ---------- building blocks ----------


def total_revenue(bookings: Iterable[Booking]) -> Decimal:
    """A6 / K2: sum of `price_dkk`."""
    return sum((b.price_dkk for b in bookings), ZERO)


def stay_metrics(bookings: Sequence[Booking]) -> StayMetrics:
    """Booking count, nights, revenue, ALOS, ADR and revenue per booking (A7); zero denominators give 0.00."""
    count = len(bookings)
    nights = sum(b.days_rented for b in bookings)
    revenue = round_half_up(total_revenue(bookings))
    return StayMetrics(
        booking_count=count,
        nights_sold=nights,
        revenue_dkk=revenue,
        average_length_of_stay_nights=safe_ratio(nights, count),
        average_daily_rate_dkk=safe_ratio(revenue, nights),
        average_revenue_per_booking_dkk=safe_ratio(revenue, count),
    )


def satisfaction_metrics(reviews: Sequence[GuestReview]) -> SatisfactionMetrics:
    """K3: mean rating and the share of ratings >= 4; 0.00 without reviews."""
    count = len(reviews)
    return SatisfactionMetrics(
        review_count=count,
        average_satisfaction=safe_ratio(sum(r.rating for r in reviews), count),
        satisfied_share_pct=safe_ratio(sum(1 for r in reviews if r.rating >= 4), count, 100),
    )


def occupancy_rate_pct(nights_sold: int, available_nights: int) -> Decimal:
    """K1: nights sold / available room-nights x 100."""
    return safe_ratio(nights_sold, available_nights, 100)


# ---------- summary & breakdowns ----------


def hotel_summary(
    bookings: Sequence[Booking],
    reviews: Sequence[GuestReview],
    room_types: Sequence[RoomType],
    seasons: Sequence[Season],
    years: Sequence[int],
    year: ReportYear,
) -> HotelSummary:
    """Overall hotel KPI summary (A6, K1, K2, K3, A7) for the requested scope."""
    stay = stay_metrics(bookings)
    rooms = sum(rt.room_count for rt in room_types)
    available = available_room_nights(rooms, years, seasons)
    return HotelSummary(
        year=year,
        stay=stay,
        available_room_nights=available,
        occupancy_rate_pct=occupancy_rate_pct(stay.nights_sold, available),
        satisfaction=satisfaction_metrics(reviews),
    )


def room_type_kpis(
    bookings: Sequence[Booking],
    reviews: Sequence[GuestReview],
    room_types: Sequence[RoomType],
    seasons: Sequence[Season],
    years: Sequence[int],
    year: ReportYear,
) -> list[RoomTypeKpi]:
    """A4: one row per room type in scope, ranked by revenue (ties alphabetical)."""
    stays = {rt.name: stay_metrics([b for b in bookings if b.room_type == rt.name]) for rt in room_types}
    shares = dict(zip(stays, largest_remainder_shares([s.revenue_dkk for s in stays.values()])))
    ranked = competition_ranks(list(room_types), key=lambda rt: stays[rt.name].revenue_dkk, tie_key=lambda rt: rt.name)
    rows = []
    for rank, rt in ranked:
        stay = stays[rt.name]
        available = available_room_nights(rt.room_count, years, seasons)
        rows.append(
            RoomTypeKpi(
                year=year,
                revenue_rank=rank,
                room_type=rt.name,
                room_count=rt.room_count,
                stay=stay,
                revenue_share_pct=shares[rt.name],
                available_room_nights=available,
                occupancy_rate_pct=occupancy_rate_pct(stay.nights_sold, available),
                satisfaction=satisfaction_metrics([r for r in reviews if r.room_type == rt.name]),
            )
        )
    return rows


def season_kpis(
    bookings: Sequence[Booking],
    reviews: Sequence[GuestReview],
    room_types: Sequence[RoomType],
    seasons: Sequence[Season],
    years: Sequence[int],
    year: ReportYear,
) -> list[SeasonKpi]:
    """One row per season in scope in canonical order (low, mid, high)."""
    ordered = [s for s in SEASON_ORDER if s in seasons]
    stays = {s: stay_metrics([b for b in bookings if b.season is s]) for s in ordered}
    shares = dict(zip(ordered, largest_remainder_shares([stays[s].revenue_dkk for s in ordered])))
    rooms = sum(rt.room_count for rt in room_types)
    rows = []
    for season in ordered:
        stay = stays[season]
        available = available_room_nights(rooms, years, [season])
        rows.append(
            SeasonKpi(
                year=year,
                season=season,
                season_days=sum(days_in_season(y, season) for y in years),
                stay=stay,
                revenue_share_pct=shares[season],
                available_room_nights=available,
                occupancy_rate_pct=occupancy_rate_pct(stay.nights_sold, available),
                satisfaction=satisfaction_metrics([r for r in reviews if r.season is season]),
            )
        )
    return rows


def room_type_season_kpis(
    bookings: Sequence[Booking],
    room_types: Sequence[RoomType],
    seasons: Sequence[Season],
    years: Sequence[int],
    year: ReportYear,
) -> list[RoomTypeSeasonKpi]:
    """A2: one row per room type x season in scope (canonical room type order, then low, mid, high)."""
    ordered = [s for s in SEASON_ORDER if s in seasons]
    cells: dict[tuple[str, Season], list[Booking]] = defaultdict(list)
    for b in bookings:
        cells[(b.room_type, b.season)].append(b)
    rows = []
    for rt in room_types:
        for season in ordered:
            stay = stay_metrics(cells[(rt.name, season)])
            available = available_room_nights(rt.room_count, years, [season])
            rows.append(
                RoomTypeSeasonKpi(
                    year=year,
                    room_type=rt.name,
                    season=season,
                    room_count=rt.room_count,
                    season_days=sum(days_in_season(y, season) for y in years),
                    stay=stay,
                    available_room_nights=available,
                    occupancy_rate_pct=occupancy_rate_pct(stay.nights_sold, available),
                )
            )
    return rows


def country_kpis(bookings: Sequence[Booking], year: ReportYear) -> list[CountryKpi]:
    """A1 / A3 / A5: one row per guest country with bookings, ranked by revenue (ties alphabetical)."""
    by_country: dict[str, list[Booking]] = defaultdict(list)
    for b in bookings:
        by_country[b.country].append(b)
    countries = sorted(by_country)
    counts = [len(by_country[c]) for c in countries]
    revenues = [round_half_up(total_revenue(by_country[c])) for c in countries]
    booking_share = dict(zip(countries, largest_remainder_shares(counts)))
    revenue_share = dict(zip(countries, largest_remainder_shares(revenues)))
    revenue = dict(zip(countries, revenues))
    ranked = competition_ranks(countries, key=lambda c: revenue[c], tie_key=lambda c: c)
    return [
        CountryKpi(
            year=year,
            revenue_rank=rank,
            country=country,
            booking_count=len(by_country[country]),
            booking_share_pct=booking_share[country],
            nights_sold=sum(b.days_rented for b in by_country[country]),
            revenue_dkk=revenue[country],
            revenue_share_pct=revenue_share[country],
        )
        for rank, country in ranked
    ]
