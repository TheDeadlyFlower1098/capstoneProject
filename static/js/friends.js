document.addEventListener("DOMContentLoaded", () => {

  // ===============================
  // TAB SYSTEM
  // ===============================

  const tabFriends = document.getElementById("tab-friends");
  const tabRequests = document.getElementById("tab-requests");
  const tabInvites = document.getElementById("tab-invites");

  const panelFriends = document.getElementById("tab-panel-friends");
  const panelRequests = document.getElementById("tab-panel-requests");
  const panelInvites = document.getElementById("tab-panel-invites");

  function setActiveTab(which) {

    if (!panelFriends || !panelRequests) return;

    // Remove all active states
    tabFriends?.classList.remove("is-active");
    tabRequests?.classList.remove("is-active");
    tabInvites?.classList.remove("is-active");

    panelFriends.classList.remove("is-active");
    panelRequests.classList.remove("is-active");
    panelInvites?.classList.remove("is-active");

    // Activate selected
    if (which === "friends") {
      tabFriends?.classList.add("is-active");
      panelFriends.classList.add("is-active");
    }

    if (which === "requests") {
      tabRequests?.classList.add("is-active");
      panelRequests.classList.add("is-active");
    }

    if (which === "invites") {
      tabInvites?.classList.add("is-active");
      panelInvites?.classList.add("is-active");
    }
  }

  tabFriends?.addEventListener("click", () => setActiveTab("friends"));
  tabRequests?.addEventListener("click", () => setActiveTab("requests"));
  tabInvites?.addEventListener("click", () => setActiveTab("invites"));



  // ===============================
  // COPY FRIEND CODE
  // ===============================

  const copyCodeBtn = document.getElementById("copyCodeBtn");
  const myFriendCodeEl = document.getElementById("myFriendCode");

  copyCodeBtn?.addEventListener("click", async () => {

    const text = myFriendCodeEl.textContent.trim();

    try {

      await navigator.clipboard.writeText(text);

      copyCodeBtn.textContent = "Copied!";

      setTimeout(() => {
        copyCodeBtn.textContent = "Copy";
      }, 900);

    } catch {

      alert(`Copy this code: ${text}`);

    }

  });



  // ===============================
  // ADD FRIEND
  // ===============================

  const addFriendBtn = document.getElementById("addFriendBtn");
  const inviteCodeInput = document.getElementById("inviteCodeInput");

  addFriendBtn?.addEventListener("click", async () => {

    const code = inviteCodeInput.value.trim();

    if (!code) {
      inviteCodeInput.focus();
      return;
    }

    try {

      const res = await fetch("/friends/add", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ code })
      });

      const data = await res.json();

      alert(data.success || data.error);

      inviteCodeInput.value = "";

      attachRequestButtons();

    } catch (err) {

      console.error(err);
      alert("Failed to send friend request.");

    }

  });



  // ===============================
  // FRIEND REQUEST BUTTONS
  // ===============================

  function attachRequestButtons() {

    panelRequests?.querySelectorAll(".acceptBtn").forEach(btn => {
      btn.removeEventListener("click", handleAccept);
      btn.addEventListener("click", handleAccept);
    });

    panelRequests?.querySelectorAll(".declineBtn").forEach(btn => {
      btn.removeEventListener("click", handleDecline);
      btn.addEventListener("click", handleDecline);
    });

  }

  async function handleAccept(e) {

    const card = e.target.closest(".request-card");
    const user_id = card.dataset.userId;

    try {

      const res = await fetch("/friends/accept", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ user_id })
      });

      const data = await res.json();

      alert(data.success || data.error);

      window.location.reload();

    } catch (err) {

      console.error(err);
      alert("Failed to accept friend request.");

    }

  }

  async function handleDecline(e) {

    const card = e.target.closest(".request-card");
    const user_id = card.dataset.userId;

    try {

      const res = await fetch("/friends/decline", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ user_id })
      });

      const data = await res.json();

      alert(data.success || data.error);

      window.location.reload();

    } catch (err) {

      console.error(err);
      alert("Failed to decline friend request.");

    }

  }



  // ===============================
  // EVENT INVITATIONS
  // ===============================

  function attachInviteButtons() {

    panelInvites?.querySelectorAll(".acceptInviteBtn").forEach(btn => {

      btn.addEventListener("click", async (e) => {

        const card = e.target.closest(".request-card");
        const event_id = card.dataset.eventId;

        const formData = new FormData();
        formData.append("response", "accepted");

        try {

          const res = await fetch(`/events/${event_id}/respond`, {
            method: "POST",
            body: formData
          });

          if (res.ok) {
            window.location.reload();
          } else {
            alert("Failed to accept invitation.");
          }

        } catch (err) {

          console.error(err);
          alert("Error accepting invitation.");

        }

      });

    });


    panelInvites?.querySelectorAll(".declineInviteBtn").forEach(btn => {

      btn.addEventListener("click", async (e) => {

        const card = e.target.closest(".request-card");
        const event_id = card.dataset.eventId;

        const formData = new FormData();
        formData.append("response", "declined");

        try {

          const res = await fetch(`/events/${event_id}/respond`, {
            method: "POST",
            body: formData
          });

          if (res.ok) {
            window.location.reload();
          } else {
            alert("Failed to decline invitation.");
          }

        } catch (err) {

          console.error(err);
          alert("Error declining invitation.");

        }

      });

    });

  }



  // ===============================
  // REFRESH BUTTON
  // ===============================

  const refreshBtn = document.getElementById("refreshFriendsBtn");

  refreshBtn?.addEventListener("click", () => {
    window.location.reload();
  });



  // ===============================
  // INITIAL LOAD
  // ===============================

  setActiveTab("friends");
  attachRequestButtons();
  attachInviteButtons();

});