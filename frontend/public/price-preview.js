// Display-only mirror of two backend rules, used for the live price preview and the two price fields
// (FR-018, FR-019):
//   - the season of a check-in date (backend: business/rules/seasons.py), and
//   - the standard price: the season's standard nightly rate x nights (backend: business/rules/pricing.py).
// The API stays the only authority. When a booking is saved it re-derives the season, prices the stay and
// validates every value, so nothing calculated here is a rule's outcome. The architecture test
// backend/tests/architecture/test_frontend_price_mirror.py fails if SEASON_BY_MONTH drifts from seasons.py.

// January first. Keep it on one line of plain strings: the architecture test reads it.
export const SEASON_BY_MONTH = ["low", "low", "mid", "mid", "mid", "high", "high", "high", "mid", "mid", "low", "high"];

const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/;

/** Rounds to 2 decimals the way money is shown (half up, nudged so binary fractions do not round down). */
export function round2(value) {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

/** `low`, `mid` or `high` for an ISO date (YYYY-MM-DD), else null. A stay belongs to the season of its check-in date. */
export function seasonOf(isoDate) {
  const match = ISO_DATE.exec(isoDate || "");
  if (!match) return null;
  const month = Number(match[2]);
  return month >= 1 && month <= 12 ? SEASON_BY_MONTH[month - 1] : null;
}

/** The rate band of `roomType` (an item of GET /room-types) in `season`, else null. */
export function rateFor(roomType, season) {
  return (roomType && roomType.rates.find((rate) => rate.season === season)) || null;
}

/** What a stay costs at the standard price, or null until room type, check-in date and nights are all usable. */
export function standardPreview(roomType, isoDate, nights) {
  const season = seasonOf(isoDate);
  const rate = season && rateFor(roomType, season);
  if (!rate || !Number.isInteger(nights) || nights < 1) return null;
  return { season, rate, nights, total: round2(rate.standard_nightly_dkk * nights) };
}

/** The total of a stay at a fixed price per night. */
export const totalFromNightly = (nightly, nights) => round2(nightly * nights);

/** The price per night that gives `total` over `nights`. Shown for convenience: the API only gets what was typed. */
export const nightlyFromTotal = (total, nights) => round2(total / nights);
