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

export const listRoomTypes = () => request("GET", "/room-types").then((r) => r.items);
export const listBookings = () => request("GET", "/bookings").then((r) => r.items);
export const createBooking = (booking) => request("POST", "/bookings", booking);
export const replaceBooking = (id, booking) => request("PUT", `/bookings/${id}`, booking);
export const deleteBooking = (id) => request("DELETE", `/bookings/${id}`);
