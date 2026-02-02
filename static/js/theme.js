// theme.js
// Applies theme globally using <html data-theme="light|dark">
//
// Source of truth:
// - localStorage "planit_settings" JSON with { theme: "system"|"light"|"dark" }
// - falls back to OS preference if theme === "system"

(function () {
  const SETTINGS_KEY = "planit_settings";

  function getSavedTheme() {
    try {
      const raw = localStorage.getItem(SETTINGS_KEY);
      const s = raw ? JSON.parse(raw) : null;
      const t = s?.theme;
      if (t === "light" || t === "dark" || t === "system") return t;
    } catch {}
    return "system";
  }

  function prefersDark() {
    return window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function resolveTheme(theme) {
    if (theme === "dark") return "dark";
    if (theme === "light") return "light";
    return prefersDark() ? "dark" : "light"; // system
  }

  function applyTheme(theme) {
    const finalTheme = resolveTheme(theme);
    document.documentElement.dataset.theme = finalTheme;
  }

  // Expose helpers so settings.js can call it immediately after saving
  window.PlanITTheme = {
    applyTheme,
    getSavedTheme,
    resolveTheme,
  };

  // Apply on initial load
  applyTheme(getSavedTheme());

  // If user has "system", update when OS theme changes
  try {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    mq.addEventListener("change", () => {
      if (getSavedTheme() === "system") applyTheme("system");
    });
  } catch {
    // Older browsers: ignore
  }
})();
