// Booking page for reception and Hotel Analytics dashboard (FR-022, Phase 9 Revision).
// The API stays the only authority: it derives the season, prices the stay, validates every field
// and calculates every KPI (research R15). The live price preview and the two price fields use
// price-preview.js, a display-only mirror of the season table and the standard price (FR-018, FR-019).
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

// Navigation state: primary view ('bookings' | 'analytics') and analytics subview ('hotel' | 'bar')
const navState = {
  view: "bookings",
  analyticsSubView: "hotel",
};

// Cached revenue numbers for the top executive summary card (TODOS.md)
const revenueState = {
  roomRevenue: 0,
  roomBookings: 0,
  barRevenue: 0,
  barUnits: 0,
};

// priceMode: which manual price field is in use, only one at a time (FR-019): "total", "nightly" or null (standard price).
const state = { roomTypes: [], bookings: [], editingId: null, visible: PAGE_SIZE, priceMode: null };

// Navigation elements
const tabBookings = document.getElementById("tab-bookings");
const tabAnalytics = document.getElementById("tab-analytics");
const viewBookings = document.getElementById("view-bookings");
const viewAnalytics = document.getElementById("view-analytics");
const subtabHotel = document.getElementById("subtab-hotel");
const subtabBar = document.getElementById("subtab-bar");
const subviewHotel = document.getElementById("analytics-subview-hotel");
const subviewBar = document.getElementById("analytics-subview-bar");

// Top Executive Revenue Overview elements
const metricTopRoomRevenue = document.getElementById("metric-top-room-revenue");
const metricTopRoomSub = document.getElementById("metric-top-room-sub");
const metricTopBarRevenue = document.getElementById("metric-top-bar-revenue");
const metricTopBarSub = document.getElementById("metric-top-bar-sub");
const metricTopTotalRevenue = document.getElementById("metric-top-total-revenue");

// Booking Form & List elements
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

// Hotel Analytics elements
const analyticsForm = document.getElementById("analytics-filters");
const barForm = document.getElementById("bar-filters");
const analyticsStatus = document.getElementById("analytics-status");
const metricRevenue = document.getElementById("metric-revenue");
const metricBookings = document.getElementById("metric-bookings");
const metricNights = document.getElementById("metric-nights");
const metricAvailableNights = document.getElementById("metric-available-nights");
const metricOccupancy = document.getElementById("metric-occupancy");
const metricOccupancySub = document.getElementById("metric-occupancy-sub");
const metricAlos = document.getElementById("metric-alos");
const metricAdr = document.getElementById("metric-adr");
const metricRevPerBooking = document.getElementById("metric-rev-per-booking");
const metricReviews = document.getElementById("metric-reviews");
const metricSatisfaction = document.getElementById("metric-satisfaction");
const metricSatisfiedShare = document.getElementById("metric-satisfied-share");
const roomTypeRows = document.getElementById("room-type-rows");
const seasonRows = document.getElementById("season-rows");
const roomTypeSeasonRows = document.getElementById("room-type-season-rows");
const countryRows = document.getElementById("country-rows");
const countryEmpty = document.getElementById("country-empty");

// Bar Analytics elements
const metricBarRevenue = document.getElementById("metric-bar-revenue");
const metricBarUnits = document.getElementById("metric-bar-units");
const metricBarDrinks = document.getElementById("metric-bar-drinks");
const barCategoryRows = document.getElementById("bar-category-rows");
const barPriceTierRows = document.getElementById("bar-price-tier-rows");
const barDrinkRows = document.getElementById("bar-drink-rows");
const barDrinkEmpty = document.getElementById("bar-drink-empty");

const money = new Intl.NumberFormat("da-DK", { style: "currency", currency: "DKK" });
const number = new Intl.NumberFormat("da-DK");
const decimalFmt = new Intl.NumberFormat("da-DK", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const pct = (value) => `${decimalFmt.format(value)} %`;
const rating = (count, avg) => (count > 0 ? `${decimalFmt.format(avg)} / 5` : "–");

// ---------- Navigation & Tab Routing (TODOS.md, T071) ----------

function setPrimaryView(viewName, updateHash = true) {
  navState.view = viewName === "analytics" ? "analytics" : "bookings";
  const isBookings = navState.view === "bookings";

  if (tabBookings) {
    tabBookings.classList.toggle("active", isBookings);
    tabBookings.setAttribute("aria-selected", isBookings ? "true" : "false");
  }
  if (tabAnalytics) {
    tabAnalytics.classList.toggle("active", !isBookings);
    tabAnalytics.setAttribute("aria-selected", !isBookings ? "true" : "false");
  }

  if (viewBookings) viewBookings.hidden = !isBookings;
  if (viewAnalytics) viewAnalytics.hidden = isBookings;

  if (updateHash) {
    const hash = isBookings ? "#bookings" : `#analytics/${navState.analyticsSubView}`;
    if (window.location.hash !== hash) {
      window.history.pushState(null, "", hash);
    }
  }

  if (!isBookings) {
    loadAnalytics();
  }
}

function setAnalyticsSubView(subViewName, updateHash = true) {
  navState.analyticsSubView = subViewName === "bar" ? "bar" : "hotel";
  const isHotel = navState.analyticsSubView === "hotel";

  if (subtabHotel) {
    subtabHotel.classList.toggle("active", isHotel);
    subtabHotel.setAttribute("aria-selected", isHotel ? "true" : "false");
  }
  if (subtabBar) {
    subtabBar.classList.toggle("active", !isHotel);
    subtabBar.setAttribute("aria-selected", !isHotel ? "true" : "false");
  }

  if (subviewHotel) subviewHotel.hidden = !isHotel;
  if (subviewBar) subviewBar.hidden = isHotel;

  if (updateHash && navState.view === "analytics") {
    const hash = `#analytics/${navState.analyticsSubView}`;
    if (window.location.hash !== hash) {
      window.history.pushState(null, "", hash);
    }
  }
}

function handleHashChange() {
  const hash = window.location.hash;
  if (hash.startsWith("#analytics")) {
    const parts = hash.split("/");
    const sub = parts[1] === "bar" ? "bar" : "hotel";
    setAnalyticsSubView(sub, false);
    setPrimaryView("analytics", false);
  } else {
    setPrimaryView("bookings", false);
  }
}

function renderTopRevenueSummary() {
  const totalRev = Number(revenueState.roomRevenue || 0) + Number(revenueState.barRevenue || 0);
  if (metricTopRoomRevenue) metricTopRoomRevenue.textContent = money.format(revenueState.roomRevenue);
  if (metricTopRoomSub) metricTopRoomSub.textContent = `${number.format(revenueState.roomBookings)} bookings`;
  if (metricTopBarRevenue) metricTopBarRevenue.textContent = money.format(revenueState.barRevenue);
  if (metricTopBarSub) metricTopBarSub.textContent = `${number.format(revenueState.barUnits)} units sold`;
  if (metricTopTotalRevenue) metricTopTotalRevenue.textContent = money.format(totalRev);
}

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

// ---------- Table Column Sorting ----------

function parseCellValue(text) {
  const trimmed = text.trim();
  if (!trimmed || trimmed === "–" || trimmed === "-" || trimmed === "N/A") {
    return { type: "empty", value: null };
  }

  // ISO Date: YYYY-MM-DD
  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
    return { type: "date", value: trimmed };
  }

  // Rating: "3,74 / 5"
  const ratingMatch = trimmed.match(/^(\d+(?:,\d+)?)\s*\/\s*5$/);
  if (ratingMatch) {
    return { type: "number", value: parseFloat(ratingMatch[1].replace(",", ".")) };
  }

  // Danish/European currency or unit: e.g. "126.025.150,00 kr.", "75,14 %", "3,25 nights", "18.062", "1.234,56 DKK"
  const cleanNumCandidate = trimmed
    .replace(/\s*(?:kr\.?|DKK|%|nights|rooms|days|bookings|units)\s*/gi, "")
    .trim();

  // Danish formatted number: optional minus, digits with optional '.' thousands, optional ',' decimals
  if (/^-?\d{1,3}(?:\.\d{3})*(?:,\d+)?$/.test(cleanNumCandidate)) {
    const normalized = cleanNumCandidate.replace(/\./g, "").replace(",", ".");
    return { type: "number", value: parseFloat(normalized) };
  }

  // Standard float / integer
  if (/^-?\d+(?:\.\d+)?$/.test(cleanNumCandidate)) {
    return { type: "number", value: parseFloat(cleanNumCandidate) };
  }

  return { type: "string", value: trimmed };
}

function sortTable(table, colIndex, dir, markHeader = true) {
  const tbody = table.querySelector("tbody");
  if (!tbody) return;
  const rowsArray = Array.from(tbody.querySelectorAll("tr"));

  if (rowsArray.length > 1) {
    rowsArray.sort((rowA, rowB) => {
      const cellA = rowA.children[colIndex];
      const cellB = rowB.children[colIndex];
      const textA = cellA ? cellA.textContent : "";
      const textB = cellB ? cellB.textContent : "";
      const valA = parseCellValue(textA);
      const valB = parseCellValue(textB);

      if (valA.type === "empty" && valB.type === "empty") return 0;
      if (valA.type === "empty") return 1;
      if (valB.type === "empty") return -1;

      let cmp = 0;
      if (valA.type === "number" && valB.type === "number") {
        cmp = valA.value - valB.value;
      } else {
        cmp = String(valA.value).localeCompare(String(valB.value), "da", { numeric: true, sensitivity: "base" });
      }
      return dir === "asc" ? cmp : -cmp;
    });

    tbody.replaceChildren(...rowsArray);
  }

  table.dataset.sortCol = String(colIndex);
  table.dataset.sortDir = dir;

  if (markHeader) {
    const headers = table.querySelectorAll("thead th");
    headers.forEach((th, idx) => {
      if (idx === colIndex) {
        th.classList.remove("sorted-asc", "sorted-desc");
        th.classList.add(dir === "asc" ? "sorted-asc" : "sorted-desc");
        th.setAttribute("aria-sort", dir === "asc" ? "ascending" : "descending");
        th.setAttribute("title", dir === "asc" ? "Sorted ascending (click for descending)" : "Sorted descending (click for ascending)");
      } else {
        th.classList.remove("sorted-asc", "sorted-desc");
        th.removeAttribute("aria-sort");
        if (th.classList.contains("sortable")) {
          th.setAttribute("title", "Click to sort");
        }
      }
    });
  }
}

function applyActiveSort(table) {
  if (!table || table.dataset.sortCol === undefined) return;
  const colIndex = parseInt(table.dataset.sortCol, 10);
  const dir = table.dataset.sortDir || "asc";
  sortTable(table, colIndex, dir, false);
}

function initTableSorting() {
  document.querySelectorAll("table").forEach((table) => {
    const ths = table.querySelectorAll("thead th");
    ths.forEach((th, colIndex) => {
      const text = th.textContent.trim();
      if (!text || th.classList.contains("no-sort") || th.querySelector(".visually-hidden")?.textContent.trim() === "Actions") {
        return;
      }

      th.classList.add("sortable");
      th.setAttribute("tabindex", "0");
      th.setAttribute("role", "button");
      th.setAttribute("title", "Click to sort");

      const handleSort = () => {
        const isCurrentlyAsc = th.classList.contains("sorted-asc");
        const nextDir = isCurrentlyAsc ? "desc" : "asc";
        sortTable(table, colIndex, nextDir, true);
      };

      th.addEventListener("click", handleSort);
      th.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          handleSort();
        }
      });
    });
  });
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
  applyActiveSort(rows.closest("table"));
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
    category: (barForm && barForm.elements.category && barForm.elements.category.value) || undefined,
    price_tier: (barForm && barForm.elements.price_tier && barForm.elements.price_tier.value) || undefined,
  };
}

function formatPriceTierRange(row) {
  if (row.price_to_dkk === null || row.price_to_dkk === undefined) {
    return `≥ ${number.format(row.price_from_dkk)} DKK`;
  }
  return `${number.format(row.price_from_dkk)}–${number.format(row.price_to_dkk)} DKK`;
}

function renderHotelAnalytics(summary, byRoomType, bySeason, byRoomTypeSeason, byCountry) {
  revenueState.roomRevenue = summary.total_revenue_dkk;
  revenueState.roomBookings = summary.booking_count;
  renderTopRevenueSummary();

  if (metricRevenue) metricRevenue.textContent = money.format(summary.total_revenue_dkk);
  metricBookings.textContent = number.format(summary.booking_count);
  metricNights.textContent = number.format(summary.nights_sold);
  metricAvailableNights.textContent = number.format(summary.available_room_nights);
  metricOccupancy.textContent = pct(summary.occupancy_rate_pct);
  if (metricOccupancySub) {
    metricOccupancySub.textContent = `${number.format(summary.nights_sold)} / ${number.format(summary.available_room_nights)} nights`;
  }
  if (metricAlos) metricAlos.textContent = `${decimalFmt.format(summary.average_length_of_stay_nights)} nights`;
  if (metricAdr) metricAdr.textContent = money.format(summary.average_daily_rate_dkk);
  if (metricRevPerBooking) metricRevPerBooking.textContent = money.format(summary.average_revenue_per_booking_dkk);
  metricReviews.textContent = number.format(summary.review_count);
  metricSatisfaction.textContent = rating(summary.review_count, summary.average_satisfaction);
  metricSatisfiedShare.textContent = pct(summary.satisfied_share_pct);

  roomTypeRows.replaceChildren();
  for (const row of byRoomType) {
    const tr = document.createElement("tr");
    tr.append(
      cell(row.revenue_rank, "num"),
      cell(row.room_type),
      cell(row.room_count, "num"),
      cell(number.format(row.booking_count), "num"),
      cell(number.format(row.nights_sold), "num"),
      cell(number.format(row.available_room_nights), "num"),
      cell(pct(row.occupancy_rate_pct), "num"),
      cell(decimalFmt.format(row.average_length_of_stay_nights), "num"),
      cell(money.format(row.average_daily_rate_dkk), "num"),
      cell(money.format(row.average_revenue_per_booking_dkk), "num"),
      cell(money.format(row.revenue_dkk), "num"),
      cell(pct(row.revenue_share_pct), "num"),
      cell(number.format(row.review_count), "num"),
      cell(rating(row.review_count, row.average_satisfaction), "num"),
      cell(pct(row.satisfied_share_pct), "num"),
    );
    roomTypeRows.append(tr);
  }

  seasonRows.replaceChildren();
  for (const row of bySeason) {
    const tr = document.createElement("tr");
    tr.append(
      cell(row.season),
      cell(row.calendar_days, "num"),
      cell(number.format(row.booking_count), "num"),
      cell(number.format(row.nights_sold), "num"),
      cell(number.format(row.available_room_nights), "num"),
      cell(pct(row.occupancy_rate_pct), "num"),
      cell(decimalFmt.format(row.average_length_of_stay_nights), "num"),
      cell(money.format(row.average_daily_rate_dkk), "num"),
      cell(money.format(row.average_revenue_per_booking_dkk), "num"),
      cell(money.format(row.revenue_dkk), "num"),
      cell(pct(row.revenue_share_pct), "num"),
      cell(number.format(row.review_count), "num"),
      cell(rating(row.review_count, row.average_satisfaction), "num"),
      cell(pct(row.satisfied_share_pct), "num"),
    );
    seasonRows.append(tr);
  }

  roomTypeSeasonRows.replaceChildren();
  const byType = new Map();
  for (const row of byRoomTypeSeason) {
    if (!byType.has(row.room_type)) byType.set(row.room_type, {});
    byType.get(row.room_type)[row.season] = row.revenue_dkk;
  }
  for (const [roomType, seasons] of byType.entries()) {
    const tr = document.createElement("tr");
    tr.append(
      cell(roomType),
      cell(money.format(seasons.low ?? 0), "num"),
      cell(money.format(seasons.mid ?? 0), "num"),
      cell(money.format(seasons.high ?? 0), "num"),
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
  applyActiveSort(roomTypeRows.closest("table"));
  applyActiveSort(seasonRows.closest("table"));
  applyActiveSort(roomTypeSeasonRows.closest("table"));
  applyActiveSort(countryRows.closest("table"));
}

function renderBarAnalytics(barSummary, barByCategory, barByPriceTier, barByDrink) {
  revenueState.barRevenue = barSummary.total_revenue_dkk;
  revenueState.barUnits = barSummary.units_sold;
  renderTopRevenueSummary();

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

  if (barPriceTierRows) {
    barPriceTierRows.replaceChildren();
    for (const row of barByPriceTier) {
      const tr = document.createElement("tr");
      tr.append(
        cell(row.price_tier),
        cell(formatPriceTierRange(row)),
        cell(number.format(row.drink_count), "num"),
        cell(number.format(row.units_sold), "num"),
        cell(pct(row.unit_share_pct), "num"),
        cell(money.format(row.revenue_dkk), "num"),
        cell(pct(row.revenue_share_pct), "num"),
      );
      barPriceTierRows.append(tr);
    }
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
  applyActiveSort(barCategoryRows.closest("table"));
  if (barPriceTierRows) applyActiveSort(barPriceTierRows.closest("table"));
  applyActiveSort(barDrinkRows.closest("table"));
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
      barByPriceTier,
      barByDrink,
    ] = await Promise.all([
      getHotelSummary(hotelFilters),
      getHotelKpis("by-room-type", hotelFilters),
      getHotelKpis("by-season", hotelFilters),
      getHotelKpis("by-room-type-and-season", hotelFilters),
      getHotelKpis("by-country", hotelFilters),
      getBarSummary(barFilters),
      getBarKpis("by-category", barFilters),
      getBarKpis("by-price-tier", barFilters),
      getBarKpis("by-drink", barFilters),
    ]);
    renderHotelAnalytics(summary, byRoomType, bySeason, byRoomTypeSeason, byCountry);
    renderBarAnalytics(barSummary, barByCategory, barByPriceTier, barByDrink);
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

/**
 * Live price preview (FR-018) and cross-fill between total and nightly price (FR-019).
 *
 * Runs on every keystroke. Derives season, standard rate and totals directly from the form inputs
 * through price-preview.js (R15).
 */
function refreshPrice() {
  const nights = nightsValue();
  const roomTypeName = form.elements.room_type.value;
  const checkInDate = form.elements.check_in_date.value;
  const standard = standardPreview(roomTypeName, checkInDate, nights, state.roomTypes);

  // Cross-fill the other price field while one is being typed (FR-019).
  if (state.priceMode === "total") {
    const nightly = nightlyFromTotal(amount(totalInput), nights);
    nightlyInput.value = nightly !== null ? nightly : "";
    totalInput.readOnly = false;
    nightlyInput.readOnly = true;
  } else if (state.priceMode === "nightly") {
    const total = totalFromNightly(amount(nightlyInput), nights);
    totalInput.value = total !== null ? total : "";
    totalInput.readOnly = true;
    nightlyInput.readOnly = false;
  } else {
    totalInput.readOnly = false;
    nightlyInput.readOnly = false;
  }

  // Preview box below the inputs.
  if (standard === null) {
    previewBox.replaceChildren();
    const p = document.createElement("p");
    p.className = "preview-empty";
    p.textContent = "Choose room type, check-in date and nights to preview the price.";
    previewBox.append(p);
    return;
  }

  const typedTotal = amount(totalInput);
  const typedNightly = amount(nightlyInput);
  const manual = state.priceMode === "total" ? typedTotal : state.priceMode === "nightly" ? typedNightly : null;
  const usesManual = manual !== null && !Number.isNaN(manual);

  const dl = document.createElement("dl");
  dl.className = "preview-list";

  const row = (label, value, isTotal = false) => {
    const div = document.createElement("div");
    if (isTotal) div.className = "total";
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = value;
    div.append(dt, dd);
    return div;
  };

  dl.append(
    row("Season", standard.season),
    row(
      "Standard rate",
      `${number.format(standard.standard_nightly_dkk)} DKK / night (${number.format(standard.min_nightly_dkk)}–${number.format(standard.max_nightly_dkk)})`,
    ),
  );

  if (usesManual) {
    const totalDkk = state.priceMode === "total" ? typedTotal : totalFromNightly(typedNightly, nights);
    const nightlyDkk = state.priceMode === "nightly" ? typedNightly : nightlyFromTotal(typedTotal, nights);
    dl.append(
      row("Manual rate", `${number.format(nightlyDkk ?? 0)} DKK / night`),
      row("Total to pay", money.format(totalDkk ?? 0), true),
    );
  } else {
    dl.append(row("Standard total", money.format(standard.standard_total_dkk), true));
  }

  previewBox.replaceChildren(dl);
}

/** Edit mode (FR-020): banner on top, warm border around the form, button says "Save changes", cancel button jumps
back. */
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
  // If editing from another view, ensure bookings view is open
  setPrimaryView("bookings");
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

if (tabBookings) {
  tabBookings.addEventListener("click", () => setPrimaryView("bookings"));
}
if (tabAnalytics) {
  tabAnalytics.addEventListener("click", () => setPrimaryView("analytics"));
}
if (subtabHotel) {
  subtabHotel.addEventListener("click", () => setAnalyticsSubView("hotel"));
}
if (subtabBar) {
  subtabBar.addEventListener("click", () => setAnalyticsSubView("bar"));
}

window.addEventListener("hashchange", handleHashChange);

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
    initTableSorting();
    handleHashChange();
    state.roomTypes = await listRoomTypes();
    renderRoomTypes();
    await reload();
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    say(error.message, "error");
  }
}

init();
