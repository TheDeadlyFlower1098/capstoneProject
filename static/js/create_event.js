document.addEventListener("DOMContentLoaded", function () {
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("create-event-form");
  if (!form) return;

  const allDayCheckbox = document.getElementById("all_day");
  const startInput = document.getElementById("start_time");
  const endInput = document.getElementById("end_time");

  // ============================
  // All-Day Toggle Logic
  // ============================
  function toggleTimeInputs() {
    if (allDayCheckbox.checked) {
      startInput.disabled = true;
      endInput.disabled = true;
      startInput.classList.add("disabled-input");
      endInput.classList.add("disabled-input");
      startInput.value = "";
      endInput.value = "";
    } else {
      startInput.disabled = false;
      endInput.disabled = false;
      startInput.classList.remove("disabled-input");
      endInput.classList.remove("disabled-input");
    }
  }

  // Initialize on page load
  toggleTimeInputs();
  allDayCheckbox.addEventListener("change", toggleTimeInputs);

  // ============================
  // Form Submission
  // ============================
  form.addEventListener("submit", function (e) {
    // Remove times from submission if all-day is checked
    if (allDayCheckbox.checked) {
      startInput.value = "";
      endInput.value = "";
    } else {
      // Optional: simple inline validation
      if (startInput.value && endInput.value && startInput.value >= endInput.value) {
        alert("End time must be after start time.");
        e.preventDefault();
        return;
      }
    }
  });
});

  // ============================
  // Inline Time Validation
  // ============================
  function showInlineError(message) {
    let existing = document.querySelector(".form-error");
    if (!existing) {
      existing = document.createElement("div");
      existing.className = "flash flash-error form-error";
      form.prepend(existing);
    }
    existing.textContent = message;
    setTimeout(() => existing.remove(), 4000);
  }

  // ============================
  // AJAX Form Submission
  // ============================
  form.addEventListener("submit", function (e) {
    e.preventDefault();

    if (!allDayCheckbox.checked) {
      const start = startInput?.value;
      const end = endInput?.value;
      if (start && end && start >= end) {
        showInlineError("End time must be after start time.");
        return;
      }
    }

    const formData = new FormData(form);

    fetch(form.action, {
      method: "POST",
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          showInlineError(data.error);
        } else {
          window.location.href = "/calendar";
        }
      })
      .catch(err => {
        showInlineError("Error creating event.");
        console.error(err);
      });
  });

  // ============================
  // Color Picker Logic
  // ============================
  const colorOptions = document.querySelectorAll(".color-badge");
  const hiddenColorInput = document.getElementById("selectedColor");
  if (colorOptions.length && hiddenColorInput) {
    colorOptions.forEach(option => {
      option.addEventListener("click", () => {
        colorOptions.forEach(o => o.classList.remove("selected"));
        option.classList.add("selected");
        hiddenColorInput.value = option.dataset.color;
      });
    });
  }

  // ============================
  // Friend Invites / Comments (optional)
  // ============================
  const eventIdInput = document.getElementById("event_id");
  const eventId = eventIdInput ? eventIdInput.value : null;

  if (eventId) {
    // Poll invites every 10s
    setInterval(() => {
      fetch(`/api/events/${eventId}`)
        .then(res => res.json())
        .then(event => {
          const container = document.getElementById("invites-container");
          if (!container) return;
          container.innerHTML = "";
          event.accepted_users.forEach(u => {
            const img = document.createElement("img");
            img.src = `/static/profile_pics/${u.profile_pic}`;
            img.classList.add("invite-avatar");
            container.appendChild(img);
          });
        });
    }, 10000);

    // Poll comments every 10s
    function fetchComments() {
      fetch(`/api/event/${eventId}/comments`)
        .then(res => res.json())
        .then(data => {
          const container = document.getElementById("comments-container");
          if (!container) return;
          container.innerHTML = "";
          data.forEach(c => {
            const div = document.createElement("div");
            div.classList.add("comment-entry");
            div.innerHTML = `
              <img src="/static/profile_pics/${c.profile_pic}" class="invite-avatar">
              <b>${c.user}</b>: ${c.content} <small>${c.created_at}</small>`;
            container.appendChild(div);
          });
        });
    }

    const commentForm = document.getElementById("comment-form");
    if (commentForm) {
      commentForm.addEventListener("submit", e => {
        e.preventDefault();
        const content = document.getElementById("comment-input").value;
        fetch(`/api/event/${eventId}/comments`, {
          method: "POST",
          headers: {"Content-Type": "application/x-www-form-urlencoded"},
          body: `content=${encodeURIComponent(content)}`
        }).then(() => {
          document.getElementById("comment-input").value = "";
          fetchComments();
        });
      });

      fetchComments();
      setInterval(fetchComments, 10000);
    }
  }
});