const saveBtn = document.getElementById("saveSettingsBtn");
const statusEl = document.getElementById("saveStatus");

const themeSelect = document.getElementById("themeSelect");
const weekStartSelect = document.getElementById("weekStartSelect");
const timeFormatSelect = document.getElementById("timeFormatSelect");
const notificationsSelect = document.getElementById("notificationsSelect");
const defaultReminderSelect = document.getElementById("defaultReminderSelect");
const shareStatusToggle = document.getElementById("shareStatusToggle");
const eventVisibilityToggle = document.getElementById("eventVisibilityToggle");

const STORAGE_KEY = "planit_settings";

function readSettingsFromForm() {
  return {
    theme: themeSelect.value, // "system" | "light" | "dark"
    weekStart: weekStartSelect.value, // "sunday" | "monday"
    timeFormat: timeFormatSelect.value, // "12" | "24"
    notifications: notificationsSelect.value, // "on" | "off"
    defaultReminderMinutes: defaultReminderSelect.value, // "none" | "10" | ...
    shareStatus: shareStatusToggle.checked,
    eventVisibility: eventVisibilityToggle.checked,
  };
}

function applySettingsToForm(settings) {
  if (!settings) return;

  if (settings.theme) themeSelect.value = settings.theme;
  if (settings.weekStart) weekStartSelect.value = settings.weekStart;
  if (settings.timeFormat) timeFormatSelect.value = settings.timeFormat;
  if (settings.notifications) notificationsSelect.value = settings.notifications;
  if (settings.defaultReminderMinutes) defaultReminderSelect.value = settings.defaultReminderMinutes;

  if (typeof settings.shareStatus === "boolean") shareStatusToggle.checked = settings.shareStatus;
  if (typeof settings.eventVisibility === "boolean") eventVisibilityToggle.checked = settings.eventVisibility;
}

function loadSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveSettings(settings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));

  // Convenience keys for other pages (calendar uses this)
  localStorage.setItem("planit_weekStart", settings.weekStart);
}

saveBtn?.addEventListener("click", () => {
  const settings = readSettingsFromForm();
  saveSettings(settings);

  // Apply theme immediately (uses theme.js)
  if (window.PlanITTheme && typeof window.PlanITTheme.applyTheme === "function") {
    window.PlanITTheme.applyTheme(settings.theme);
  }

  statusEl.textContent = "Saved ✓";
  setTimeout(() => (statusEl.textContent = ""), 1200);

  console.log("Saved settings:", settings);
});

// On load
(function init() {
  const saved = loadSettings();
  if (saved) applySettingsToForm(saved);
})();
