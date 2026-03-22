const TOKEN_KEY = "csm_session_token";
const USER_KEY = "csm_current_user";

let sessionToken = localStorage.getItem(TOKEN_KEY) || "";
let currentUser = null;
let viewedMemberId = null;

try {
  currentUser = JSON.parse(localStorage.getItem(USER_KEY) || "null");
} catch {
  currentUser = null;
}

function apiHeaders() {
  return {
    "Content-Type": "application/json",
    "session-token": sessionToken,
  };
}

function setStatus(id, message, isError = false) {
  const el = document.getElementById(id);
  if (!el) {
    return;
  }
  el.textContent = message;
  el.className = isError ? "status error" : "status";
}

function persistSession(token, user) {
  sessionToken = token;
  currentUser = user;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearSession() {
  sessionToken = "";
  currentUser = null;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function verifySession() {
  if (!sessionToken) {
    return null;
  }

  const res = await fetch("/isAuth", {
    method: "GET",
    headers: apiHeaders(),
  });

  if (!res.ok) {
    clearSession();
    return null;
  }

  const payload = await res.json();
  currentUser = payload;
  localStorage.setItem(USER_KEY, JSON.stringify(payload));
  return payload;
}

function redirectTo(url) {
  window.location.href = url;
}

function isAdminUser() {
  return currentUser?.role === "Admin";
}

async function parseApiResponse(res) {
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return await res.json();
  }
  const text = await res.text();
  return { detail: text || "Unexpected server response" };
}

function setupHamburgerAndLogout() {
  const toggle = document.getElementById("menu-toggle");
  const menu = document.getElementById("mobile-nav");
  const logoutBtn = document.getElementById("logout-btn");

  if (toggle && menu) {
    toggle.addEventListener("click", () => {
      menu.classList.toggle("hidden");
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      if (sessionToken) {
        try {
          await fetch("/logout", {
            method: "POST",
            headers: apiHeaders(),
          });
        } catch {
          // Ignore network failure and still clear client session.
        }
      }
      clearSession();
      redirectTo("/static/login.html");
    });
  }
}

async function requireAuth() {
  const user = await verifySession();
  if (!user) {
    redirectTo("/static/login.html");
    return null;
  }
  return user;
}

function renderPortfolio(data) {
  const panel = document.getElementById("portfolio-view");
  panel.innerHTML = `
    <p><strong>Name:</strong> ${data.Name}</p>
    <p><strong>Email:</strong> ${data.Email}</p>
    <p><strong>Contact:</strong> ${data.ContactNumber ?? ""}</p>
    <p><strong>Department:</strong> ${data.Department ?? ""}</p>
    <p><strong>Age:</strong> ${data.Age ?? ""}</p>
    <p><strong>Role:</strong> ${data.Role}</p>
    <p><strong>Followers:</strong> ${data.FollowerCount ?? 0}</p>
    <p><strong>Following:</strong> ${data.FollowingCount ?? 0}</p>
    <p><strong>Bio:</strong> ${data.Bio ?? ""}</p>
  `;

  document.getElementById("bio").value = data.Bio ?? "";
  document.getElementById("contact_number").value = data.ContactNumber ?? "";
  document.getElementById("department").value = data.Department ?? "";
  document.getElementById("age").value = data.Age ?? "";
}

function renderMemberPortfolio(data) {
  const panel = document.getElementById("member-portfolio-view");
  if (!panel) {
    return;
  }
  panel.classList.remove("hidden");
  panel.innerHTML = `
    <p><strong>Member ID:</strong> ${data.MemberID}</p>
    <p><strong>Name:</strong> ${data.Name}</p>
    <p><strong>Email:</strong> ${data.Email}</p>
    <p><strong>Contact:</strong> ${data.ContactNumber ?? ""}</p>
    <p><strong>Department:</strong> ${data.Department ?? ""}</p>
    <p><strong>Age:</strong> ${data.Age ?? ""}</p>
    <p><strong>Role:</strong> ${data.Role}</p>
    <p><strong>Followers:</strong> ${data.FollowerCount ?? 0}</p>
    <p><strong>Following:</strong> ${data.FollowingCount ?? 0}</p>
    <p><strong>Bio:</strong> ${data.Bio ?? ""}</p>
  `;
}

function syncMemberAdminEditPanel(data) {
  const panel = document.getElementById("member-admin-edit-panel");
  if (!panel) {
    return;
  }

  if (!isAdminUser()) {
    panel.classList.add("hidden");
    return;
  }

  panel.classList.remove("hidden");

  const target = document.getElementById("member-admin-edit-target");
  if (target) {
    target.textContent = `Editing member #${data.MemberID} (${data.Name})`;
  }

  const bio = document.getElementById("member_admin_bio");
  const contact = document.getElementById("member_admin_contact_number");
  const department = document.getElementById("member_admin_department");
  const age = document.getElementById("member_admin_age");

  if (bio) bio.value = data.Bio ?? "";
  if (contact) contact.value = data.ContactNumber ?? "";
  if (department) department.value = data.Department ?? "";
  if (age) age.value = data.Age ?? "";
}

function renderFollowList(listId, rows) {
  const list = document.getElementById(listId);
  if (!list) {
    return;
  }

  list.innerHTML = "";
  if (!rows || rows.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No entries";
    list.appendChild(li);
    return;
  }

  rows.forEach((row) => {
    const li = document.createElement("li");
    li.textContent = `#${row.MemberID} ${row.Name} (${row.Role}, ${row.Department ?? "N/A"})`;
    list.appendChild(li);
  });
}

function setMemberFollowActions(data) {
  const actions = document.getElementById("member-follow-actions");
  const toggleBtn = document.getElementById("follow-toggle-btn");

  if (!actions || !toggleBtn) {
    return;
  }

  if (!data?.ViewerCanFollow) {
    actions.classList.add("hidden");
    toggleBtn.dataset.following = "false";
    toggleBtn.textContent = "Follow";
    return;
  }

  actions.classList.remove("hidden");
  const alreadyFollowing = Boolean(data.ViewerIsFollowing);
  toggleBtn.dataset.following = alreadyFollowing ? "true" : "false";
  toggleBtn.textContent = alreadyFollowing ? "Unfollow" : "Follow";
}

async function loadMemberNetworkData(memberId) {
  const [followersRes, followingRes] = await Promise.all([
    fetch(`/members/${memberId}/followers?limit=50`, { method: "GET", headers: apiHeaders() }),
    fetch(`/members/${memberId}/following?limit=50`, { method: "GET", headers: apiHeaders() }),
  ]);

  const followersPayload = await parseApiResponse(followersRes);
  const followingPayload = await parseApiResponse(followingRes);

  if (!followersRes.ok) {
    setStatus("member-network-status", followersPayload.detail || "Failed to load followers", true);
    return;
  }
  if (!followingRes.ok) {
    setStatus("member-network-status", followingPayload.detail || "Failed to load following", true);
    return;
  }

  renderFollowList("member-followers-list", followersPayload.data || []);
  renderFollowList("member-following-list", followingPayload.data || []);
  setStatus("member-network-status", "Followers and following loaded");
}

async function refreshViewedMember() {
  if (!viewedMemberId) {
    return;
  }

  const res = await fetch(`/portfolio/${viewedMemberId}`, {
    method: "GET",
    headers: apiHeaders(),
  });
  const payload = await parseApiResponse(res);
  if (!res.ok) {
    setStatus("member-view-status", payload.detail || "Unable to reload member profile", true);
    return;
  }

  renderMemberPortfolio(payload.data);
  syncMemberAdminEditPanel(payload.data);
  setMemberFollowActions(payload.data);
  await loadMemberNetworkData(viewedMemberId);
  await loadMemberPosts(viewedMemberId);
}

async function loadMemberPosts(memberId) {
  const res = await fetch(`/members/${memberId}/posts?limit=30&offset=0`, {
    method: "GET",
    headers: apiHeaders(),
  });
  const payload = await parseApiResponse(res);
  if (!res.ok) {
    setStatus("member-post-status", payload.detail || "Failed to load member posts", true);
    return;
  }

  renderMemberPosts(payload.data || []);
  setStatus("member-post-status", `${payload.count ?? 0} post(s) loaded`);
}

async function loadMyNetworkData() {
  if (!currentUser?.member_id) {
    return;
  }

  const memberId = Number(currentUser.member_id);
  const [followersRes, followingRes] = await Promise.all([
    fetch(`/members/${memberId}/followers?limit=50`, { method: "GET", headers: apiHeaders() }),
    fetch(`/members/${memberId}/following?limit=50`, { method: "GET", headers: apiHeaders() }),
  ]);

  const followersPayload = await parseApiResponse(followersRes);
  const followingPayload = await parseApiResponse(followingRes);

  if (!followersRes.ok) {
    setStatus("my-network-status", followersPayload.detail || "Failed to load followers", true);
    return;
  }
  if (!followingRes.ok) {
    setStatus("my-network-status", followingPayload.detail || "Failed to load following", true);
    return;
  }

  renderFollowList("my-followers-list", followersPayload.data || []);
  renderFollowList("my-following-list", followingPayload.data || []);
  setStatus("my-network-status", "Followers and following loaded");
}

async function loadMyPosts() {
  if (!currentUser?.member_id) {
    return;
  }

  const memberId = Number(currentUser.member_id);
  const res = await fetch(`/members/${memberId}/posts?limit=30&offset=0`, {
    method: "GET",
    headers: apiHeaders(),
  });
  const payload = await parseApiResponse(res);
  if (!res.ok) {
    setStatus("my-post-status", payload.detail || "Failed to load posts", true);
    return;
  }

  renderPostsInto("my-post-list", payload.data || [], false);
  setStatus("my-post-status", `${payload.count ?? 0} post(s) loaded`);
}

async function loadMemberProfile(memberIdRaw) {
  if (!currentUser) {
    setStatus("member-view-status", "Please login first", true);
    return;
  }

  const memberId = Number(memberIdRaw);
  if (!Number.isInteger(memberId) || memberId < 1) {
    setStatus("member-view-status", "Enter a valid Member ID", true);
    return;
  }

  viewedMemberId = memberId;
  const panel = document.getElementById("member-portfolio-view");
  if (panel) {
    panel.classList.add("hidden");
  }

  const res = await fetch(`/portfolio/${memberId}`, {
    method: "GET",
    headers: apiHeaders(),
  });
  const payload = await parseApiResponse(res);

  if (!res.ok) {
    setStatus("member-view-status", payload.detail || "Unable to load member profile", true);
    return;
  }

  setStatus("member-view-status", payload.message || "Profile loaded");
  renderMemberPortfolio(payload.data);
  syncMemberAdminEditPanel(payload.data);
  setMemberFollowActions(payload.data);
  await loadMemberNetworkData(viewedMemberId);
  await loadMemberPosts(viewedMemberId);
}

function renderPostsInto(containerId, posts, allowOwnerMenu = true) {
  const postList = document.getElementById(containerId);
  if (!postList) {
    return;
  }
  postList.innerHTML = "";

  posts.forEach((post) => {
    const isOwner = Number(currentUser?.member_id) === Number(post.MemberID);
    const isAdmin = isAdminUser();
    const canEdit = isOwner;
    const canDelete = isOwner || isAdmin;
    const viewerHasLiked = Boolean(post.ViewerHasLiked);

    const div = document.createElement("div");
    div.className = "post-item";
    const ownerActions = allowOwnerMenu && canDelete
      ? `
      <details class="post-menu">
        <summary title="Post actions">...</summary>
        <div class="post-menu-items">
          ${canEdit ? `<button data-action="edit" data-id="${post.PostID}" data-edit-allowed="true">Edit</button>` : ""}
          <button data-action="delete" data-id="${post.PostID}" data-delete-allowed="true">Delete</button>
        </div>
      </details>
    `
      : "";

    div.innerHTML = `
      <div class="post-header-row">
        <p class="post-header-text"><strong>#${post.PostID}</strong> by <a href="/static/member-profile.html?member_id=${post.MemberID}">${post.AuthorName}</a> (${post.Visibility})</p>
        ${ownerActions}
      </div>
      <p>${post.Content}</p>
        <div class="like-row">
        <button type="button" class="like-toggle-icon ${viewerHasLiked ? "liked" : ""}" data-action="toggle-like" data-id="${post.PostID}" data-liked="${viewerHasLiked ? "true" : "false"}" title="Toggle like" aria-label="Toggle like">
            <span class="like-icon" aria-hidden="true">&#9829;</span>
          </button>
          <span class="like-count">${post.LikeCount ?? 0}</span>
        </div>
      <p><small>${post.PostDate}</small></p>
    `;

    postList.appendChild(div);
  });
}

function renderPosts(posts) {
  renderPostsInto("post-list", posts, true);
}

function renderMemberPosts(posts) {
  renderPostsInto("member-post-list", posts, false);
}

function renderMemberSearchResults(rows) {
  const list = document.getElementById("member-search-results");
  if (!list) {
    return;
  }

  list.innerHTML = "";
  if (!rows || rows.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No members found";
    list.appendChild(li);
    return;
  }

  rows.forEach((row) => {
    const li = document.createElement("li");
    li.innerHTML = `<a href="/static/member-profile.html?member_id=${row.MemberID}">#${row.MemberID} ${row.Name}</a> - ${row.Email} (${row.Role}, ${row.Department ?? "N/A"})`;
    list.appendChild(li);
  });
}

function getLikeCountElement(toggleButton) {
  return toggleButton.parentElement?.querySelector(".like-count") || null;
}

function applyLikeUI(toggleButton, liked, likeCount) {
  toggleButton.dataset.liked = liked ? "true" : "false";
  toggleButton.classList.toggle("liked", liked);
  const likeCountEl = getLikeCountElement(toggleButton);
  if (likeCountEl) {
    likeCountEl.textContent = String(likeCount);
  }
}

async function handleLikeToggle(toggleButton, statusId) {
  if (toggleButton.dataset.busy === "true") {
    return;
  }

  const postId = toggleButton.dataset.id;
  if (!postId) {
    return;
  }

  const currentlyLiked = toggleButton.dataset.liked === "true";
  const likeCountEl = getLikeCountElement(toggleButton);
  const currentCount = likeCountEl ? Number(likeCountEl.textContent || "0") : 0;
  const nextLiked = !currentlyLiked;
  const nextCount = Math.max(currentCount + (nextLiked ? 1 : -1), 0);

  // Optimistic update for snappy UX while request is in-flight.
  applyLikeUI(toggleButton, nextLiked, nextCount);
  toggleButton.dataset.busy = "true";
  toggleButton.disabled = true;

  const res = await fetch(`/posts/${postId}/like/toggle`, {
    method: "POST",
    headers: apiHeaders(),
  });
  const payload = await parseApiResponse(res);

  toggleButton.dataset.busy = "false";
  toggleButton.disabled = false;

  if (!res.ok) {
    applyLikeUI(toggleButton, currentlyLiked, currentCount);
    setStatus(statusId, payload.detail || "Like toggle failed", true);
    return;
  }

  applyLikeUI(toggleButton, Boolean(payload.liked), Number(payload.like_count ?? 0));
}

function initAdminControls() {
  const adminPanel = document.getElementById("admin-panel");
  if (!adminPanel) {
    return;
  }

  if (!isAdminUser()) {
    adminPanel.classList.add("hidden");
    return;
  }

  adminPanel.classList.remove("hidden");

  const deleteMemberForm = document.getElementById("admin-delete-member-form");
  if (deleteMemberForm) {
    deleteMemberForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const memberId = document.getElementById("admin_delete_member_id").value;
      const res = await fetch(`/admin/members/${memberId}`, {
        method: "DELETE",
        headers: apiHeaders(),
      });
      const payload = await parseApiResponse(res);
      if (!res.ok) {
        setStatus("admin-delete-member-status", payload.detail || "Delete member failed", true);
        return;
      }
      setStatus("admin-delete-member-status", payload.message || "Member deleted");
    });
  }
}

async function fetchMyPortfolio() {
  if (!currentUser || !currentUser.member_id) {
    setStatus("portfolio-status", "Session user not available", true);
    return;
  }

  const res = await fetch(`/portfolio/${currentUser.member_id}`, {
    method: "GET",
    headers: apiHeaders(),
  });
  const payload = await res.json();

  if (!res.ok) {
    setStatus("portfolio-status", payload.detail || "Failed to load portfolio", true);
    return;
  }

  renderPortfolio(payload.data);
}

async function fetchPosts() {
  const res = await fetch("/posts?limit=30&offset=0", {
    method: "GET",
    headers: apiHeaders(),
  });
  const payload = await res.json();

  if (!res.ok) {
    setStatus("post-create-status", payload.detail || "Failed to load posts", true);
    return;
  }

  renderPosts(payload.data || []);
}

function initLoginPage() {
  verifySession().then((user) => {
    if (user) {
      redirectTo("/static/portfolio.html");
    }
  });

  const form = document.getElementById("login-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    setStatus("auth-status", "Signing in...");

    try {
      const res = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const payload = await parseApiResponse(res);

      if (!res.ok) {
        setStatus("auth-status", payload.detail || "Login failed", true);
        return;
      }

      sessionToken = payload.session_token;
      const user = await verifySession();
      if (!user) {
        setStatus("auth-status", "Session validation failed", true);
        return;
      }

      persistSession(payload.session_token, user);
      redirectTo("/static/portfolio.html");
    } catch (err) {
      setStatus("auth-status", "Unable to reach server. Check API and database connection.", true);
      console.error("Login error:", err);
    }
  });
}

function initSignupPage() {
  verifySession().then((user) => {
    if (user) {
      redirectTo("/static/portfolio.html");
    }
  });

  const form = document.getElementById("signup-form");
  if (!form) {
    return;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    setStatus("signup-status", "Creating account...");

    const body = {
      name: document.getElementById("signup_name").value,
      email: document.getElementById("signup_email").value,
      contact_number: document.getElementById("signup_contact").value,
      college_id: document.getElementById("signup_college_id").value,
      department: document.getElementById("signup_department").value,
      age: document.getElementById("signup_age").value ? Number(document.getElementById("signup_age").value) : null,
      bio: document.getElementById("signup_bio").value || null,
      password: document.getElementById("signup_password").value,
    };

    try {
      const res = await fetch("/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const payload = await parseApiResponse(res);

      if (!res.ok) {
        setStatus("signup-status", payload.detail || "Signup failed", true);
        return;
      }

      setStatus("signup-status", "Signup successful. Redirecting to login...");
      setTimeout(() => redirectTo("/static/login.html"), 900);
    } catch (err) {
      setStatus("signup-status", "Unable to reach server. Check API and database connection.", true);
      console.error("Signup error:", err);
    }
  });
}

function initPortfolioPage() {
  setupHamburgerAndLogout();
  requireAuth().then((user) => {
    if (!user) {
      return;
    }
    fetchMyPortfolio();
    loadMyNetworkData();
    loadMyPosts();
    initAdminControls();
  });

  const form = document.getElementById("portfolio-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentUser) {
      setStatus("portfolio-status", "Please login first", true);
      return;
    }

    const body = {
      bio: document.getElementById("bio").value,
      contact_number: document.getElementById("contact_number").value,
      department: document.getElementById("department").value,
      age: document.getElementById("age").value ? Number(document.getElementById("age").value) : null,
    };

    const res = await fetch(`/portfolio/${currentUser.member_id}`, {
      method: "PUT",
      headers: apiHeaders(),
      body: JSON.stringify(body),
    });
    const payload = await res.json();

    if (!res.ok) {
      setStatus("portfolio-status", payload.detail || "Update failed", true);
      return;
    }

    setStatus("portfolio-status", payload.message || "Portfolio updated");
    await fetchMyPortfolio();
    await loadMyNetworkData();
    await loadMyPosts();
  });

  const myPostList = document.getElementById("my-post-list");
  if (myPostList) {
    myPostList.addEventListener("click", async (e) => {
      const clicked = e.target;
      if (!(clicked instanceof Element)) {
        return;
      }

      const target = clicked.closest("button[data-action]");
      if (!(target instanceof HTMLButtonElement)) {
        return;
      }

      if (target.dataset.action !== "toggle-like") {
        return;
      }

      await handleLikeToggle(target, "my-post-status");
    });
  }

}

function initMemberProfilePage() {
  setupHamburgerAndLogout();
  requireAuth().then(async (user) => {
    if (!user) {
      return;
    }

    const params = new URLSearchParams(window.location.search);
    const memberId = params.get("member_id");
    if (!memberId) {
      setStatus("member-view-status", "Missing member_id in URL", true);
      return;
    }
    await loadMemberProfile(memberId);
  });

  const toggleBtn = document.getElementById("follow-toggle-btn");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", async () => {
      if (!viewedMemberId) {
        setStatus("member-follow-action-status", "Load a member profile first", true);
        return;
      }

      const isFollowing = toggleBtn.dataset.following === "true";
      const method = isFollowing ? "DELETE" : "POST";
      const pendingText = isFollowing ? "Unfollowing..." : "Following...";
      const failureText = isFollowing ? "Unfollow failed" : "Follow failed";

      setStatus("member-follow-action-status", pendingText);
      toggleBtn.disabled = true;

      const res = await fetch(`/members/${viewedMemberId}/follow`, {
        method,
        headers: apiHeaders(),
      });
      const payload = await parseApiResponse(res);
      toggleBtn.disabled = false;

      if (!res.ok) {
        setStatus("member-follow-action-status", payload.detail || failureText, true);
        return;
      }

      setStatus("member-follow-action-status", payload.message || "Updated follow status");
      await refreshViewedMember();
    });
  }

  const memberPostList = document.getElementById("member-post-list");
  if (memberPostList) {
    memberPostList.addEventListener("click", async (e) => {
      const clicked = e.target;
      if (!(clicked instanceof Element)) {
        return;
      }

      const target = clicked.closest("button[data-action]");
      if (!(target instanceof HTMLButtonElement)) {
        return;
      }

      const action = target.dataset.action;
      if (action !== "toggle-like") {
        return;
      }

      await handleLikeToggle(target, "member-post-status");
    });
  }

  const memberAdminEditForm = document.getElementById("member-admin-edit-form");
  if (memberAdminEditForm) {
    memberAdminEditForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      if (!isAdminUser()) {
        setStatus("member-admin-edit-status", "Admin access required", true);
        return;
      }

      if (!viewedMemberId) {
        setStatus("member-admin-edit-status", "Load a member profile first", true);
        return;
      }

      const body = {
        bio: document.getElementById("member_admin_bio")?.value ?? "",
        contact_number: document.getElementById("member_admin_contact_number")?.value ?? "",
        department: document.getElementById("member_admin_department")?.value ?? "",
        age: document.getElementById("member_admin_age")?.value
          ? Number(document.getElementById("member_admin_age").value)
          : null,
      };

      const res = await fetch(`/portfolio/${viewedMemberId}`, {
        method: "PUT",
        headers: apiHeaders(),
        body: JSON.stringify(body),
      });
      const payload = await parseApiResponse(res);

      if (!res.ok) {
        setStatus("member-admin-edit-status", payload.detail || "Update failed", true);
        return;
      }

      setStatus("member-admin-edit-status", payload.message || "Profile updated");
      await refreshViewedMember();
    });
  }
}

function initSearchMembersPage() {
  setupHamburgerAndLogout();
  requireAuth().then((user) => {
    if (!user) {
      return;
    }
  });

  const form = document.getElementById("member-search-form");
  if (!form) {
    return;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = document.getElementById("member_search_query").value.trim();
    if (!query) {
      setStatus("member-search-status", "Enter a name or email", true);
      return;
    }

    setStatus("member-search-status", "Searching...");
    const res = await fetch(`/members/search?q=${encodeURIComponent(query)}&limit=30`, {
      method: "GET",
      headers: apiHeaders(),
    });
    const payload = await parseApiResponse(res);
    if (!res.ok) {
      setStatus("member-search-status", payload.detail || "Search failed", true);
      return;
    }

    setStatus("member-search-status", `${payload.count ?? 0} member(s) found`);
    renderMemberSearchResults(payload.data || []);
  });
}

function initPostsPage() {
  setupHamburgerAndLogout();
  requireAuth().then((user) => {
    if (!user) {
      return;
    }
    fetchPosts();
  });

  document.getElementById("refresh-posts").addEventListener("click", async () => {
    if (!currentUser) {
      setStatus("post-create-status", "Please login first", true);
      return;
    }
    await fetchPosts();
  });

  document.getElementById("post-list").addEventListener("click", async (e) => {
    const clicked = e.target;
    if (!(clicked instanceof Element)) {
      return;
    }

    const target = clicked.closest("button[data-action]");
    if (!(target instanceof HTMLButtonElement)) {
      return;
    }

    const action = target.dataset.action;
    const postId = target.dataset.id;
    const editAllowed = target.dataset.editAllowed === "true";
    const deleteAllowed = target.dataset.deleteAllowed === "true";
    if (!action || !postId) {
      return;
    }

    if (action === "toggle-like") {
      await handleLikeToggle(target, "post-create-status");
      return;
    }

    if (action === "edit" && !editAllowed) {
      return;
    }

    if (action === "delete" && !deleteAllowed) {
      return;
    }

    if (action === "delete") {
      const confirmed = confirm("Are you sure you want to delete this post?");
      if (!confirmed) {
        return;
      }

      const res = await fetch(`/posts/${postId}`, {
        method: "DELETE",
        headers: apiHeaders(),
      });
      const payload = await res.json();
      if (!res.ok) {
        if (res.status === 403) {
          alert(payload.detail || "You cannot modify this post.");
          return;
        }
        setStatus("post-create-status", payload.detail || "Delete failed", true);
        return;
      }
      setStatus("post-create-status", payload.message || "Post deleted");
      await fetchPosts();
      return;
    }

    if (action === "edit") {
      const newContent = prompt("Enter updated post content:");
      if (newContent === null) {
        return;
      }

      const res = await fetch(`/posts/${postId}`, {
        method: "PUT",
        headers: apiHeaders(),
        body: JSON.stringify({ content: newContent }),
      });
      const payload = await res.json();

      if (!res.ok) {
        if (res.status === 403) {
          alert(payload.detail || "You cannot modify this post.");
          return;
        }
        setStatus("post-create-status", payload.detail || "Update failed", true);
        return;
      }

      setStatus("post-create-status", payload.message || "Post updated");
      await fetchPosts();
    }
  });
}

function initCreatePostPage() {
  setupHamburgerAndLogout();
  requireAuth().then((user) => {
    if (!user) {
      return;
    }
  });

  document.getElementById("post-create-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentUser) {
      setStatus("post-create-status", "Please login first", true);
      return;
    }

    const body = {
      content: document.getElementById("post_content").value,
      media_url: document.getElementById("post_media_url").value || null,
      media_type: document.getElementById("post_media_type").value,
      visibility: document.getElementById("post_visibility").value,
    };

    const res = await fetch("/posts", {
      method: "POST",
      headers: apiHeaders(),
      body: JSON.stringify(body),
    });
    const payload = await res.json();

    if (!res.ok) {
      setStatus("post-create-status", payload.detail || "Create failed", true);
      return;
    }

    setStatus("post-create-status", "Post created. Redirecting to posts page...");
    redirectTo("/static/posts.html");
  });
}

const page = document.body.dataset.page;

if (page === "login") {
  initLoginPage();
}

if (page === "signup") {
  initSignupPage();
}

if (page === "portfolio") {
  initPortfolioPage();
}

if (page === "posts") {
  initPostsPage();
}

if (page === "create-post") {
  initCreatePostPage();
}

if (page === "search-members") {
  initSearchMembersPage();
}

if (page === "member-profile") {
  initMemberProfilePage();
}
