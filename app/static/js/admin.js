class AdminConsole {
  constructor() {
    this.environments = {
      production: {
        label: "Production",
        apiBaseUrl: "https://api.wobbly.site",
        stagingKey: "",
      },
      staging: {
        label: "Staging",
        apiBaseUrl: "https://staging-api.wobbly.site",
        stagingKey: "39rDOkCgTc5TfeyTsRebbSzvWycSRluR",
      },
    };
    this.state = {
      environment: this.detectEnvironment(),
      token: "",
      role: "",
      currentUserId: null,
      selectedUserId: null,
      users: [],
      admins: [],
    };
  }

  init() {
    this.cacheNodes();
    this.bindEvents();
    this.renderEnvironment();
    this.restoreToken();
  }

  cacheNodes() {
    this.currentEnvBadge = document.getElementById("current-env-badge");
    this.loginForm = document.getElementById("login-form");
    this.loginStatus = document.getElementById("login-status");
    this.usersCard = document.getElementById("users-card");
    this.usersStatus = document.getElementById("users-status");
    this.usersTableBody = document.getElementById("users-table-body");
    this.searchForm = document.getElementById("search-form");
    this.searchInput = document.getElementById("search-input");
    this.refreshUsersButton = document.getElementById("refresh-users-button");
    this.editorCard = document.getElementById("editor-card");
    this.editorUserBadge = document.getElementById("editor-user-badge");
    this.editorForm = document.getElementById("editor-form");
    this.editorUsername = document.getElementById("editor-username");
    this.editorScore = document.getElementById("editor-score");
    this.editorRating = document.getElementById("editor-rating");
    this.editorStatus = document.getElementById("editor-status");
    this.adminsCard = document.getElementById("admins-card");
    this.adminsTableBody = document.getElementById("admins-table-body");
    this.adminsStatus = document.getElementById("admins-status");
    this.adminCreateForm = document.getElementById("admin-create-form");
    this.adminLoginInput = document.getElementById("admin-login-input");
    this.adminPasswordInput = document.getElementById("admin-password-input");
    this.roleBadge = document.getElementById("role-badge");
    this.envLinks = document.querySelectorAll("[data-env-link]");
  }

  bindEvents() {
    this.loginForm.addEventListener("submit", (event) => this.handleLogin(event));
    this.searchForm.addEventListener("submit", (event) => this.handleSearch(event));
    this.refreshUsersButton.addEventListener("click", () => this.loadUsers());
    this.editorForm.addEventListener("submit", (event) => this.handleUserUpdate(event));
    this.adminCreateForm.addEventListener("submit", (event) => this.handleAdminCreate(event));
  }

  detectEnvironment() {
    const path = window.location.pathname.toLowerCase();
    if (path.indexOf("/staging") === 0) {
      return "staging";
    }
    return "production";
  }

  environmentConfig() {
    return this.environments[this.state.environment];
  }

  renderEnvironment() {
    const env = this.environmentConfig();
    let index = 0;

    this.currentEnvBadge.textContent = env.label;
    while (index < this.envLinks.length) {
      if (this.envLinks[index].dataset.envLink === this.state.environment) {
        this.envLinks[index].classList.remove("inactive");
      } else {
        this.envLinks[index].classList.add("inactive");
      }
      index += 1;
    }
  }

  storageKey() {
    return "wobbly-admin-token-" + this.state.environment;
  }

  restoreToken() {
    const token = window.localStorage.getItem(this.storageKey());
    if (!token) {
      return;
    }
    this.state.token = token;
    this.loadDashboard();
  }

  handleLogin(event) {
    event.preventDefault();
    this.loginStatus.textContent = "Входим...";
    this.loginStatus.className = "status";
    this.login().catch((error) => this.showError(this.loginStatus, error.message));
  }

  async login() {
    const response = await this.request("/admin/auth/login", {
      method: "POST",
      body: JSON.stringify({
        login: document.getElementById("login-input").value.trim(),
        password: document.getElementById("password-input").value,
      }),
    }, false);
    this.state.token = response.accessToken;
    window.localStorage.setItem(this.storageKey(), this.state.token);
    this.showOk(this.loginStatus, "Вход выполнен");
    await this.loadDashboard();
  }

  async loadDashboard() {
    const me = await this.request("/admin/me");
    this.state.role = me.role;
    this.roleBadge.textContent = me.role;
    this.usersCard.classList.remove("section-hidden");
    this.editorCard.classList.remove("section-hidden");
    this.adminsCard.classList.remove("section-hidden");
    if (me.role !== "owner") {
      this.adminCreateForm.classList.add("section-hidden");
    }
    await this.loadUsers();
    await this.loadAdmins();
  }

  handleSearch(event) {
    event.preventDefault();
    this.loadUsers().catch((error) => this.showError(this.usersStatus, error.message));
  }

  async loadUsers() {
    const search = this.searchInput.value.trim();
    const suffix = search ? "?search=" + encodeURIComponent(search) : "";
    const response = await this.request("/admin/users" + suffix);
    this.state.users = response.items;
    this.renderUsers();
    this.showOk(this.usersStatus, "Пользователи обновлены");
  }

  renderUsers() {
    let index = 0;
    let markup = "";
    while (index < this.state.users.length) {
      const user = this.state.users[index];
      markup += `
        <tr>
          <td>${user.id}</td>
          <td>${user.username || "—"}</td>
          <td>${user.score}</td>
          <td>${user.participateInRating ? "on" : "off"}</td>
          <td>${this.formatDate(user.updatedAt)}</td>
          <td><button type="button" data-user-id="${user.id}">Edit</button></td>
        </tr>
      `;
      index += 1;
    }
    this.usersTableBody.innerHTML = markup || '<tr><td colspan="6">Нет пользователей</td></tr>';
    this.bindUserButtons();
  }

  bindUserButtons() {
    const buttons = this.usersTableBody.querySelectorAll("[data-user-id]");
    let index = 0;
    while (index < buttons.length) {
      buttons[index].addEventListener("click", () => this.selectUser(buttons[index].dataset.userId));
      index += 1;
    }
  }

  selectUser(userIdValue) {
    const userId = Number(userIdValue);
    const user = this.findById(this.state.users, userId);
    if (!user) {
      return;
    }
    this.state.selectedUserId = user.id;
    this.editorUserBadge.textContent = "#" + user.id;
    this.editorUsername.value = user.username || "";
    this.editorScore.value = String(user.score);
    this.editorRating.checked = Boolean(user.participateInRating);
    this.showOk(this.editorStatus, "Пользователь загружен в форму");
  }

  handleUserUpdate(event) {
    event.preventDefault();
    if (!this.state.selectedUserId) {
      this.showError(this.editorStatus, "Сначала выбери пользователя");
      return;
    }
    this.updateUser().catch((error) => this.showError(this.editorStatus, error.message));
  }

  async updateUser() {
    const payload = {
      username: this.editorUsername.value.trim() || null,
      score: Number(this.editorScore.value),
      participateInRating: this.editorRating.checked,
    };
    const response = await this.request("/admin/users/" + this.state.selectedUserId, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    this.replaceUser(response);
    this.renderUsers();
    this.selectUser(response.id);
    this.showOk(this.editorStatus, "Пользователь сохранен");
  }

  async loadAdmins() {
    if (this.state.role !== "owner") {
      this.adminsTableBody.innerHTML = '<tr><td colspan="5">Доступно только owner</td></tr>';
      return;
    }
    const response = await this.request("/admin/admin-users");
    this.state.admins = response.items;
    this.renderAdmins();
    this.showOk(this.adminsStatus, "Администраторы обновлены");
  }

  renderAdmins() {
    let index = 0;
    let markup = "";
    while (index < this.state.admins.length) {
      const admin = this.state.admins[index];
      markup += `
        <tr>
          <td>${admin.id}</td>
          <td>${admin.login}</td>
          <td>${admin.role}</td>
          <td>${admin.isActive ? "yes" : "no"}</td>
          <td><button type="button" data-admin-id="${admin.id}" data-admin-active="${admin.isActive}">${admin.isActive ? "Disable" : "Enable"}</button></td>
        </tr>
      `;
      index += 1;
    }
    this.adminsTableBody.innerHTML = markup || '<tr><td colspan="5">Нет админов</td></tr>';
    this.bindAdminButtons();
  }

  bindAdminButtons() {
    const buttons = this.adminsTableBody.querySelectorAll("[data-admin-id]");
    let index = 0;
    while (index < buttons.length) {
      buttons[index].addEventListener("click", () => this.toggleAdmin(buttons[index]));
      index += 1;
    }
  }

  async toggleAdmin(button) {
    const adminId = Number(button.dataset.adminId);
    const isActive = button.dataset.adminActive === "true";
    await this.request("/admin/admin-users/" + adminId, {
      method: "PATCH",
      body: JSON.stringify({ isActive: !isActive }),
    });
    await this.loadAdmins();
  }

  handleAdminCreate(event) {
    event.preventDefault();
    this.createAdmin().catch((error) => this.showError(this.adminsStatus, error.message));
  }

  async createAdmin() {
    await this.request("/admin/admin-users", {
      method: "POST",
      body: JSON.stringify({
        login: this.adminLoginInput.value.trim(),
        password: this.adminPasswordInput.value,
      }),
    });
    this.adminLoginInput.value = "";
    this.adminPasswordInput.value = "";
    await this.loadAdmins();
    this.showOk(this.adminsStatus, "Новый admin создан");
  }

  async request(path, options, withAuth) {
    const finalOptions = options || {};
    const headers = {
      "Content-Type": "application/json",
    };
    const env = this.environmentConfig();

    if (env.stagingKey) {
      headers["X-Staging-Key"] = env.stagingKey;
    }

    if (withAuth !== false && this.state.token) {
      headers.Authorization = "Bearer " + this.state.token;
    }

    if (finalOptions.headers) {
      Object.assign(headers, finalOptions.headers);
    }

    const response = await fetch(env.apiBaseUrl + path, {
      method: finalOptions.method || "GET",
      headers,
      body: finalOptions.body,
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({ message: "Request failed" }));
      throw new Error(errorPayload.message || "Request failed");
    }

    return response.json();
  }

  replaceUser(updatedUser) {
    let index = 0;
    while (index < this.state.users.length) {
      if (this.state.users[index].id === updatedUser.id) {
        this.state.users[index] = updatedUser;
        return;
      }
      index += 1;
    }
    this.state.users.unshift(updatedUser);
  }

  findById(items, id) {
    let index = 0;
    while (index < items.length) {
      if (items[index].id === id) {
        return items[index];
      }
      index += 1;
    }
    return null;
  }

  formatDate(value) {
    if (!value) {
      return "—";
    }
    return new Date(value).toLocaleString();
  }

  showOk(node, message) {
    node.textContent = message;
    node.className = "status status-ok";
  }

  showError(node, message) {
    node.textContent = message;
    node.className = "status status-error";
  }
}

window.addEventListener("DOMContentLoaded", () => {
  const consoleApp = new AdminConsole();
  consoleApp.init();
});
