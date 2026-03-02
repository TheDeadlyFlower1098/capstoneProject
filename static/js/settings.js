// ---------------- DOM ELEMENTS ----------------
const saveBtn = document.getElementById("saveSettingsBtn");
const statusEl = document.getElementById("saveStatus");

const themeSelect = document.getElementById("themeSelect");
const weekStartSelect = document.getElementById("weekStartSelect");
const timeFormatSelect = document.getElementById("timeFormatSelect");
const notificationsSelect = document.getElementById("notificationsSelect");
const defaultReminderSelect = document.getElementById("defaultReminderSelect");
const shareStatusToggle = document.getElementById("shareStatusToggle");
const eventVisibilityToggle = document.getElementById("eventVisibilityToggle");

const profileInput = document.getElementById("profile_pic");
const avatarImg = document.querySelector(".avatar img");
const navAvatarImg = document.querySelector(".nav-profile img"); // Nav bar profile pic

const STORAGE_KEY = "planit_settings";

// ---------------- SETTINGS FUNCTIONS ----------------
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
  localStorage.setItem("planit_weekStart", settings.weekStart);
}

// ---------------- THEME HANDLING ----------------
function applyTheme(theme) {
  const html = document.documentElement;

  if (theme === "dark") {
    html.setAttribute("data-theme", "dark");
  } else if (theme === "light") {
    html.removeAttribute("data-theme");
  } else if (theme === "system") {
    // Use system preference
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      html.setAttribute("data-theme", "dark");
    } else {
      html.removeAttribute("data-theme"); // fallback to light
    }
  }
}

// ---------------- SAVE BUTTON ----------------
saveBtn?.addEventListener("click", () => {
  const settings = readSettingsFromForm();
  saveSettings(settings);

  // Apply theme immediately
  applyTheme(settings.theme);

  statusEl.textContent = "Saved ✓";
  setTimeout(() => (statusEl.textContent = ""), 1200);

  console.log("Saved settings:", settings);
});

// ---------------- PROFILE PICTURE UPLOAD ----------------
profileInput.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  // Live preview for settings + nav bar
  const reader = new FileReader();
  reader.onload = (e) => {
    avatarImg.src = e.target.result;      // Settings page
    if (navAvatarImg) navAvatarImg.src = e.target.result; // Nav bar
  };
  reader.readAsDataURL(file);

  // Upload via AJAX
  const formData = new FormData();
  formData.append("profile_pic", file);

  try {
    const response = await fetch("/settings/upload_profile", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (!response.ok || result.error) {
      console.error("Upload failed:", result.error || "Unknown error");
      statusEl.textContent = "Upload failed ❌";
      setTimeout(() => (statusEl.textContent = ""), 2000);
      return;
    }

    statusEl.textContent = "Profile picture updated ✓";
    setTimeout(() => (statusEl.textContent = ""), 2000);
    console.log("Uploaded file:", result.filename);

    // Force nav bar image reload to avoid caching old image
    if (navAvatarImg) {
      navAvatarImg.src = result.filename + "?t=" + new Date().getTime();
    }

  } catch (err) {
    console.error("Upload error:", err);
    statusEl.textContent = "Upload error ❌";
    setTimeout(() => (statusEl.textContent = ""), 2000);
  }
});

// ---------------- INITIALIZE ----------------
(function init() {
  const saved = loadSettings();
  if (saved) {
    applySettingsToForm(saved);
    applyTheme(saved.theme);
  }
})();