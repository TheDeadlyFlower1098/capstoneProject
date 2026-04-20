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

const WEEK_START = localStorage.getItem("planit_weekStart") || "sunday";

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
// LOAD EVENTS FROM API
// ===============================

async function loadEvents() {
    try {
        const res = await fetch("/api/events");
        const data = await res.json();

        window.EVENTS = data;

        renderCalendar();
        renderDayPanel();
    } catch (err) {
        console.error("Failed to load events:", err);
    }
}

// ===============================
// HELPERS
// ===============================

function getUserSettings(){
    return JSON.parse(localStorage.getItem("planit_settings") || "{}");
}

function startOfDay(d) {
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function formatDateKey(date) {
    return date.toISOString().split("T")[0];
}

function getTimeFormat() {
    return localStorage.getItem("planit_timeFormat") || "12";
}

function formatTime(timeStr) {
    if (!timeStr) return "No time";

    const is24 = getTimeFormat() === "24";

    const d = new Date(`1970-01-01T${timeStr}`);

    return d.toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
        hour12: !is24
    });
}

// ===============================
// EVENT FILTERING
// ===============================

function eventsForDate(dateKey) {

    if (!window.EVENTS) return [];

    const current = new Date(dateKey);

    return window.EVENTS.filter(ev => {

        const start = new Date(ev.start_date);
        const end = ev.end_date ? new Date(ev.end_date) : start;

        if (current < start || current > end) return false;

        if (!ev.repeat_type) return true;

        const diffDays = Math.floor((current - start) / 86400000);

        switch (ev.repeat_type) {

            case "daily":
                return true;

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
    });
}

// ===============================
// WEEKDAY HEADER
// ===============================

function renderWeekdays() {

    const days = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
    const ordered = WEEK_START === "monday"
        ? days.slice(1).concat(days[0])
        : days;

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
        ["New Year’s Day",0,1],
        ["Juneteenth",5,19],
        ["Independence Day",6,4],
        ["Veterans Day",10,11],
        ["Christmas Day",11,25]
    ];

    fixed.forEach(([name,m,d])=>{
        items.push({name,date:new Date(year,m,d)});
    });

    items.push({name:"Martin Luther King Jr. Day",date:nthWeekdayOfMonth(year,0,1,3)});
    items.push({name:"Presidents’ Day",date:nthWeekdayOfMonth(year,1,1,3)});
    items.push({name:"Memorial Day",date:lastWeekdayOfMonth(year,4,1)});
    items.push({name:"Labor Day",date:nthWeekdayOfMonth(year,8,1,1)});
    items.push({name:"Columbus Day",date:nthWeekdayOfMonth(year,9,1,2)});
    items.push({name:"Thanksgiving Day",date:nthWeekdayOfMonth(year,10,4,4)});

    const map={};

    items.forEach(it=>{
        const actual=startOfDay(it.date);
        const obs=startOfDay(observedDate(actual));

        const actualKey=formatDateKey(actual);
        const obsKey=formatDateKey(obs);

        if(!map[actualKey]) map[actualKey]=[];
        map[actualKey].push({name:it.name,observed:false});

        if(obsKey!==actualKey){
            if(!map[obsKey]) map[obsKey]=[];
            map[obsKey].push({name:`${it.name} (Observed)`,observed:true});
        }
    });

    return map;
}

// ===============================
// RELIGIOUS HOLIDAYS
// ===============================

function jewishHolidaysForDate(date){

    if(!HOLIDAY_SETTINGS.jewish) return [];

    const year=date.getFullYear();
    const key=formatDateKey(date);
    const items=[];

    const approx=[
        ["Rosh Hashanah",8,16],
        ["Yom Kippur",8,25],
        ["Sukkot",8,30],
        ["Hanukkah",11,7],
        ["Passover",3,5],
        ["Shavuot",4,25]
    ];

    approx.forEach(([name,m,d])=>{
        const dt=new Date(year,m,d);
        if(formatDateKey(dt)===key) items.push({name,observed:false});
    });

    return items;
}

function islamicHolidaysForDate(date){

    if(!HOLIDAY_SETTINGS.islamic) return [];

    const year=date.getFullYear();
    const key=formatDateKey(date);
    const items=[];

    const approx=[
        ["Ramadan Begins",2,22],
        ["Eid al-Fitr",3,21],
        ["Eid al-Adha",5,28],
        ["Islamic New Year",6,17],
        ["Mawlid",9,27]
    ];

    approx.forEach(([name,m,d])=>{
        const dt=new Date(year,m,d);
        if(formatDateKey(dt)===key) items.push({name,observed:false});
    });

    return items;
}

function chineseHolidaysForDate(date){

    if(!HOLIDAY_SETTINGS.chinese) return [];

    const year=date.getFullYear();
    const key=formatDateKey(date);
    const items=[];

    const approx=[
        ["Chinese New Year",0,22],
        ["Lantern Festival",1,5],
        ["Dragon Boat Festival",5,22],
        ["Mid-Autumn Festival",8,29],
        ["National Day",9,1]
    ];

    approx.forEach(([name,m,d])=>{
        const dt=new Date(year,m,d);
        if(formatDateKey(dt)===key) items.push({name,observed:false});
    });

    return items;
}

function christianHolidaysForDate(date){

    if(!HOLIDAY_SETTINGS.christian) return [];

    const year=date.getFullYear();
    const key=formatDateKey(date);
    const items=[];

    const fixed=[
        ["Christmas",11,25],
        ["Epiphany",0,6],
        ["All Saints' Day",10,1],
        ["Immaculate Conception",11,8],
        ["Assumption of Mary",7,15],
        ["St. Patrick's Day",2,17]
    ];

    fixed.forEach(([name,m,d])=>{
        const dt=new Date(year,m,d);
        if(formatDateKey(dt)===key) items.push({name,observed:false});
    });

    return items;
}

// ===============================
// HOLIDAYS FOR DATE
// ===============================

function holidaysForDate(date){

    const key=formatDateKey(date);
    let all=[];

    const us=getUSFederalHolidays(date.getFullYear())[key]||[];
    all.push(...us);

    all.push(...christianHolidaysForDate(date));
    all.push(...jewishHolidaysForDate(date));
    all.push(...islamicHolidaysForDate(date));
    all.push(...chineseHolidaysForDate(date));

    return all;
}

// ===============================
// RENDER CALENDAR
// ===============================

function renderCalendar(){

    calendarGrid.innerHTML="";

    const year=viewDate.getFullYear();
    const month=viewDate.getMonth();

    monthNameEl.textContent=viewDate.toLocaleString("default",{month:"long"});
    yearNameEl.textContent=year;

    let firstDay=new Date(year,month,1).getDay();

    if(WEEK_START==="monday") firstDay=(firstDay+6)%7;

    const daysInMonth=new Date(year,month+1,0).getDate();

    for(let i=0;i<firstDay;i++){
        const empty=document.createElement("div");
        empty.classList.add("day-cell","is-outside");
        calendarGrid.appendChild(empty);
    }

    for(let day=1;day<=daysInMonth;day++){

        const cellDate=new Date(year,month,day);
        const dateKey=formatDateKey(cellDate);

        const evs=eventsForDate(dateKey);
        const hols=holidaysForDate(cellDate);

        const cell=document.createElement("div");
        cell.classList.add("day-cell");

        if(formatDateKey(selectedDate)===dateKey) cell.classList.add("is-selected");
        if(formatDateKey(new Date())===dateKey) cell.classList.add("is-today");

        const num=document.createElement("div");
        num.classList.add("day-number");
        num.textContent=day;
        cell.appendChild(num);

        const badgeRow=document.createElement("div");
        badgeRow.classList.add("badge-row");

        evs.concat(hols).forEach(it=>{

            const badge=document.createElement("div");
            badge.classList.add("badge");

            badge.textContent=it.name;

            if(it.color) badge.style.backgroundColor=it.color;

            badgeRow.appendChild(badge);
        });

        if(badgeRow.children.length>0) cell.appendChild(badgeRow);

        cell.addEventListener("click",()=>{
            selectedDate=startOfDay(cellDate);
            renderCalendar();
            renderDayPanel();
        });

        calendarGrid.appendChild(cell);
    }
}

// ===============================
// DAY PANEL
// ===============================

function renderDayPanel(){

    const key=formatDateKey(selectedDate);

    const evs=eventsForDate(key);
    const hols=holidaysForDate(selectedDate);

    const total=evs.length+hols.length;

    selectedDateText.textContent=selectedDate.toDateString();

    selectedBadges.textContent=
        total===0?"No items":`${total} item${total>1?"s":""}`;

    dayDetails.innerHTML="";

    if(total===0){
        dayDetails.innerHTML="<div class='detail-card'>No events or holidays</div>";
        return;
    }

    evs.concat(hols).forEach(it=>{

        const card=document.createElement("div");
        card.classList.add("detail-card");

        const title=document.createElement("div");
        title.classList.add("detail-title");

        const settings = JSON.parse(localStorage.getItem("planit_settings") || "{}");
        if(it.visibility === "private" && !settings.eventVisibility){
            title.textContent = "Private Event";
        }else{
            title.textContent = it.name;
        }

        card.appendChild(title);

        // ===============================
    // OWNER (CREATOR)
    // ===============================
    if (it.creator) {

        const creator = document.createElement("div");
        creator.classList.add("detail-sub");
        creator.textContent = `👑 Owner: ${it.creator}`;
        card.appendChild(creator);
    }

    // ===============================
    // ATTENDEES (ACCEPTED ONLY)
    // ===============================
    if (it.attendees && it.attendees.length > 0) {

        const attendees = document.createElement("div");
        attendees.classList.add("detail-sub");

        attendees.textContent = `👥 Attendees: ${it.attendees.join(", ")}`;

        card.appendChild(attendees);
    }

        if(it.start_time!==undefined){

            const details=document.createElement("div");
            details.classList.add("detail-sub");

            const start=formatTime(it.start_time);
            const end=formatTime(it.end_time);

            let parts=[];

            if(it.location) parts.push(`📍 ${it.location}`);

            if(it.all_day) parts.push("🕒 All Day");
            else if(it.start_time) parts.push(`🕒 ${start} - ${end}`);

            details.textContent=parts.join(" • ");
            card.appendChild(details);
        }

        if(it.observed){
            const observed=document.createElement("div");
            observed.classList.add("detail-sub");
            observed.textContent="(Observed)";
            card.appendChild(observed);
        }

        dayDetails.appendChild(card);
    });
}

// ===============================
// HOLIDAY BUTTONS
// ===============================

function initHolidayButtons(container){

    container.querySelectorAll("button").forEach(btn=>{

        btn.addEventListener("click",()=>{

            const type=btn.dataset.type;

            HOLIDAY_SETTINGS[type]=!HOLIDAY_SETTINGS[type];

            btn.classList.toggle("active",HOLIDAY_SETTINGS[type]);

            renderCalendar();
            renderDayPanel();
        });
    });
}

// ===============================
// NAVIGATION
// ===============================

prevBtn.addEventListener("click",()=>{
    viewDate=new Date(viewDate.getFullYear(),viewDate.getMonth()-1,1);
    renderCalendar();
});

nextBtn.addEventListener("click",()=>{
    viewDate=new Date(viewDate.getFullYear(),viewDate.getMonth()+1,1);
    renderCalendar();
});

todayBtn.addEventListener("click",()=>{

    const now=new Date();

    viewDate=startOfDay(now);
    selectedDate=startOfDay(now);

    renderCalendar();
    renderDayPanel();
});

// ===============================
// INITIALIZE
// ===============================

document.addEventListener("DOMContentLoaded",()=>{

    renderWeekdays();
    initHolidayButtons(holidayButtonsContainer);

    const now=new Date();

    viewDate=startOfDay(now);
    selectedDate=startOfDay(now);

    loadEvents();

    const addEventBtn=document.getElementById("addEventBtn");

    if(addEventBtn){
        addEventBtn.addEventListener("click",()=>{
            window.location.href="/events/new";
        });
    }
});

// ===============================
// AUTO REFRESH EVENTS
// ===============================

setInterval(()=>{
    loadEvents();
},20000);


function requestNotificationPermission() {
    if (!("Notification" in window)) return;
    if (Notification.permission === "default") {
        Notification.requestPermission();
    }
}

function checkEventReminders() {
    const settings = getUserSettings();

    if (settings.notifications !== "on") return;

    const now = new Date();
    const events = window.EVENTS || [];

    events.forEach(ev => {
        // Skip all-day events
        if (ev.all_day) return;

        const eventDate = new Date(ev.start_date + "T" + ev.start_time);
        const reminderMinutes = parseInt(ev.reminder || settings.defaultReminderMinutes || "0", 10);
        const notifyTime = new Date(eventDate.getTime() - reminderMinutes * 60000);

        // Only notify if it's within the current minute
        if (now >= notifyTime && now < new Date(notifyTime.getTime() + 60000)) {
            showReminderPopup(ev);

            // Also fire Notification API if permission granted
            if ("Notification" in window && Notification.permission === "granted") {
                const title = "Upcoming Event";
                const body = `${ev.name} at ${formatTime(ev.start_time)}${ev.location ? " • " + ev.location : ""}`;
                new Notification(title, { body, icon: "/static/img/calendar_icon.png" });
            }
        }
    });
}

// Request permission and start checking
document.addEventListener("DOMContentLoaded", () => {
    requestNotificationPermission();
    setInterval(checkEventReminders, 60000);
});