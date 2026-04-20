// ---------------- DOM ELEMENTS ----------------
const saveBtn = document.getElementById("saveSettingsBtn");
const statusEl = document.getElementById("saveStatus");

const themeSelect = document.getElementById("themeSelect");
const weekStartSelect = document.getElementById("weekStartSelect");
const timeFormatSelect = document.getElementById("timeFormatSelect");
const notificationsSelect = document.getElementById("notificationsSelect");
const defaultReminderSelect = document.getElementById("defaultReminderSelect");

const shareStatusToggle =
  document.getElementById("shareStatusToggle") || { checked: true };

const eventVisibilityToggle =
  document.getElementById("eventVisibilityToggle") || { checked: true };

const profileInput = document.getElementById("profile_pic");
const avatarImg = document.querySelector(".avatar img");
const navAvatarImg = document.querySelector(".nav-profile img");

const STORAGE_KEY = "planit_settings";

// ---------------- GLOBAL SYNC KEYS ----------------
const TIME_FORMAT_KEY = "planit_timeFormat";
const WEEK_START_KEY = "planit_weekStart";

// ---------------- SETTINGS FUNCTIONS ----------------
function readSettingsFromForm() {
  return {
    theme: themeSelect.value,
    weekStart: weekStartSelect.value,
    timeFormat: timeFormatSelect.value,
    notifications: notificationsSelect.value,
    defaultReminderMinutes: defaultReminderSelect.value,
    shareStatus: shareStatusToggle.checked,
    eventVisibility: eventVisibilityToggle.checked,
  };
}

function applySettingsToForm(settings) {
  if (!settings) return;

  themeSelect.value = settings.theme ?? "system";
  weekStartSelect.value = settings.weekStart ?? "sunday";
  timeFormatSelect.value = settings.timeFormat ?? "12";
  notificationsSelect.value = settings.notifications ?? "on";
  defaultReminderSelect.value = settings.defaultReminderMinutes ?? "10";

  shareStatusToggle.checked = settings.shareStatus ?? true;
  eventVisibilityToggle.checked = settings.eventVisibility ?? true;
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

  // GLOBAL SYNC (IMPORTANT FIX)
  localStorage.setItem(TIME_FORMAT_KEY, settings.timeFormat);
  localStorage.setItem(WEEK_START_KEY, settings.weekStart);

  // triggers live update across tabs/pages
  window.dispatchEvent(new Event("planit-settings-updated"));
}

// ---------------- THEME ----------------
function applyTheme(theme) {
  const html = document.documentElement;

  if (theme === "dark") {
    html.setAttribute("data-theme", "dark");
  } else if (theme === "light") {
    html.removeAttribute("data-theme");
  } else {
    if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      html.setAttribute("data-theme", "dark");
    } else {
      html.removeAttribute("data-theme");
    }
  }
}

// ---------------- SAVE ----------------
saveBtn?.addEventListener("click", () => {
  const settings = readSettingsFromForm();

  saveSettings(settings);
  applyTheme(settings.theme);

  statusEl.textContent = "Saved ✓";
  setTimeout(() => (statusEl.textContent = ""), 1200);
});

// ---------------- PROFILE ----------------
profileInput?.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    if (avatarImg) avatarImg.src = e.target.result;
    if (navAvatarImg) navAvatarImg.src = e.target.result;
  };
  reader.readAsDataURL(file);

  const formData = new FormData();
  formData.append("profile_pic", file);

  try {
    const response = await fetch("/settings/upload_profile", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (!response.ok || result.error) {
      statusEl.textContent = "Upload failed ❌";
      return;
    }

    statusEl.textContent = "Profile updated ✓";
  } catch {
    statusEl.textContent = "Upload error ❌";
  }
});

// ---------------- INIT ----------------
(function init() {
  let saved = loadSettings();

  if (!saved) {
    saved = {
      theme: "system",
      weekStart: "sunday",
      timeFormat: "12",
      notifications: "on",
      defaultReminderMinutes: "10",
      shareStatus: true,
      eventVisibility: true,
    };

    saveSettings(saved);
  }

  applySettingsToForm(saved);
  applyTheme(saved.theme);
})();