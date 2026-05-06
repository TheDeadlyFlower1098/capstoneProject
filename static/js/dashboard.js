// ===============================
// Dashboard JS - PlanIT
// ===============================

// Helper: handle fetch responses
async function postJSON(url, data = {}) {
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  return res.json();
}

// ===============================
// TASK TOGGLE
// ===============================
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".task-list input").forEach(checkbox => {
    checkbox.addEventListener("change", async function () {
      const taskId = this.dataset.id;

      try {
        await postJSON(`/tasks/toggle/${taskId}`);
        location.reload(); // simple refresh to update progress
      } catch (err) {
        console.error("Error toggling task:", err);
      }
    });
  });
});

// ===============================
// ADD TASK
// ===============================
async function addTask() {
  const title = prompt("Enter task name:");

  if (!title) return;

  try {
    await postJSON("/tasks/add", { title });
    location.reload();
  } catch (err) {
    console.error("Error adding task:", err);
  }
}

// ===============================
// ADD EVENT
// ===============================
async function addEvent() {
  const title = prompt("Event name:");
  if (!title) return;

  const date = prompt("Event date (e.g. Tomorrow or 2026-04-22):");
  if (!date) return;

  try {
    await postJSON("/events/add", { title, date });
    location.reload();
  } catch (err) {
    console.error("Error adding event:", err);
  }
}

// ===============================
// ADD NOTE
// ===============================
async function addNote() {
  const content = prompt("Write your note:");

  if (!content) return;

  try {
    await postJSON("/notes/add", { content });
    location.reload();
  } catch (err) {
    console.error("Error adding note:", err);
  }
}

// Update progress bar dynamically
function updateProgress(completed, total) {
  const percent = total === 0 ? 0 : Math.round((completed / total) * 100);

  const bar = document.querySelector(".progress-fill");
  const text = document.querySelector(".progress p");

  if (bar) bar.style.width = percent + "%";
  if (text) text.innerText = `${completed} of ${total} tasks completed`;
}
document.querySelectorAll(".progress-fill").forEach(el => {
  el.style.width = (el.dataset.progress || 0) + "%";
});