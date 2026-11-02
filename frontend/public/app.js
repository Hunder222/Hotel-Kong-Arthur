// Booking page for reception and Hotel Analytics dashboard (FR-022). The API stays the only authority:
// it derives the season, prices the stay, validates every field and calculates every KPI (research R15).
// The live price preview and the two price fields use price-preview.js, a display-only mirror of the
// season table and the standard price (FR-018, FR-019).
import {
  ApiError,
  createBooking,
  deleteBooking,
  getBarKpis,
  getBarSummary,
  getHotelKpis,
  getHotelSummary,
  listBookings,
  listRoomTypes,
  replaceBooking,
} from "./api.js";
import { nightlyFromTotal, standardPreview, totalFromNightly } from "./price-preview.js";

const PAGE_SIZE = 50;
const FIELDS = [
  "first_name", "family_name", "country", "room_type", "check_in_date", "days_rented", "price_dkk", "price_per_night_dkk",
];

// priceMode: which manual price field is in use, only one at a time (FR-019): "total", "nightly" or null (standard price).
const state = { roomTypes: [], bookings: [], editingId: null, visible: PAGE_SIZE, priceMode: null };

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
const totalInput = form.elements.price_dkk;
const nightlyInput = form.elements.price_per_night_dkk;
const clearPriceButton = document.getElementById("clear-price");
const previewBox = document.getElementById("price-preview");
const bannerText = document.getElementById("edit-banner-text");
const bannerCancel = document.getElementById("banner-cancel");

const analyticsForm = document.getElementById("analytics-filters");
const barForm = document.getElementById("bar-filters");
const analyticsStatus = document.getElementById("analytics-status");
const metricRevenue = document.getElementById("metric-revenue");
const metricBookings = document.getElementById("metric-bookings");
const metricNights = document.getElementById("metric-nights");
const metricAvailableNights = document.getElementById("metric-available-nights");
const metricOccupancy = document.getElementById("metric-occupancy");
const metricReviews = document.getElementById("metric-reviews");
const metricSatisfaction = document.getElementById("metric-satisfaction");
const metricSatisfiedShare = document.getElementById("metric-satisfied-share");
const roomTypeRows = document.getElementById("room-type-rows");
const seasonRows = document.getElementById("season-rows");
const roomTypeSeasonRows = document.getElementById("room-type-season-rows");
const countryRows = document.getElementById("country-rows");
const countryEmpty = document.getElementById("country-empty");

const metricBarRevenue = document.getElementById("metric-bar-revenue");
const metricBarUnits = document.getElementById("metric-bar-units");
const metricBarDrinks = document.getElementById("metric-bar-drinks");
const barCategoryRows = document.getElementById("bar-category-rows");
const barDrinkRows = document.getElementById("bar-drink-rows");
const barDrinkEmpty = document.getElementById("bar-drink-empty");

const money = new Intl.NumberFormat("da-DK", { style: "currency", currency: "DKK" });
const number = new Intl.NumberFormat("da-DK");
const decimalFmt = new Intl.NumberFormat("da-DK", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const pct = (value) => `${decimalFmt.format(value)} %`;
const rating = (count, avg) => (count > 0 ? `${decimalFmt.format(avg)} / 5` : "–");

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
  refreshPrice();
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

// ---------- Hotel Analytics dashboard (FR-022) ----------

function populateSelect(select, allLabel, values) {
  const current = select.value;
  select.replaceChildren();
  const first = document.createElement("option");
  first.value = "";
  first.textContent = allLabel;
  select.append(first);
  for (const value of values) {
    const option = document.createElement("option");
    option.value = String(value);
    option.textContent = String(value);
    select.append(option);
  }
  if (values.map(String).includes(current)) select.value = current;
}

function updateAnalyticsFilterOptions(roomTypes, bookings) {
  if (!analyticsForm) return;
  const years = [...new Set([2026, ...bookings.map((b) => b.year)])].sort((a, b) => a - b);
  const countries = [...new Set(bookings.map((b) => b.country))].sort((a, b) => a.localeCompare(b));
  populateSelect(analyticsForm.elements.year, "All years", years);
  populateSelect(
    analyticsForm.elements.room_type,
    "All room types",
    roomTypes.map((r) => r.name),
  );
  populateSelect(analyticsForm.elements.country, "All countries", countries);
}

function currentAnalyticsFilters() {
  if (!analyticsForm) return {};
  return {
    year: analyticsForm.elements.year.value || "all",
    season: analyticsForm.elements.season.value || undefined,
    room_type: analyticsForm.elements.room_type.value || undefined,
    country: analyticsForm.elements.country.value || undefined,
  };
}

function currentBarFilters() {
  return {
    year: (analyticsForm && analyticsForm.elements.year.value) || "all",
    category: (barForm && barForm.elements.category.value) || undefined,
  };
}

function renderHotelAnalytics(summary, byRoomType, bySeason, byRoomTypeSeason, byCountry) {
  metricRevenue.textContent = money.format(summary.total_revenue_dkk);
  metricBookings.textContent = number.format(summary.booking_count);
  metricNights.textContent = number.format(summary.nights_sold);
  metricAvailableNights.textContent = number.format(summary.available_room_nights);
  metricOccupancy.textContent = pct(summary.occupancy_rate_pct);
  metricReviews.textContent = number.format(summary.review_count);
  metricSatisfaction.textContent = rating(summary.review_count, summary.average_satisfaction);
  metricSatisfiedShare.textContent = summary.review_count > 0 ? pct(summary.satisfied_share_pct) : "–";

  roomTypeRows.replaceChildren();
  for (const row of byRoomType) {
    const tr = document.createElement("tr");
    tr.append(
      cell(row.revenue_rank, "num"),
      cell(row.room_type),
      cell(number.format(row.room_count), "num"),
      cell(number.format(row.booking_count), "num"),
      cell(number.format(row.nights_sold), "num"),
      cell(number.format(row.available_room_nights), "num"),
      cell(pct(row.occupancy_rate_pct), "num"),
      cell(money.format(row.revenue_dkk), "num"),
      cell(pct(row.revenue_share_pct), "num"),
      cell(number.format(row.review_count), "num"),
      cell(rating(row.review_count, row.average_satisfaction), "num"),
      cell(row.review_count > 0 ? pct(row.satisfied_share_pct) : "–", "num"),
    );
    roomTypeRows.append(tr);
  }

  seasonRows.replaceChildren();
  for (const row of bySeason) {
    const tr = document.createElement("tr");
    tr.append(
      cell(row.season),
      cell(number.format(row.season_days), "num"),
      cell(number.format(row.booking_count), "num"),
      cell(number.format(row.nights_sold), "num"),
      cell(number.format(row.available_room_nights), "num"),
      cell(pct(row.occupancy_rate_pct), "num"),
      cell(money.format(row.revenue_dkk), "num"),
      cell(pct(row.revenue_share_pct), "num"),
      cell(number.format(row.review_count), "num"),
      cell(rating(row.review_count, row.average_satisfaction), "num"),
      cell(row.review_count > 0 ? pct(row.satisfied_share_pct) : "–", "num"),
    );
    seasonRows.append(tr);
  }

  roomTypeSeasonRows.replaceChildren();
  const byTypeMap = new Map();
  for (const cellRow of byRoomTypeSeason) {
    if (!byTypeMap.has(cellRow.room_type)) byTypeMap.set(cellRow.room_type, {});
    byTypeMap.get(cellRow.room_type)[cellRow.season] = cellRow;
  }
  for (const [roomTypeName, seasonsObj] of byTypeMap.entries()) {
    const tr = document.createElement("tr");
    tr.append(
      cell(roomTypeName),
      cell(seasonsObj.low ? money.format(seasonsObj.low.revenue_dkk) : "–", "num"),
      cell(seasonsObj.mid ? money.format(seasonsObj.mid.revenue_dkk) : "–", "num"),
      cell(seasonsObj.high ? money.format(seasonsObj.high.revenue_dkk) : "–", "num"),
    );
    roomTypeSeasonRows.append(tr);
  }

  countryRows.replaceChildren();
  for (const row of byCountry) {
    const tr = document.createElement("tr");
    tr.append(
      cell(row.revenue_rank, "num"),
      cell(row.country),
      cell(number.format(row.booking_count), "num"),
      cell(pct(row.booking_share_pct), "num"),
      cell(number.format(row.nights_sold), "num"),
      cell(money.format(row.revenue_dkk), "num"),
      cell(pct(row.revenue_share_pct), "num"),
    );
    countryRows.append(tr);
  }
  countryEmpty.hidden = byCountry.length > 0;
}

function renderBarAnalytics(barSummary, barByCategory, barByDrink) {
  if (!metricBarRevenue) return;
  metricBarRevenue.textContent = money.format(barSummary.total_revenue_dkk);
  metricBarUnits.textContent = number.format(barSummary.units_sold);
  metricBarDrinks.textContent = number.format(barSummary.drink_count);

  barCategoryRows.replaceChildren();
  for (const row of barByCategory) {
    const tr = document.createElement("tr");
    tr.append(
      cell(row.category),
      cell(number.format(row.drink_count), "num"),
      cell(number.format(row.units_sold), "num"),
      cell(pct(row.unit_share_pct), "num"),
      cell(money.format(row.revenue_dkk), "num"),
      cell(pct(row.revenue_share_pct), "num"),
    );
    barCategoryRows.append(tr);
  }

  barDrinkRows.replaceChildren();
  for (const row of barByDrink) {
    const tr = document.createElement("tr");
    tr.append(
      cell(row.revenue_rank, "num"),
      cell(row.drink_name),
      cell(row.category),
      cell(row.price_tier),
      cell(money.format(row.unit_price_dkk), "num"),
      cell(number.format(row.units_sold), "num"),
      cell(row.units_rank, "num"),
      cell(money.format(row.revenue_dkk), "num"),
    );
    barDrinkRows.append(tr);
  }
  barDrinkEmpty.hidden = barByDrink.length > 0;
}

async function loadAnalytics() {
  if (!analyticsForm) return;
  analyticsStatus.textContent = "";
  analyticsStatus.className = "status";
  const hotelFilters = currentAnalyticsFilters();
  const barFilters = currentBarFilters();
  try {
    const [
      summary,
      byRoomType,
      bySeason,
      byRoomTypeSeason,
      byCountry,
      barSummary,
      barByCategory,
      barByDrink,
    ] = await Promise.all([
      getHotelSummary(hotelFilters),
      getHotelKpis("by-room-type", hotelFilters),
      getHotelKpis("by-season", hotelFilters),
      getHotelKpis("by-room-type-and-season", hotelFilters),
      getHotelKpis("by-country", hotelFilters),
      getBarSummary(barFilters),
      getBarKpis("by-category", barFilters),
      getBarKpis("by-drink", barFilters),
    ]);
    renderHotelAnalytics(summary, byRoomType, bySeason, byRoomTypeSeason, byCountry);
    renderBarAnalytics(barSummary, barByCategory, barByDrink);
  } catch (error) {
    analyticsStatus.textContent = error instanceof ApiError ? error.message : "Failed to load analytics.";
    analyticsStatus.className = "status error";
  }
}

function refreshAnalytics(roomTypes, bookings) {
  updateAnalyticsFilterOptions(roomTypes, bookings);
  loadAnalytics();
}

// ---------- price fields and live preview (FR-018, FR-019) ----------

const amount = (input) => (input.value.trim() === "" ? null : Number(input.value));

/** The number of nights as a whole number from 1, or null while the field is empty or not usable. */
function nightsValue() {
  const nights = amount(form.elements.days_rented);
  return nights !== null && Number.isInteger(nights) && nights >= 1 ? nights : null;
}

/** Back to the standard price: both price fields empty and unlocked. */
function clearManualPrice() {
  state.priceMode = null;
  totalInput.value = "";
  nightlyInput.value = "";
}

/** Typing in one price field makes it the manual price (FR-019); the other then shows the calculated value. */
function onPriceInput(kind) {
  const typed = kind === "total" ? totalInput : nightlyInput;
  if (typed.value.trim() === "" && !typed.validity.badInput) clearManualPrice();
  else state.priceMode = kind;
  refreshPrice();
}

/** Fills and locks the field that is not in use with the calculated counterpart of the one that is. */
function syncPriceFields() {
  const nights = nightsValue();
  if (state.priceMode === "total") {
    const total = amount(totalInput);
    nightlyInput.value = nights && Number.isFinite(total) ? String(nightlyFromTotal(total, nights)) : "";
  } else if (state.priceMode === "nightly") {
    const nightly = amount(nightlyInput);
    totalInput.value = nights && Number.isFinite(nightly) ? String(totalFromNightly(nightly, nights)) : "";
  }
  totalInput.readOnly = state.priceMode === "nightly";
  nightlyInput.readOnly = state.priceMode === "total";
  totalInput.classList.toggle("computed", state.priceMode === "nightly");
  nightlyInput.classList.toggle("computed", state.priceMode === "total");
  clearPriceButton.hidden = state.priceMode === null;
}

/** The price breakdown under the price fields: standard rate, nights and standard total, then the typed price. */
function renderPreview() {
  const roomType = state.roomTypes.find((r) => r.name === form.elements.room_type.value);
  const preview = standardPreview(roomType, form.elements.check_in_date.value, nightsValue());
  previewBox.replaceChildren();
  if (!preview) {
    const note = document.createElement("p");
    note.className = "preview-empty";
    note.textContent = "Choose room type, check-in date and nights to see the price.";
    previewBox.append(note);
    return;
  }
  const list = document.createElement("dl");
  list.className = "preview-list";
  const line = (label, value, className) => {
    const row = document.createElement("div");
    if (className) row.className = className;
    const term = document.createElement("dt");
    term.textContent = label;
    const detail = document.createElement("dd");
    detail.textContent = value;
    row.append(term, detail);
    list.append(row);
  };
  const { season, rate } = preview;
  line("Season", season[0].toUpperCase() + season.slice(1));
  line("Standard rate per night", money.format(rate.standard_nightly_dkk));
  line("Nights", number.format(preview.nights));
  line("Standard total", money.format(preview.total), state.priceMode ? undefined : "total");
  if (state.priceMode) {
    const nightly = amount(nightlyInput);
    const total = amount(totalInput);
    line("Your price per night", Number.isFinite(nightly) ? money.format(nightly) : "–");
    line("Your total", Number.isFinite(total) ? money.format(total) : "–", "total");
  }
  const band = document.createElement("p");
  band.className = "hint";
  band.textContent =
    `Allowed per night in ${season} season: ${number.format(rate.min_nightly_dkk)}–` +
    `${number.format(rate.max_nightly_dkk)} DKK. The server checks the price when you save.`;
  previewBox.append(list, band);
}

function refreshPrice() {
  syncPriceFields();
  renderPreview();
}

/** Edit mode (FR-020): a banner, another colour scheme for page and form, and a clear way back. */
function setEditMode(on, booking) {
  document.body.classList.toggle("edit-mode", on);
  bannerText.textContent = on
    ? `Editing booking ${booking.id} (${booking.first_name} ${booking.family_name}). Nothing changes until you press “Save changes”.`
    : "";
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
    // Only the price field in use is sent; with neither, the API uses the standard price.
    price_dkk: state.priceMode === "total" ? numeric("price_dkk") : null,
    price_per_night_dkk: state.priceMode === "nightly" ? numeric("price_per_night_dkk") : null,
  };
}

function resetForm() {
  state.editingId = null;
  state.priceMode = null;
  form.reset();
  clearErrors();
  formTitle.textContent = "New booking";
  submitButton.textContent = "Create booking";
  cancelButton.hidden = true;
  setEditMode(false);
  showRateHint();
  refreshPrice();
}

function startEdit(booking) {
  state.editingId = booking.id;
  clearErrors();
  for (const name of FIELDS) form.elements[name].value = booking[name] ?? "";
  state.priceMode = "total"; // a saved booking carries its total; the price per night is worked out from it
  formTitle.textContent = `Edit booking ${booking.id}`;
  submitButton.textContent = "Save changes";
  cancelButton.hidden = false;
  setEditMode(true, booking);
  showRateHint();
  refreshPrice();
  say("");
  renderBookings();
  form.scrollIntoView({ block: "start" });
  form.elements.first_name.focus();
}

function busy(isBusy) {
  submitButton.disabled = isBusy;
}

async function reload() {
  state.bookings = await listBookings();
  renderBookings();
  refreshAnalytics(state.roomTypes, state.bookings); // fire and forget: analytics report their own errors
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
if (analyticsForm) {
  analyticsForm.addEventListener("change", () => loadAnalytics());
}
if (barForm) {
  barForm.addEventListener("change", () => loadAnalytics());
}

// Another room type or check-in date means another rate band, so a typed price no longer applies: clear it and
// let the API price the stay. Another number of nights keeps a fixed price per night (the total follows) but
// not a typed total. In every case the preview follows what is typed.
for (const name of ["room_type", "check_in_date", "days_rented"]) {
  for (const type of ["input", "change"]) {
    form.elements[name].addEventListener(type, () => {
      if (name !== "days_rented" || state.priceMode === "total") clearManualPrice();
      refreshPrice();
    });
  }
}
totalInput.addEventListener("input", () => onPriceInput("total"));
nightlyInput.addEventListener("input", () => onPriceInput("nightly"));
clearPriceButton.addEventListener("click", () => {
  clearManualPrice();
  refreshPrice();
  totalInput.focus();
});
bannerCancel.addEventListener("click", () => {
  resetForm();
  renderBookings();
});

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
