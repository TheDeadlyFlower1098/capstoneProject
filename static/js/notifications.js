// ===============================
// GLOBAL EVENT NOTIFICATIONS
// ===============================

let EVENTS = [];
const shownNotifications = new Set();
const snoozedNotifications = new Map();

function getUserSettings(){
    return JSON.parse(localStorage.getItem("planit_settings") || "{}");
}

function formatTime(timeStr) {
    if (!timeStr) return "";

    const settings = getUserSettings();
    const is24 = settings.timeFormat === "24";

    const d = new Date(`1970-01-01T${timeStr}`);

    return d.toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
        hour12: !is24
    });
}

// ===============================
// FETCH EVENTS
// ===============================
async function fetchEvents() {
    try {
        const res = await fetch("/api/events");
        EVENTS = await res.json();
    } catch (err) {
        console.error("Notification fetch failed:", err);
    }
}

// ===============================
// SHOW NOTIFICATION
// ===============================
function showNotification(ev) {
    const container = document.getElementById("notificationContainer");
    if (!container) return;

    const id = `${ev.id}-${ev.start_date}-${ev.start_time}`;

    // Prevent duplicates unless snoozed time has expired
    if (shownNotifications.has(id)) return;

    shownNotifications.add(id);

    const card = document.createElement("div");
    card.classList.add("notification-card");

    card.innerHTML = `
        <div class="notification-title">${ev.name}</div>
        <div class="notification-sub">
            ${formatTime(ev.start_time)}
            ${ev.location ? " • " + ev.location : ""}
        </div>
        <div class="notification-actions">
            <button class="notification-btn snooze-btn">Snooze</button>
            <button class="notification-btn dismiss-btn">Dismiss</button>
        </div>
    `;

    const snoozeBtn = card.querySelector(".snooze-btn");
    const dismissBtn = card.querySelector(".dismiss-btn");

    // ===============================
    // SNOOZE (5 minutes)
    // ===============================
    snoozeBtn.addEventListener("click", () => {
        const snoozeUntil = new Date(Date.now() + 5 * 60000);
        snoozedNotifications.set(id, snoozeUntil);

        container.removeChild(card);
        shownNotifications.delete(id);
    });

    // ===============================
    // DISMISS
    // ===============================
    dismissBtn.addEventListener("click", () => {
        container.removeChild(card);
        shownNotifications.delete(id);
        snoozedNotifications.delete(id);
    });

    container.appendChild(card);

    // Auto remove after 1 minute
    setTimeout(() => {
        if (container.contains(card)) {
            container.removeChild(card);
            shownNotifications.delete(id);
        }
    }, 60000);
}

// ===============================
// CHECK REMINDERS
// ===============================
function checkNotifications() {
    const settings = getUserSettings();
    if (settings.notifications === "off") return;

    const now = new Date();

    EVENTS.forEach(ev => {
        if (ev.all_day || !ev.start_time) return;

        const id = `${ev.id}-${ev.start_date}-${ev.start_time}`;

        // ===============================
        // HANDLE SNOOZE
        // ===============================
        if (snoozedNotifications.has(id)) {
            const snoozeUntil = snoozedNotifications.get(id);

            if (now < snoozeUntil) {
                return; // still snoozed
            } else {
                snoozedNotifications.delete(id); // expired → allow notify
            }
        }

        const eventDate = new Date(ev.start_date + "T" + ev.start_time);
        const reminderMinutes = parseInt(ev.reminder || 0, 10);

        if (!reminderMinutes) return;

        const notifyTime = new Date(eventDate.getTime() - reminderMinutes * 60000);

        if (now >= notifyTime && now < new Date(notifyTime.getTime() + 60000)) {
            showNotification(ev);

            if ("Notification" in window && Notification.permission === "granted") {
                new Notification("Upcoming Event", {
                    body: `${ev.name} at ${formatTime(ev.start_time)}`
                });
            }
        }
    });
}

// ===============================
// INIT
// ===============================
document.addEventListener("DOMContentLoaded", async () => {

    if ("Notification" in window && Notification.permission === "default") {
        Notification.requestPermission();
    }

    await fetchEvents();

    // refresh events every 20 sec
    setInterval(fetchEvents, 20000);

    // check every minute
    setInterval(checkNotifications, 60000);
});