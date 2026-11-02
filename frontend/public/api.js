// Thin fetch wrappers for the REST API (same origin: nginx proxies /api/ to the backend).
// No business rules here: the API derives season and price and validates every field.

const BASE = "/api/v1";

/** An error response from the API. `problem` is the parsed RFC 9457 body (with `errors[]`) when there is one. */
export class ApiError extends Error {
  constructor(status, problem) {
    super((problem && (problem.detail || problem.title)) || `Request failed (${status})`);
    this.status = status;
    this.problem = problem;
  }

  /** `[{field, message}]` for 400/422 responses, else an empty list. */
  get fieldErrors() {
    return (this.problem && this.problem.errors) || [];
  }
}

async function request(method, path, body) {
  let response;
  try {
    response = await fetch(BASE + path, {
      method,
      headers: body === undefined ? {} : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (cause) {
    throw new ApiError(0, { title: "Network error", detail: "The server cannot be reached. Try again shortly." });
  }
  if (response.status === 204) return null;
  const type = response.headers.get("content-type") || "";
  let data = null;
  if (type.includes("json")) {
    try {
      data = await response.json();
    } catch (cause) {
      data = null;
    }
  }
  if (!response.ok) throw new ApiError(response.status, data);
  return data;
}

function queryString(filters = {}) {
  const query = new URLSearchParams();
  for (const [name, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== "") query.set(name, value);
  }
  const text = query.toString();
  return text ? "?" + text : "";
}

export const listRoomTypes = () => request("GET", "/room-types").then((r) => r.items);
export const listBookings = () => request("GET", "/bookings").then((r) => r.items);
export const createBooking = (booking) => request("POST", "/bookings", booking);
export const replaceBooking = (id, booking) => request("PUT", `/bookings/${id}`, booking);
export const deleteBooking = (id) => request("DELETE", `/bookings/${id}`);

/** Hotel KPI summary (`GET /api/v1/kpis/hotel/summary`). */
export const getHotelSummary = (filters = {}) => request("GET", `/kpis/hotel/summary${queryString(filters)}`);

/**
 * Hotel KPI breakdowns calculated by the API (`Hotel Analytics`). `kind` is one of `by-room-type`, `by-season`,
 * `by-room-type-and-season` or `by-country`; `filters` holds the optional year, season, room_type and country.
 */
export function getHotelKpis(kind, filters = {}) {
  return request("GET", `/kpis/hotel/${kind}${queryString(filters)}`).then((r) =>
    r && r.items !== undefined ? r.items : r,
  );
}

/** Cocktail bar KPI summary (`GET /api/v1/kpis/bar/summary`). */
export const getBarSummary = (filters = {}) => request("GET", `/kpis/bar/summary${queryString(filters)}`);

/**
 * Cocktail bar KPI breakdowns calculated by the API (`Hotel Analytics`). `kind` is one of `by-drink`,
 * `by-category` or `by-price-tier`; `filters` holds the optional year, category and price_tier.
 */
export function getBarKpis(kind, filters = {}) {
  return request("GET", `/kpis/bar/${kind}${queryString(filters)}`).then((r) =>
    r && r.items !== undefined ? r.items : r,
  );
}
