// Booking page for reception. Renders what the API returns; it contains NO business rules:
// no season mapping, no price calculation and no validation of values (research R15).
import { ApiError, createBooking, deleteBooking, listBookings, listRoomTypes, replaceBooking } from "./api.js";

const PAGE_SIZE = 50;
const FIELDS = ["first_name", "family_name", "country", "room_type", "check_in_date", "days_rented", "price_dkk"];

const state = { roomTypes: [], bookings: [], editingId: null, visible: PAGE_SIZE };

const form = document.getElementById("booking-form");
const rows = document.getElementById("booking-rows");
const statusLine = document.getElementById("status");
const formTitle = document.getElementById("form-title");
const submitButton = document.getElementById("submit-button");
const cancelButton = document.getElementById("cancel-button");
const moreButton = document.getElementById("more-button");
const emptyNote = document.getElementById("empty");
const countLabel = document.getElementById("count");
const rateHint = document.getElementById("rate-hint");

const money = new Intl.NumberFormat("da-DK", { style: "currency", currency: "DKK" });
const number = new Intl.NumberFormat("da-DK");

// ---------- messages ----------

function say(text, kind) {
  statusLine.textContent = text;
  statusLine.className = "status" + (kind ? " " + kind : "");
}

function clearErrors() {
  form.querySelectorAll("[data-error-for]").forEach((el) => (el.textContent = ""));
  FIELDS.forEach((name) => form.elements[name].removeAttribute("aria-invalid"));
}

/** Show each API error next to its field; anything else goes to the form-level line. */
function showFieldErrors(errors, fallback) {
  clearErrors();
  let placed = 0;
  for (const { field, message } of errors) {
    const target = FIELDS.includes(field) ? form.querySelector(`[data-error-for="${field}"]`) : null;
    if (target) {
      target.textContent = (target.textContent ? target.textContent + " " : "") + message;
      form.elements[field].setAttribute("aria-invalid", "true");
      placed += 1;
    } else {
      const general = form.querySelector('[data-error-for="_form"]');
      general.textContent = (general.textContent ? general.textContent + " " : "") + `${field}: ${message}`;
      placed += 1;
    }
  }
  if (placed === 0) form.querySelector('[data-error-for="_form"]').textContent = fallback;
  const first = form.querySelector('[aria-invalid="true"]');
  if (first) first.focus();
}

// ---------- rendering ----------

function renderRoomTypes() {
  const select = form.elements.room_type;
  select.replaceChildren();
  for (const roomType of state.roomTypes) {
    const option = document.createElement("option");
    option.value = roomType.name;
    option.textContent = roomType.name;
    select.append(option);
  }
  showRateHint();
}

/** Shows the API's rate bands for the selected room type as information only. */
function showRateHint() {
  const roomType = state.roomTypes.find((r) => r.name === form.elements.room_type.value);
  if (!roomType) {
    rateHint.textContent = "";
    return;
  }
  const bands = roomType.rates.map(
    (r) => `${r.season} ${number.format(r.min_nightly_dkk)}–${number.format(r.max_nightly_dkk)}`,
  );
  rateHint.textContent = `Per night: ${bands.join(" · ")} DKK`;
}

function cell(text, className) {
  const td = document.createElement("td");
  td.textContent = text;
  if (className) td.className = className;
  return td;
}

function renderBookings() {
  rows.replaceChildren();
  const shown = state.bookings.slice(0, state.visible);
  for (const booking of shown) {
    const tr = document.createElement("tr");
    if (booking.id === state.editingId) tr.className = "editing";
    tr.append(
      cell(booking.id),
      cell(`${booking.first_name} ${booking.family_name}`),
      cell(booking.country),
      cell(booking.room_type),
      cell(booking.check_in_date),
      cell(booking.days_rented, "num"),
      cell(booking.season),
      cell(money.format(booking.price_dkk), "num"),
    );
    const actions = document.createElement("td");
    actions.className = "row-actions";
    const edit = document.createElement("button");
    edit.type = "button";
    edit.textContent = "Edit";
    edit.setAttribute("aria-label", `Edit booking ${booking.id}`);
    edit.addEventListener("click", () => startEdit(booking));
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "danger";
    remove.textContent = "Delete";
    remove.setAttribute("aria-label", `Delete booking ${booking.id}`);
    remove.addEventListener("click", () => removeBooking(booking));
    actions.append(edit, remove);
    tr.append(actions);
    rows.append(tr);
  }
  emptyNote.hidden = state.bookings.length > 0;
  moreButton.hidden = state.bookings.length <= state.visible;
  countLabel.textContent = state.bookings.length ? `(${state.bookings.length})` : "";
}

// ---------- form ----------

function formValues() {
  const text = (name) => form.elements[name].value;
  const numeric = (name) => (text(name).trim() === "" ? null : Number(text(name)));
  return {
    first_name: text("first_name"),
    family_name: text("family_name"),
    country: text("country"),
    room_type: text("room_type"),
    check_in_date: text("check_in_date"),
    days_rented: numeric("days_rented"),
    price_dkk: numeric("price_dkk"), // empty -> null -> the API uses the standard price
  };
}

function resetForm() {
  state.editingId = null;
  form.reset();
  clearErrors();
  formTitle.textContent = "New booking";
  submitButton.textContent = "Create booking";
  cancelButton.hidden = true;
  showRateHint();
}

function startEdit(booking) {
  state.editingId = booking.id;
  clearErrors();
  for (const name of FIELDS) form.elements[name].value = booking[name] ?? "";
  formTitle.textContent = `Edit booking ${booking.id}`;
  submitButton.textContent = "Save changes";
  cancelButton.hidden = false;
  showRateHint();
  say("");
  renderBookings();
  form.elements.first_name.focus();
}

function busy(isBusy) {
  submitButton.disabled = isBusy;
}

async function reload() {
  state.bookings = await listBookings();
  renderBookings();
}

async function onSubmit(event) {
  event.preventDefault();
  clearErrors();
  say("");
  busy(true);
  const editing = state.editingId;
  try {
    const saved = editing === null ? await createBooking(formValues()) : await replaceBooking(editing, formValues());
    resetForm();
    await reload();
    say(editing === null ? `Booking ${saved.id} created.` : `Booking ${saved.id} saved.`, "ok");
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    if (error.status === 400 || error.status === 422) {
      showFieldErrors(error.fieldErrors, error.message);
    } else if (error.status === 404) {
      say(`${error.message} The list has been refreshed.`, "error");
      resetForm();
      await reload().catch(() => {});
    } else {
      say(error.message, "error");
    }
  } finally {
    busy(false);
  }
}

async function removeBooking(booking) {
  const who = `${booking.first_name} ${booking.family_name}`;
  if (!window.confirm(`Delete booking ${booking.id} for ${who}?`)) return;
  say("");
  try {
    await deleteBooking(booking.id);
    if (state.editingId === booking.id) resetForm();
    await reload();
    say(`Booking ${booking.id} deleted.`, "ok");
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    say(error.message, "error");
    if (error.status === 404) await reload().catch(() => {});
  }
}

// ---------- wiring ----------

form.addEventListener("submit", onSubmit);
cancelButton.addEventListener("click", () => {
  resetForm();
  renderBookings();
});
moreButton.addEventListener("click", () => {
  state.visible += PAGE_SIZE;
  renderBookings();
});
form.elements.room_type.addEventListener("change", showRateHint);

// A different room type, check-in date or number of nights means a different price: clear the field so
// the API recalculates the standard price (unless the user types one).
for (const name of ["room_type", "check_in_date", "days_rented"]) {
  form.elements[name].addEventListener("change", () => {
    form.elements.price_dkk.value = "";
  });
}

async function init() {
  try {
    state.roomTypes = await listRoomTypes();
    renderRoomTypes();
    await reload();
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    say(error.message, "error");
  }
}

init();
