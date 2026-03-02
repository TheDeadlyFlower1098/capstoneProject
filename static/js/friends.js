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
    const email = inviteCodeInput.value.trim();
    if (!email) return inviteCodeInput.focus();

    try {
      const res = await fetch("/friends/request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      alert(data.message || data.error);
      inviteCodeInput.value = "";
      loadFriendRequests();
    } catch (err) {
      console.error(err);
    }
  });

  // --- Friend Requests (Accept / Decline) ---
  async function loadFriendRequests() {
    const panel = panelRequests;
    if (!panel) return;

    try {
      const res = await fetch("/friends/requests");
      const requests = await res.json();

      panel.innerHTML = requests.length
        ? requests
            .map(
              (r) => `
          <div class="request-card" data-request-id="${r.request_id}">
            <span>${r.name}</span>
            <span>${r.sent_at}</span>
            <button class="acceptBtn">Accept</button>
            <button class="declineBtn">Decline</button>
          </div>
        `
            )
            .join("")
        : "<p>No pending requests.</p>";

      panel.querySelectorAll(".acceptBtn").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
          const card = e.target.closest(".request-card");
          const request_id = card.dataset.requestId;
          const res = await fetch(`/friends/request/${request_id}/accept`, {
            method: "POST"
          });
          const data = await res.json();
          alert(data.message || data.error);
          loadFriendRequests();
          loadFriendsList();
        });
      });

      panel.querySelectorAll(".declineBtn").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
          const card = e.target.closest(".request-card");
          const request_id = card.dataset.requestId;
          const res = await fetch(`/friends/request/${request_id}/decline`, {
            method: "POST"
          });
          const data = await res.json();
          alert(data.message || data.error);
          loadFriendRequests();
        });
      });
    } catch (err) {
      console.error(err);
    }
  }

  // --- Friends List ---
  const friendsListPanel = panelFriends;
  async function loadFriendsList() {
    if (!friendsListPanel) return;
    try {
      const res = await fetch("/friends/list");
      const friends = await res.json();

      friendsListPanel.innerHTML = friends.length
        ? friends
            .map(
              (f) => `<div class="friend-card">
                  <span>${f.name}</span>
                </div>`
            )
            .join("")
        : "<p>No friends yet.</p>";
    } catch (err) {
      console.error(err);
    }
  }

  // --- Refresh Button ---
  const refreshBtn = document.getElementById("refreshFriendsBtn");
  refreshBtn?.addEventListener("click", () => {
    loadFriendRequests();
    loadFriendsList();
  });

  // --- Initial Load ---
  setActiveTab("friends");
  loadFriendsList();
  loadFriendRequests();
});