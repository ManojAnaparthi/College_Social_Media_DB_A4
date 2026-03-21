const TOKEN_KEY = "csm_session_token";
const USER_KEY = "csm_current_user";

let sessionToken = localStorage.getItem(TOKEN_KEY) || "";
let currentUser = null;

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
    <p><strong>Name:</strong> ${data.Name}</p>
    <p><strong>Email:</strong> ${data.Email}</p>
    <p><strong>Contact:</strong> ${data.ContactNumber ?? ""}</p>
    <p><strong>Department:</strong> ${data.Department ?? ""}</p>
    <p><strong>Age:</strong> ${data.Age ?? ""}</p>
    <p><strong>Role:</strong> ${data.Role}</p>
    <p><strong>Bio:</strong> ${data.Bio ?? ""}</p>
  `;
}

function renderPosts(posts) {
  const postList = document.getElementById("post-list");
  postList.innerHTML = "";

  posts.forEach((post) => {
    const isOwner = Number(currentUser?.member_id) === Number(post.MemberID);
    const isAdmin = currentUser?.role === "Admin";
    const canModify = isOwner || isAdmin;

    const div = document.createElement("div");
    div.className = "post-item";
    div.innerHTML = `
      <p><strong>#${post.PostID}</strong> by ${post.AuthorName} (${post.Visibility})</p>
      <p>${post.Content}</p>
      <p><small>${post.PostDate}</small></p>
      <div class="post-actions">
        <button data-action="edit" data-id="${post.PostID}" data-can-modify="${canModify}">Edit</button>
        <button data-action="delete" data-id="${post.PostID}" data-can-modify="${canModify}">Delete</button>
      </div>
    `;

    const buttons = div.querySelectorAll("button[data-can-modify='false']");
    buttons.forEach((btn) => {
      btn.disabled = true;
      btn.title = "Only post owner or admin can modify";
    });

    postList.appendChild(div);
  });
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

  const addGroupMemberForm = document.getElementById("admin-add-group-member-form");
  if (addGroupMemberForm) {
    addGroupMemberForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const groupId = document.getElementById("admin_group_id").value;
      const memberId = document.getElementById("admin_member_id").value;
      const role = document.getElementById("admin_group_role").value;

      const res = await fetch(`/admin/groups/${groupId}/members`, {
        method: "POST",
        headers: apiHeaders(),
        body: JSON.stringify({ member_id: Number(memberId), role }),
      });
      const payload = await parseApiResponse(res);
      if (!res.ok) {
        setStatus("admin-add-group-member-status", payload.detail || "Add group member failed", true);
        return;
      }
      setStatus("admin-add-group-member-status", payload.message || "Group member added");
    });
  }

  const removeGroupMemberForm = document.getElementById("admin-remove-group-member-form");
  if (removeGroupMemberForm) {
    removeGroupMemberForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const groupId = document.getElementById("admin_remove_group_id").value;
      const memberId = document.getElementById("admin_remove_member_id").value;

      const res = await fetch(`/admin/groups/${groupId}/members/${memberId}`, {
        method: "DELETE",
        headers: apiHeaders(),
      });
      const payload = await parseApiResponse(res);
      if (!res.ok) {
        setStatus("admin-remove-group-member-status", payload.detail || "Remove group member failed", true);
        return;
      }
      setStatus("admin-remove-group-member-status", payload.message || "Group member removed");
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
  });

  const memberViewForm = document.getElementById("member-view-form");
  if (memberViewForm) {
    memberViewForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!currentUser) {
        setStatus("member-view-status", "Please login first", true);
        return;
      }

      const memberId = document.getElementById("member_id_lookup").value;
      const panel = document.getElementById("member-portfolio-view");
      if (panel) {
        panel.classList.add("hidden");
      }

      const res = await fetch(`/portfolio/${memberId}`, {
        method: "GET",
        headers: apiHeaders(),
      });
      const payload = await res.json();

      if (!res.ok) {
        if (res.status === 403) {
          setStatus("member-view-status", "You do not have permission to view this profile.", true);
          return;
        }
        setStatus("member-view-status", payload.detail || "Unable to load member profile", true);
        return;
      }

      setStatus("member-view-status", payload.message || "Profile loaded");
      renderMemberPortfolio(payload.data);
    });
  }
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
    const target = e.target;
    if (!(target instanceof HTMLButtonElement)) {
      return;
    }

    const action = target.dataset.action;
    const postId = target.dataset.id;
    const canModify = target.dataset.canModify === "true";
    if (!action || !postId) {
      return;
    }

    if ((action === "edit" || action === "delete") && !canModify) {
      alert("You can only modify your own posts.");
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
