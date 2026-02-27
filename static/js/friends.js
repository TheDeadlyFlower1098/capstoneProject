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

  console.log("Elements found:", {
    tabFriends: !!tabFriends,
    tabRequests: !!tabRequests,
    panelFriends: !!panelFriends,
    panelRequests: !!panelRequests,
    copyCodeBtn: !!copyCodeBtn,
    myFriendCodeEl: !!myFriendCodeEl,
    addFriendBtn: !!addFriendBtn,
    inviteCodeInput: !!inviteCodeInput,
    refreshBtn: !!refreshBtn,
  });

  function setActiveTab(which) {
    const isFriends = which === "friends";

    tabFriends.classList.toggle("is-active", isFriends);
    tabRequests.classList.toggle("is-active", !isFriends);

    tabFriends.setAttribute("aria-selected", isFriends ? "true" : "false");
    tabRequests.setAttribute("aria-selected", !isFriends ? "true" : "false");

    panelFriends.classList.toggle("is-active", isFriends);
    panelRequests.classList.toggle("is-active", !isFriends);

    console.log("Switched tab to:", which);
  }

  if (tabFriends && tabRequests && panelFriends && panelRequests) {
    tabFriends.addEventListener("click", () => setActiveTab("friends"));
    tabRequests.addEventListener("click", () => setActiveTab("requests"));
  }

  if (copyCodeBtn && myFriendCodeEl) {
    copyCodeBtn.addEventListener("click", async () => {
      const text = (myFriendCodeEl.textContent || "").trim();
      console.log("Copy clicked:", text);

      try {
        await navigator.clipboard.writeText(text);
        copyCodeBtn.textContent = "Copied!";
        setTimeout(() => (copyCodeBtn.textContent = "Copy"), 900);
      } catch (err) {
        console.error("Clipboard failed:", err);
        alert(`Copy this code: ${text}`);
      }
    });
  }

  if (addFriendBtn && inviteCodeInput) {
    addFriendBtn.addEventListener("click", () => {
      const code = inviteCodeInput.value.trim();
      console.log("Add friend clicked:", code);

      if (!code) {
        inviteCodeInput.focus();
        return;
      }
      alert(`Invite code submitted: ${code}`);
      inviteCodeInput.value = "";
    });
  }

  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      console.log("Refresh clicked — reloading now");
      window.location.href =
        window.location.pathname + "?r=" + Date.now();
    });
  }

  // Default tab
  if (tabFriends && panelFriends) setActiveTab("friends");
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
