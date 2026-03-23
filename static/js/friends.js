document.addEventListener("DOMContentLoaded", () => {
  // --- Tabs ---
  const tabFriends = document.getElementById("tab-friends");
  const tabRequests = document.getElementById("tab-requests");
  const panelFriends = document.getElementById("tab-panel-friends");
  const panelRequests = document.getElementById("tab-panel-requests");

  function setActiveTab(which) {
    const isFriends = which === "friends";
    tabFriends.classList.toggle("is-active", isFriends);
    tabRequests.classList.toggle("is-active", !isFriends);
    tabFriends.setAttribute("aria-selected", isFriends ? "true" : "false");
    tabRequests.setAttribute("aria-selected", !isFriends ? "true" : "false");
    panelFriends.classList.toggle("is-active", isFriends);
    panelRequests.classList.toggle("is-active", !isFriends);
  }

  tabFriends.addEventListener("click", () => setActiveTab("friends"));
  tabRequests.addEventListener("click", () => setActiveTab("requests"));

  // --- Copy friend code ---
  const copyCodeBtn = document.getElementById("copyCodeBtn");
  const myFriendCodeEl = document.getElementById("myFriendCode");
  copyCodeBtn?.addEventListener("click", async () => {
    const text = myFriendCodeEl.textContent.trim();
    try {
      await navigator.clipboard.writeText(text);
      copyCodeBtn.textContent = "Copied!";
      setTimeout(() => (copyCodeBtn.textContent = "Copy"), 900);
    } catch {
      alert(`Copy this code: ${text}`);
    }
  });

  // --- Add Friend ---
  const addFriendBtn = document.getElementById("addFriendBtn");
  const inviteCodeInput = document.getElementById("inviteCodeInput");

  addFriendBtn?.addEventListener("click", async () => {
    const code = inviteCodeInput.value.trim();
    if (!code) return inviteCodeInput.focus();

    try {
      const res = await fetch("/friends/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code })
      });
      const data = await res.json();
      alert(data.success || data.error);
      inviteCodeInput.value = "";
      // Reattach buttons in case new request comes in
      attachRequestButtons();
    } catch (err) {
      console.error(err);
      alert("Failed to send friend request.");
    }
  });

  // --- Attach Accept / Decline button listeners ---
  function attachRequestButtons() {
    panelRequests.querySelectorAll(".acceptBtn").forEach((btn) => {
      btn.removeEventListener("click", handleAccept); // remove duplicates
      btn.addEventListener("click", handleAccept);
    });

    panelRequests.querySelectorAll(".declineBtn").forEach((btn) => {
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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id })
      });
      const data = await res.json();
      alert(data.success || data.error);
      window.location.reload(); // refresh the page to update lists
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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id })
      });
      const data = await res.json();
      alert(data.success || data.error);
      window.location.reload(); // refresh to remove request
    } catch (err) {
      console.error(err);
      alert("Failed to decline friend request.");
    }
  }

  // --- Refresh Button ---
  const refreshBtn = document.getElementById("refreshFriendsBtn");
  refreshBtn?.addEventListener("click", () => window.location.reload());

  // --- Initial Load ---
  setActiveTab("friends");
  attachRequestButtons();
});