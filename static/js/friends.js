document.addEventListener("DOMContentLoaded", () => {
  const tabFriends = document.getElementById("tab-friends");
  const tabRequests = document.getElementById("tab-requests");
  const panelFriends = document.getElementById("tab-panel-friends");
  const panelRequests = document.getElementById("tab-panel-requests");

  const copyCodeBtn = document.getElementById("copyCodeBtn");
  const myFriendCodeEl = document.getElementById("myFriendCode");

  const addFriendBtn = document.getElementById("addFriendBtn");
  const inviteCodeInput = document.getElementById("inviteCodeInput");

  const refreshBtn = document.getElementById("refreshFriendsBtn");

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

  copyCodeBtn.addEventListener("click", async () => {
    const text = myFriendCodeEl.textContent.trim();
    try {
      await navigator.clipboard.writeText(text);
      copyCodeBtn.textContent = "Copied!";
      setTimeout(() => (copyCodeBtn.textContent = "Copy"), 900);
    } catch {
      alert(`Copy this code: ${text}`);
    }
  });

  addFriendBtn.addEventListener("click", async () => {
    const code = inviteCodeInput.value.trim();
    if (!code) return inviteCodeInput.focus();

    try {
      const res = await fetch("/friends/add", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ code })
      });
      const data = await res.json();
      alert(data.success || data.error);
      inviteCodeInput.value = "";
      window.location.reload();
    } catch (err) {
      console.error(err);
    }
  });

  // Accept / Decline
  document.querySelectorAll(".acceptBtn").forEach(btn => {
    btn.addEventListener("click", async e => {
      const card = e.target.closest(".request-card");
      const user_id = card.dataset.userId;
      const res = await fetch("/friends/accept", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ user_id })
      });
      const data = await res.json();
      alert(data.success || data.error);
      window.location.reload();
    });
  });

  document.querySelectorAll(".declineBtn").forEach(btn => {
    btn.addEventListener("click", async e => {
      const card = e.target.closest(".request-card");
      const user_id = card.dataset.userId;
      const res = await fetch("/friends/decline", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ user_id })
      });
      const data = await res.json();
      alert(data.success || data.error);
      window.location.reload();
    });
  });

  refreshBtn.addEventListener("click", () => {
    window.location.href = window.location.pathname + "?r=" + Date.now();
  });

  // Default tab
  setActiveTab("friends");
});



const searchInput = document.getElementById("inviteCodeInput");

searchInput.addEventListener("input", async () => {
  const query = searchInput.value.trim();
  if (query.length < 2) return;

  const res = await fetch(`/friends/search?q=${encodeURIComponent(query)}`);
  const users = await res.json();

  console.log(users); // replace with UI rendering
  document.addEventListener("DOMContentLoaded", () => {
  const addBtn = document.getElementById("addFriendBtn");
  const input = document.getElementById("inviteCodeInput");

  addBtn.addEventListener("click", async () => {
    const value = input.value.trim();

    if (!value) {
      alert("Enter a user ID for now");
      return;
    }

    const res = await fetch("/friends/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ receiver_id: value })
    });

    const data = await res.json();

    if (!res.ok) {
      alert(data.error);
      return;
    }

    alert("Friend request sent!");
    input.value = "";
  });
});

});
