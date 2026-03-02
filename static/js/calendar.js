// Interactable month calendar + US federal holidays + event previews
// Uses local time for display.

const monthNameEl = document.getElementById("monthName");
const yearNameEl = document.getElementById("yearName");
const gridEl = document.getElementById("calendarGrid");

const prevBtn = document.getElementById("prevMonthBtn");
const nextBtn = document.getElementById("nextMonthBtn");
const todayBtn = document.getElementById("todayBtn");
const addEventBtn = document.getElementById("addEventBtn");

const selectedDateTextEl = document.getElementById("selectedDateText");
const selectedBadgesEl = document.getElementById("selectedBadges");
const dayDetailsEl = document.getElementById("dayDetails");

const weekdayRowEl = document.getElementById("weekdayRow");

const MONTHS = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December"
];

const WEEKDAYS_SUN_START = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
const WEEKDAYS_MON_START = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];

function pad2(n) { return String(n).padStart(2, "0"); }

function ymd(dateObj) {
  const y = dateObj.getFullYear();
  const m = pad2(dateObj.getMonth() + 1);
  const d = pad2(dateObj.getDate());
  return `${y}-${m}-${d}`;
}

function sameDay(a, b) {
  return a.getFullYear() === b.getFullYear()
    && a.getMonth() === b.getMonth()
    && a.getDate() === b.getDate();
}

function startOfDay(d) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

/**
 * Get user's preferred week start.
 * Returns "sunday" or "monday"
 */
function getWeekStartPreference() {
  const direct = localStorage.getItem("planit_weekStart");
  if (direct === "monday" || direct === "sunday") return direct;

  // Fallback: try reading full settings object
  try {
    const raw = localStorage.getItem("planit_settings");
    const obj = raw ? JSON.parse(raw) : null;
    if (obj?.weekStart === "monday" || obj?.weekStart === "sunday") return obj.weekStart;
  } catch {}

  return "sunday";
}

function renderWeekdayHeader() {
  if (!weekdayRowEl) return;

  const weekStart = getWeekStartPreference();
  const labels = weekStart === "monday" ? WEEKDAYS_MON_START : WEEKDAYS_SUN_START;

  weekdayRowEl.innerHTML = "";
  for (const label of labels) {
    const d = document.createElement("div");
    d.className = "weekday";
    d.textContent = label;
    weekdayRowEl.appendChild(d);
  }
}

// ---------- US Federal Holidays (with observed rules) ----------
function observedDate(dateObj) {
  // If holiday falls on Saturday -> observed Friday
  // If holiday falls on Sunday -> observed Monday
  const day = dateObj.getDay();
  if (day === 6) return new Date(dateObj.getFullYear(), dateObj.getMonth(), dateObj.getDate() - 1);
  if (day === 0) return new Date(dateObj.getFullYear(), dateObj.getMonth(), dateObj.getDate() + 1);
  return dateObj;
}

function nthWeekdayOfMonth(year, monthIndex, weekday, n) {
  // weekday: 0=Sun..6=Sat
  // n: 1..5
  const first = new Date(year, monthIndex, 1);
  const offset = (7 + weekday - first.getDay()) % 7;
  const day = 1 + offset + (n - 1) * 7;
  return new Date(year, monthIndex, day);
}

function lastWeekdayOfMonth(year, monthIndex, weekday) {
  const last = new Date(year, monthIndex + 1, 0); // last day of month
  const offset = (7 + last.getDay() - weekday) % 7;
  return new Date(year, monthIndex, last.getDate() - offset);
}

function getUSFederalHolidays(year) {
  // Returns map: { "YYYY-MM-DD": [ {name, observed: boolean, actual: YYYY-MM-DD} ] }
  const items = [];

  // Fixed-date holidays
  const newYear = new Date(year, 0, 1);
  const juneteenth = new Date(year, 5, 19);
  const independence = new Date(year, 6, 4);
  const veterans = new Date(year, 10, 11);
  const christmas = new Date(year, 11, 25);

  items.push({ name: "New Year’s Day", date: newYear });
  items.push({ name: "Juneteenth", date: juneteenth });
  items.push({ name: "Independence Day", date: independence });
  items.push({ name: "Veterans Day", date: veterans });
  items.push({ name: "Christmas Day", date: christmas });

  // Monday/Thursday-based holidays
  items.push({ name: "Martin Luther King Jr. Day", date: nthWeekdayOfMonth(year, 0, 1, 3) }); // 3rd Mon Jan
  items.push({ name: "Presidents’ Day", date: nthWeekdayOfMonth(year, 1, 1, 3) }); // 3rd Mon Feb
  items.push({ name: "Memorial Day", date: lastWeekdayOfMonth(year, 4, 1) }); // last Mon May
  items.push({ name: "Labor Day", date: nthWeekdayOfMonth(year, 8, 1, 1) }); // 1st Mon Sep
  items.push({ name: "Columbus Day", date: nthWeekdayOfMonth(year, 9, 1, 2) }); // 2nd Mon Oct
  items.push({ name: "Thanksgiving Day", date: nthWeekdayOfMonth(year, 10, 4, 4) }); // 4th Thu Nov (Thu=4)

  const map = {};

  for (const it of items) {
    const actual = startOfDay(it.date);
    const obs = startOfDay(observedDate(actual));
    const actualKey = ymd(actual);
    const obsKey = ymd(obs);

    // show holiday on its actual date
    if (!map[actualKey]) map[actualKey] = [];
    map[actualKey].push({ name: it.name, observed: false, actual: actualKey });

    // if observed differs, also show on observed date as "Observed"
    if (obsKey !== actualKey) {
      if (!map[obsKey]) map[obsKey] = [];
      map[obsKey].push({ name: `${it.name} (Observed)`, observed: true, actual: actualKey });
    }
  }

  return map;
}

// ---------- Events helpers ----------
function eventsForDate(dateKey) {
  return (window.EVENTS || []).filter(e => e.date === dateKey);
}

// ---------- Rendering ----------
let viewDate = new Date();                 // controls displayed month
let selectedDate = startOfDay(new Date()); // controls right-side panel

function setHeader(dateObj) {
  monthNameEl.textContent = MONTHS[dateObj.getMonth()];
  yearNameEl.textContent = String(dateObj.getFullYear());
}

/**
 * Build 42 day cells.
 * weekStart: "sunday" -> weekStartIndex = 0
 *           "monday" -> weekStartIndex = 1
 */
function buildCalendarCells(dateObj) {
  const year = dateObj.getFullYear();
  const month = dateObj.getMonth();

  const holidays = getUSFederalHolidays(year);

  const weekStart = getWeekStartPreference();
  const weekStartIndex = (weekStart === "monday") ? 1 : 0;

  // Determine grid start: weekStart day of the week containing the 1st of the month
  const firstOfMonth = new Date(year, month, 1);
  const firstDow = firstOfMonth.getDay(); // 0=Sun..6=Sat

  // how many days to go back from the 1st to reach the chosen week start
  const offset = (7 + firstDow - weekStartIndex) % 7;
  const gridStart = new Date(year, month, 1 - offset);

  // 6-week grid (42 days)
  const days = [];
  for (let i = 0; i < 42; i++) {
    const d = new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + i);
    const key = ymd(d);
    days.push({
      date: d,
      key,
      isOutside: d.getMonth() !== month,
      isToday: sameDay(d, new Date()),
      holidays: holidays[key] || [],
      events: eventsForDate(key),
    });
  }

  return days;
}

function renderGrid() {
  renderWeekdayHeader(); // reflect settings
  setHeader(viewDate);
  gridEl.innerHTML = "";

  const cells = buildCalendarCells(viewDate);

  for (const cell of cells) {
    const el = document.createElement("button");
    el.type = "button";
    el.className = "day-cell";
    if (cell.isOutside) el.classList.add("is-outside");
    if (cell.isToday) el.classList.add("is-today");
    if (sameDay(cell.date, selectedDate)) el.classList.add("is-selected");

    el.setAttribute("data-date", cell.key);
    el.setAttribute("aria-label", `${MONTHS[cell.date.getMonth()]} ${cell.date.getDate()}, ${cell.date.getFullYear()}`);

    const top = document.createElement("div");
    top.className = "day-top";

    const num = document.createElement("div");
    num.className = "day-number";
    num.textContent = String(cell.date.getDate());

    top.appendChild(num);
    el.appendChild(top);

    // badges (holiday + event counts)
    const badgeRow = document.createElement("div");
    badgeRow.className = "badge-row";

    if (cell.holidays.length > 0) {
      const b = document.createElement("div");
      b.className = "badge holiday";
      b.textContent = "Holiday";
      badgeRow.appendChild(b);
    }

    if (cell.events.length > 0) {
      const b = document.createElement("div");
      b.className = "badge event";
      b.textContent = `${cell.events.length} event${cell.events.length === 1 ? "" : "s"}`;
      badgeRow.appendChild(b);
    }

    if (badgeRow.childElementCount > 0) el.appendChild(badgeRow);

    // preview top 2 events
    if (cell.events.length > 0) {
      const preview = document.createElement("div");
      preview.className = "events-preview";

      cell.events.slice(0, 2).forEach(ev => {
        const chip = document.createElement("div");
        chip.className = "event-chip";
        chip.textContent = `${ev.time} • ${ev.name}`;
        preview.appendChild(chip);
      });

      el.appendChild(preview);
    }

    el.addEventListener("click", () => {
      selectedDate = startOfDay(cell.date);
      renderGrid();       // refresh selection styling
      renderDayPanel();   // refresh details
    });

    gridEl.appendChild(el);
  }
}

function renderDayPanel() {
  const key = ymd(selectedDate);
  const year = selectedDate.getFullYear();
  const holidays = getUSFederalHolidays(year)[key] || [];
  const evs = eventsForDate(key);

  const pretty = selectedDate.toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric"
  });

  selectedDateTextEl.textContent = pretty;

  const count = holidays.length + evs.length;
  selectedBadgesEl.textContent = count === 0 ? "No items" : `${holidays.length} holiday • ${evs.length} event${evs.length === 1 ? "" : "s"}`;

  dayDetailsEl.innerHTML = "";

  if (holidays.length === 0 && evs.length === 0) {
    const hint = document.createElement("div");
    hint.className = "hint";
    hint.textContent = "No holidays or events for this day yet.";
    dayDetailsEl.appendChild(hint);
    return;
  }

  if (holidays.length > 0) {
    const card = document.createElement("div");
    card.className = "detail-card";
    card.innerHTML = `<div class="detail-title">Holidays</div>`;
    holidays.forEach(h => {
      const row = document.createElement("div");
      row.className = "detail-sub";
      row.textContent = `• ${h.name}`;
      card.appendChild(row);
    });
    dayDetailsEl.appendChild(card);
  }

  if (evs.length > 0) {
    const card = document.createElement("div");
    card.className = "detail-card";
    card.innerHTML = `<div class="detail-title">Events</div>`;

    evs.forEach(ev => {
      const block = document.createElement("div");
      block.style.marginTop = "10px";

      const title = document.createElement("div");
      title.style.fontWeight = "800";
      title.textContent = `${ev.time} • ${ev.name}`;

      const sub = document.createElement("div");
      sub.className = "detail-sub";
      sub.textContent = ev.people && ev.people.length ? "People:" : "People: None";

      block.appendChild(title);
      block.appendChild(sub);

      if (ev.people && ev.people.length) {
        const peopleRow = document.createElement("div");
        peopleRow.className = "people-row";
        ev.people.forEach(p => {
          const tag = document.createElement("div");
          tag.className = "person-tag";
          tag.textContent = p;
          peopleRow.appendChild(tag);
        });
        block.appendChild(peopleRow);
      }

      card.appendChild(block);
    });

    dayDetailsEl.appendChild(card);
  }
}

// ---------- Controls ----------
prevBtn.addEventListener("click", () => {
  viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() - 1, 1);
  renderGrid();
});

nextBtn.addEventListener("click", () => {
  viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 1);
  renderGrid();
});

todayBtn.addEventListener("click", () => {
  const now = new Date();
  viewDate = new Date(now.getFullYear(), now.getMonth(), 1);
  selectedDate = startOfDay(now);
  renderGrid();
  renderDayPanel();
});

addEventBtn.addEventListener("click", () => {
  const dateKey = ymd(selectedDate);
  window.location.href = `/events/new?date=${dateKey}`;
});

// if user changes settings in another tab, refresh calendar automatically
window.addEventListener("storage", (e) => {
  if (e.key === "planit_weekStart" || e.key === "planit_settings") {
    renderGrid();
  }
});

// Initial render
(function init() {
  const now = new Date();
  viewDate = new Date(now.getFullYear(), now.getMonth(), 1);
  selectedDate = startOfDay(now);
  renderGrid();
  renderDayPanel();
})();
