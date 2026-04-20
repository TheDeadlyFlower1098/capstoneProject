document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("create-event-form");
  if (!form) return;

  const allDayCheckbox = document.getElementById("all_day");
  const startInput = document.getElementById("start_time");
  const endInput = document.getElementById("end_time");
  const dateInput = document.getElementById("date");
  const endDateInput = document.getElementById("end_date"); // optional
  const hiddenColorInput = document.getElementById("selectedColor");
  const submitBtn = form.querySelector("button[type='submit']");

  // =====================================================
  // Default Date Fallback (safety in case backend misses it)
  // =====================================================
  if (dateInput && !dateInput.value) {
    const today = new Date().toISOString().split("T")[0];
    dateInput.value = today;
  }

  // =====================================================
  // ALL DAY TOGGLE
  // =====================================================
  function toggleTimeInputs() {
    if (!startInput || !endInput) return;

    if (allDayCheckbox.checked) {
      startInput.disabled = true;
      endInput.disabled = true;

      startInput.value = "";
      endInput.value = "";

      startInput.removeAttribute("required");
      endInput.removeAttribute("required");

      startInput.classList.add("disabled-input");
      endInput.classList.add("disabled-input");
    } else {
      startInput.disabled = false;
      endInput.disabled = false;

      startInput.classList.remove("disabled-input");
      endInput.classList.remove("disabled-input");
    }
  }

  if (allDayCheckbox) {
    toggleTimeInputs();
    allDayCheckbox.addEventListener("change", toggleTimeInputs);
  }

 // =====================================================
// COLOR PICKER
// =====================================================

document.addEventListener("DOMContentLoaded", function () {

  const colorOptions = document.querySelectorAll(".color-badge");
  const hiddenColorInput = document.getElementById("selectedColor");

  if (!colorOptions.length || !hiddenColorInput) return;

  colorOptions.forEach(option => {
    option.addEventListener("click", function () {

      // Remove selection from all
      colorOptions.forEach(o => o.classList.remove("selected"));

      // Add to clicked one
      this.classList.add("selected");

      // Store color value
      hiddenColorInput.value = this.dataset.color;

    });
  });

  // Ensure at least one is selected on load
  const selected = document.querySelector(".color-badge.selected");

  if (!selected) {
    colorOptions[0].classList.add("selected");
    hiddenColorInput.value = colorOptions[0].dataset.color;
  } else {
    hiddenColorInput.value = selected.dataset.color;
  }

});

  // =====================================================
  // INLINE ERROR SYSTEM
  // =====================================================
  function showInlineError(message) {
    let existing = document.querySelector(".form-error");

    if (!existing) {
      existing = document.createElement("div");
      existing.className = "flash flash-error form-error";
      form.prepend(existing);
    }

    existing.textContent = message;

    setTimeout(() => {
      if (existing) existing.remove();
    }, 4000);
  }

  function clearInlineError() {
    const existing = document.querySelector(".form-error");
    if (existing) existing.remove();
  }

  // =====================================================
  // VALIDATION
  // =====================================================
  function validateForm() {
    clearInlineError();

    if (!dateInput.value) {
      showInlineError("Start date is required.");
      return false;
    }

    // Multi-day validation
    if (endDateInput && endDateInput.value) {
      if (endDateInput.value < dateInput.value) {
        showInlineError("End date cannot be before start date.");
        return false;
      }
    }

    // Time validation (only if not all-day)
    if (!allDayCheckbox.checked) {
      if (!startInput.value || !endInput.value) {
        showInlineError("Start and end times are required.");
        return false;
      }

      if (startInput.value >= endInput.value) {
        showInlineError("End time must be after start time.");
        return false;
      }
    }

    return true;
  }

});