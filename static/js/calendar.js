// ===============================
// STATE
// ===============================

let viewDate = new Date();
let selectedDate = new Date();
window.EVENTS = window.EVENTS || [];

const HOLIDAY_SETTINGS = {
    christian: true,
    jewish: true,
    islamic: true,
    chinese: true,
};

// Get week start from localStorage (from settings page)
const WEEK_START = localStorage.getItem("planit_weekStart") || "sunday"; // "sunday" | "monday"

// ===============================
// ELEMENTS
// ===============================

const calendarGrid = document.getElementById("calendarGrid");
const monthNameEl = document.getElementById("monthName");
const yearNameEl = document.getElementById("yearName");
const selectedDateText = document.getElementById("selectedDateText");
const selectedBadges = document.getElementById("selectedBadges");
const dayDetails = document.getElementById("dayDetails");
const weekdayRow = document.getElementById("weekdayRow");

const prevBtn = document.getElementById("prevMonthBtn");
const nextBtn = document.getElementById("nextMonthBtn");
const todayBtn = document.getElementById("todayBtn");

const holidayButtonsContainer = document.querySelector(".holiday-toggles");

// ===============================
// HELPERS
// ===============================

function startOfDay(d) {
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function formatDateKey(date) {
    return date.toISOString().split("T")[0];
}

function formatTime(timeStr) {
    if (!timeStr) return "No time";
    const d = new Date(`1970-01-01T${timeStr}`);
    return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

// ===============================
// EVENT OCCURRENCE LOGIC
// ===============================

function doesEventOccurOnDate(event, dateKey) {
    const current = new Date(dateKey);
    const start = new Date(event.start_date);

    const end = event.end_date
        ? new Date(event.end_date)
        : start;

    // Before event starts
    if (current < start) return false;

    // If no repeat → check range
    if (!event.repeat_type) {
        return current >= start && current <= end;
    }

    const diffDays = Math.floor((current - start) / 86400000);

    switch (event.repeat_type) {
        case "daily":
            return current >= start;

        case "weekly":
            return diffDays % 7 === 0;

        case "monthly":
            return current.getDate() === start.getDate();

        case "yearly":
            return (
                current.getDate() === start.getDate() &&
                current.getMonth() === start.getMonth()
            );

        default:
            return false;
    }
}

// ===============================
// EVENTS FOR DATE (SAFE FALLBACK)
// ===============================
function eventsForDate(dateKey) {
    // Return an array of events matching this date
    if (!window.EVENTS) return [];
    return window.EVENTS.filter(ev => {
        const start = new Date(ev.start_date);
        const end = ev.end_date ? new Date(ev.end_date) : start;
        const current = new Date(dateKey);
        return current >= start && current <= end;
    });
}

// ===============================
// WEEKDAY HEADER
// ===============================

function renderWeekdays() {
    const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    let ordered = WEEK_START === "monday" ? days.slice(1).concat(days[0]) : days;

    weekdayRow.innerHTML = "";
    ordered.forEach(d => {
        const el = document.createElement("div");
        el.classList.add("weekday");
        el.textContent = d;
        weekdayRow.appendChild(el);
    });
}

// ===============================
// HOLIDAY CALCULATIONS
// ===============================

function observedDate(dateObj) {
    const day = dateObj.getDay();
    if (day === 6) return new Date(dateObj.getFullYear(), dateObj.getMonth(), dateObj.getDate() - 1);
    if (day === 0) return new Date(dateObj.getFullYear(), dateObj.getMonth(), dateObj.getDate() + 1);
    return dateObj;
}

function nthWeekdayOfMonth(year, monthIndex, weekday, n) {
    const first = new Date(year, monthIndex, 1);
    const offset = (7 + weekday - first.getDay()) % 7;
    return new Date(year, monthIndex, 1 + offset + (n - 1) * 7);
}

function lastWeekdayOfMonth(year, monthIndex, weekday) {
    const last = new Date(year, monthIndex + 1, 0);
    const offset = (7 + last.getDay() - weekday) % 7;
    return new Date(year, monthIndex, last.getDate() - offset);
}

function getUSFederalHolidays(year) {
    const items = [];

    const fixed = [
        ["New Year’s Day", 0, 1],
        ["Juneteenth", 5, 19],
        ["Independence Day", 6, 4],
        ["Veterans Day", 10, 11],
        ["Christmas Day", 11, 25]
    ];

    fixed.forEach(([name, m, d]) => {
        items.push({ name, date: new Date(year, m, d) });
    });

    items.push({ name: "Martin Luther King Jr. Day", date: nthWeekdayOfMonth(year, 0, 1, 3) });
    items.push({ name: "Presidents’ Day", date: nthWeekdayOfMonth(year, 1, 1, 3) });
    items.push({ name: "Memorial Day", date: lastWeekdayOfMonth(year, 4, 1) });
    items.push({ name: "Labor Day", date: nthWeekdayOfMonth(year, 8, 1, 1) });
    items.push({ name: "Columbus Day", date: nthWeekdayOfMonth(year, 9, 1, 2) });
    items.push({ name: "Thanksgiving Day", date: nthWeekdayOfMonth(year, 10, 4, 4) });

    const map = {};
    items.forEach(it => {
        const actual = startOfDay(it.date);
        const obs = startOfDay(observedDate(actual));
        const actualKey = formatDateKey(actual);
        const obsKey = formatDateKey(obs);

        if (!map[actualKey]) map[actualKey] = [];
        map[actualKey].push({ name: it.name, observed: false });

        if (obsKey !== actualKey) {
            if (!map[obsKey]) map[obsKey] = [];
            map[obsKey].push({ name: `${it.name} (Observed)`, observed: true });
        }
    });

    return map;
}

function orthodoxEaster(year) {
    const a = year % 4;
    const b = year % 7;
    const c = year % 19;
    const d = (19*c + 15) % 30;
    const e = (2*a + 4*b - d + 34) % 7;
    const month = Math.floor((d + e + 114) / 31) - 1;
    const day = ((d + e + 114) % 31) + 1 + 13;
    return new Date(year, month, day);
}

// ===============================
// date-holidays Lookups
// ===============================

function getDateHolidaysFor(date, countryCode) {
    if (!window.Holidays) return [];
    const hd = new window.Holidays(countryCode); // e.g., "US" or "IL"
    const all = hd.getHolidays(date.getFullYear()) || [];
    const key = formatDateKey(date);

    return all
        .filter(h => formatDateKey(new Date(h.date)) === key)
        .map(h => ({ name: h.name, observed: h.substitute || false }));
}

// ===============================
// Holiday fetching helpers 
// ===============================

function jewishHolidaysForDate(date) {
    if (!HOLIDAY_SETTINGS.jewish) return [];
    const year = date.getFullYear();
    const key = formatDateKey(date);
    const items = [];

    const approx = [
        ["Rosh Hashanah", 8, 16],
        ["Yom Kippur", 8, 25],
        ["Sukkot", 8, 30],
        ["Hanukkah", 11, 7],
        ["Passover", 3, 5],
        ["Shavuot", 4, 25]
    ];

    approx.forEach(([name, m, d]) => {
        const dt = new Date(year, m, d);
        if (formatDateKey(dt) === key) {
            items.push({ name, observed: false });
        }
    });

    return items;
}

function islamicHolidaysForDate(date) {
    if (!HOLIDAY_SETTINGS.islamic) return [];
    const year = date.getFullYear();
    const key = formatDateKey(date);
    const items = [];

    const approx = [
        ["Ramadan Begins", 2, 22],
        ["Eid al-Fitr", 3, 21],
        ["Eid al-Adha", 5, 28],
        ["Islamic New Year", 6, 17],
        ["Mawlid", 9, 27]
    ];

    approx.forEach(([name, m, d]) => {
        const dt = new Date(year, m, d);
        if (formatDateKey(dt) === key) {
            items.push({ name, observed: false });
        }
    });

    return items;
}

function chineseHolidaysForDate(date) {
    if (!HOLIDAY_SETTINGS.chinese) return [];
    const year = date.getFullYear();
    const key = formatDateKey(date);
    const items = [];

    const approx = [
        ["Chinese New Year", 0, 22],
        ["Lantern Festival", 1, 5],
        ["Dragon Boat Festival", 5, 22],
        ["Mid-Autumn Festival", 8, 29],
        ["National Day", 9, 1]
    ];

    approx.forEach(([name, m, d]) => {
        const dt = new Date(year, m, d);
        if (formatDateKey(dt) === key) {
            items.push({ name, observed: false });
        }
    });

    return items;
}

function christianHolidaysForDate(date) {
    if (!HOLIDAY_SETTINGS.christian) return [];
    const year = date.getFullYear();
    const key = formatDateKey(date);
    const items = [];

    const fixedHolidays = [
        ["Christmas", 11, 25],
        ["Epiphany", 0, 6],
        ["All Saints' Day", 10, 1],
        ["Immaculate Conception", 11, 8],
        ["Assumption of Mary", 7, 15],
        ["St. Patrick's Day", 2, 17],
        ["Palm Sunday", null, null],
        ["Good Friday", null, null],
        ["Easter Sunday", null, null],
        ["Ascension", null, null],
        ["Pentecost", null, null]
    ];

    const easter = orthodoxEaster(year);
    const addDays = (d, n) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);

    fixedHolidays.forEach(([name, m, d]) => {
        let dt;
        if (m !== null) dt = new Date(year, m, d);
        else {
            if (name === "Palm Sunday") dt = addDays(easter, -7);
            if (name === "Good Friday") dt = addDays(easter, -2);
            if (name === "Easter Sunday") dt = easter;
            if (name === "Ascension") dt = addDays(easter, 39);
            if (name === "Pentecost") dt = addDays(easter, 49);
        }

        if (formatDateKey(dt) === key) {
            items.push({ name, observed: false });
        }
    });

    return items;
}

// ===============================
// Moon Phase & Zodiac
// ===============================

function moonPhase(date) {
    const diff = date - new Date(2001, 0, 1);
    const days = diff / 86400000;
    const synodic = 29.53058867;
    const phase = ((days % synodic) / synodic + 1) % 1;
    if (phase < 0.03) return "New Moon";
    if (phase < 0.22) return "Waxing Crescent";
    if (phase < 0.28) return "First Quarter";
    if (phase < 0.47) return "Waxing Gibbous";
    if (phase < 0.53) return "Full Moon";
    if (phase < 0.72) return "Waning Gibbous";
    if (phase < 0.78) return "Last Quarter";
    return "Waning Crescent";
}

function zodiacSign(date) {
    const month = date.getMonth();
    const day = date.getDate();
    const z = [
        [20,"Capricorn"],[19,"Aquarius"],[20,"Pisces"],[20,"Aries"],[21,"Taurus"],[21,"Gemini"],
        [21,"Cancer"],[23,"Leo"],[23,"Virgo"],[23,"Libra"],[22,"Scorpio"],[22,"Sagittarius"]
    ];
    return (day < z[month][0]) ? z[(month+11)%12][1] : z[month][1];
}

// ===============================
// GET HOLIDAYS FOR DATE
// ===============================

function holidaysForDate(date) {
    const key = formatDateKey(date);
    let all = [];

    const usHolidays = getUSFederalHolidays(date.getFullYear())[key] || [];
    all.push(...usHolidays.map(it => ({ ...it, type: 'us' })));

    if (HOLIDAY_SETTINGS.christian) all.push(...christianHolidaysForDate(date));
    if (HOLIDAY_SETTINGS.jewish) all.push(...jewishHolidaysForDate(date));
    if (HOLIDAY_SETTINGS.islamic) all.push(...islamicHolidaysForDate(date));
    if (HOLIDAY_SETTINGS.chinese) all.push(...chineseHolidaysForDate(date));

    return all;
}

// ===============================
// RENDER CALENDAR
// ===============================

// ===============================
// RENDER CALENDAR
// ===============================

function renderCalendar() {
    calendarGrid.innerHTML = "";

    const year = viewDate.getFullYear();
    const month = viewDate.getMonth();

    monthNameEl.textContent = viewDate.toLocaleString("default", { month: "long" });
    yearNameEl.textContent = year;

    // Determine first day of the month (adjust if week starts on Monday)
    let firstDay = new Date(year, month, 1).getDay();
    if (WEEK_START === "monday") firstDay = (firstDay + 6) % 7;

    const daysInMonth = new Date(year, month + 1, 0).getDate();

    // Render empty cells before the first day
    for (let i = 0; i < firstDay; i++) {
        const empty = document.createElement("div");
        empty.classList.add("day-cell", "is-outside");
        calendarGrid.appendChild(empty);
    }

    // Helper to determine badge class
    function getBadgeClass(it) {
        if (it.color) return it.color; // use event-specific color if provided
        const name = it.name || "";
        if (/Easter|Christmas|Good Friday|Palm Sunday|Pentecost|Advent|Epiphany/i.test(name)) return "holiday";
        if (HOLIDAY_SETTINGS.jewish && /Rosh Hashanah|Yom Kippur|Sukkot|Passover|Hanukkah|Shavuot/i.test(name)) return "jewish";
        if (HOLIDAY_SETTINGS.islamic && /Ramadan|Eid|Mawlid|Islamic New Year/i.test(name)) return "islamic";
        if (HOLIDAY_SETTINGS.chinese && /Chinese New Year|Lantern Festival|Dragon Boat Festival|Mid-Autumn|National Day/i.test(name)) return "chinese";
        if (it.type === "moon") return "moon";
        if (it.type === "zodiac") return "zodiac";
        return "event";
    }

    // Render each day
    for (let day = 1; day <= daysInMonth; day++) {
        const cellDate = new Date(year, month, day);
        const dateKey = formatDateKey(cellDate);

        const evs = eventsForDate(dateKey);
        const hols = holidaysForDate(cellDate);

        const cell = document.createElement("div");
        cell.classList.add("day-cell");
        if (formatDateKey(selectedDate) === dateKey) cell.classList.add("is-selected");
        if (formatDateKey(new Date()) === dateKey) cell.classList.add("is-today");

        // Day number
        const num = document.createElement("div");
        num.classList.add("day-number");
        num.textContent = day;
        cell.appendChild(num);

        // Badge row
        const badgeRow = document.createElement("div");
        badgeRow.classList.add("badge-row");

        evs.concat(hols).forEach(it => {
            const badge = document.createElement("div");
            badge.classList.add("badge", getBadgeClass(it));
            badge.textContent = it.name;
            badge.title = it.name;

            // Apply custom background color if it's an event
            if (it.color) badge.style.backgroundColor = it.color;

            badgeRow.appendChild(badge);
        });

        if (badgeRow.children.length > 0) cell.appendChild(badgeRow);

        // Click selects date
        cell.addEventListener("click", () => {
            selectedDate = startOfDay(cellDate);
            renderCalendar();
            renderDayPanel();
        });

        calendarGrid.appendChild(cell);
    }
}

// ===============================
// RENDER DAY PANEL
// ===============================

function renderDayPanel() {
    const key = formatDateKey(selectedDate);
    const evs = eventsForDate(key);
    const hols = holidaysForDate(selectedDate);

    selectedDateText.textContent = selectedDate.toDateString();

    // Count of only events + holidays (moon/zodiac not included)
    const itemCount = evs.length + hols.length;
    selectedBadges.textContent = itemCount === 0 ? "No items" : `${itemCount} item${itemCount > 1 ? "s" : ""}`;

    // Clear previous details
    dayDetails.innerHTML = "";

    // ===============================
    // DAY-PANEL HEAD: Moon + Zodiac
    // ===============================
    // Remove previous moon/zodiac cards from body, add to head left of badge count
    const dayPanelHead = document.querySelector(".day-panel-head");

    // Remove existing moon/zodiac if present
    dayPanelHead.querySelectorAll(".moon-zodiac").forEach(el => el.remove());

    const moonZodiacContainer = document.createElement("div");
    moonZodiacContainer.classList.add("moon-zodiac");
    moonZodiacContainer.innerHTML = `
        <div class="moon-phase">🌙 ${moonPhase(selectedDate)}</div>
        <div class="zodiac-sign">⭐ ${zodiacSign(selectedDate)}</div>
    `;
    // Insert before the badge counter
    const badgePill = document.getElementById("selectedBadges");
    dayPanelHead.insertBefore(moonZodiacContainer, badgePill);

    // ===============================
    // DETAIL CARDS: Events + Holidays
    // ===============================
    if (itemCount === 0) {
        dayDetails.innerHTML = "<div class='detail-card'>No events or holidays</div>";
    } else {
        evs.concat(hols).forEach(it => {
            const card = document.createElement("div");
            card.classList.add("detail-card");

            const title = document.createElement("div");
            title.classList.add("detail-title");
            title.textContent = it.name;
            card.appendChild(title);

            const sub = document.createElement("div");
            sub.classList.add("detail-sub");
            sub.textContent = it.observed ? "(Observed)" : "";
            card.appendChild(sub);

            dayDetails.appendChild(card);
        });
    }
}

// ===============================
// HOLIDAY BUTTONS
// ===============================

function initHolidayButtons(container) {
    container.querySelectorAll("button").forEach(btn => {
        btn.addEventListener("click", () => {
            const type = btn.dataset.type;
            HOLIDAY_SETTINGS[type] = !HOLIDAY_SETTINGS[type];
            btn.classList.toggle("active", HOLIDAY_SETTINGS[type]);
            renderCalendar();
            renderDayPanel();
        });
    });
}

// ===============================
// NAVIGATION
// ===============================

prevBtn.addEventListener("click", () => {
    viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() - 1, 1);
    renderCalendar();
});

nextBtn.addEventListener("click", () => {
    viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 1);
    renderCalendar();
});

todayBtn.addEventListener("click", () => {
    const now = new Date();
    viewDate = startOfDay(now);
    selectedDate = startOfDay(now);
    renderCalendar();
    renderDayPanel();
});

// ===============================
// INITIALIZE
// ===============================

document.addEventListener("DOMContentLoaded", () => {
    renderWeekdays();
    initHolidayButtons(holidayButtonsContainer);

    const now = new Date();
    viewDate = startOfDay(now);       // set to today
    selectedDate = startOfDay(now);   // selected date is today

    renderCalendar();
    renderDayPanel();

    // Add Event button click
    const addEventBtn = document.getElementById("addEventBtn");
    if (addEventBtn) {
        addEventBtn.addEventListener("click", () => {
            // Redirect to the create event page
            window.location.href = "/events/new";
        });
    }
});