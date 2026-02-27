// ---------------- Theme & Sidebar JS ----------------

// ---------------- Theme Management ----------------
const SETTINGS_KEY = "planit_settings";

function getSavedTheme() {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    const settings = raw ? JSON.parse(raw) : {};
    const theme = settings.theme;
    if (theme === "light" || theme === "dark" || theme === "system") return theme;
  } catch {}
  return "system";
}

function prefersDark() {
  return window.matchMedia &&
         window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function resolveTheme(theme) {
  if (theme === "light") return "light";
  if (theme === "dark") return "dark";
  return prefersDark() ? "dark" : "light"; // system
}

function applyTheme(theme) {
  const finalTheme = resolveTheme(theme);
  document.documentElement.setAttribute("data-theme", finalTheme);
}

function saveTheme(theme) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify({ theme }));
}

// Apply saved theme on load
applyTheme(getSavedTheme());

// Smooth transition on theme change
document.documentElement.style.transition = "background 0.3s, color 0.3s";

// Toggle theme (can be called from button)
window.toggleTheme = function () {
  const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
  const newTheme = currentTheme === "light" ? "dark" : "light";
  applyTheme(newTheme);
  saveTheme(newTheme);
};

// Update theme if system preference changes and theme is 'system'
try {
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  mq.addEventListener("change", () => {
    if (getSavedTheme() === "system") applyTheme("system");
  });
} catch {}

// ---------------- Sidebar Toggle ----------------
const sidebar = document.querySelector(".sidebar");
const mainContent = document.querySelector(".main");
const toggleBtn = document.querySelector(".icon-btn");

function toggleSidebar() {
  sidebar.classList.toggle("collapsed");
  mainContent.classList.toggle("expanded");
  toggleBtn.classList.toggle("active"); // Hamburger animation
}

if (toggleBtn && sidebar && mainContent) {
  toggleBtn.addEventListener("click", (e) => {
    e.stopPropagation(); // Prevent outside-click handler
    toggleSidebar();
  });
}

// ---------------- Mobile / Responsive Handling ----------------
function handleResize() {
  if (window.innerWidth < 768) {
    sidebar.classList.add("collapsed");
    mainContent.classList.add("expanded");
    toggleBtn.classList.remove("active");
  } else {
    sidebar.classList.remove("collapsed");
    mainContent.classList.remove("expanded");
    toggleBtn.classList.remove("active");
  }
}

// Initial check
handleResize();

// Update on window resize
window.addEventListener("resize", handleResize);

// ---------------- Close sidebar on outside click (mobile) ----------------
document.addEventListener("click", (e) => {
  if (window.innerWidth < 768) {
    if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
      sidebar.classList.add("collapsed");
      mainContent.classList.add("expanded");
      toggleBtn.classList.remove("active");
    }
  }
});