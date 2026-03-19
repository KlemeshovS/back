class AdminConsole {
  constructor() {
    this.state = {
      environment: this.detectEnvironment(),
      session: null,
      activeScreen: "overview",
      overview: null,
      users: [],
      admins: [],
      audit: [],
      selectedUserId: null,
    };
  }

  init() {
    this.cacheNodes();
    this.bindEvents();
    this.renderEnvironment();
    this.restoreSession();
  }

  cacheNodes() {
    this.envLinks = document.querySelectorAll("[data-env-link]");
    this.screenLinks = document.querySelectorAll("[data-screen-link]");
    this.screenTitle = document.getElementById("screen-title");
    this.loginEnvBadge = document.getElementById("login-env-badge");
    this.currentEnvBadge = document.getElementById("current-env-badge");
    this.currentAdminBadge = document.getElementById("current-admin-badge");
    this.currentAdminTopbarBadge = document.getElementById("current-admin-topbar-badge");
    this.roleBadge = document.getElementById("role-badge");
    this.adminsRoleBadge = document.getElementById("admins-role-badge");
    this.loginView = document.getElementById("login-view");
    this.dashboardView = document.getElementById("dashboard-view");
    this.screenNav = document.getElementById("screen-nav");
    this.sidebarFooter = document.getElementById("sidebar-footer");
    this.logoutButton = document.getElementById("logout-button");
    this.loginForm = document.getElementById("login-form");
    this.loginStatus = document.getElementById("login-status");
    this.usersStatus = document.getElementById("users-status");
    this.editorStatus = document.getElementById("editor-status");
    this.adminsStatus = document.getElementById("admins-status");
    this.auditStatus = document.getElementById("audit-status");
    this.overviewStatus = document.getElementById("overview-status");
    this.overviewGrid = document.getElementById("overview-grid");
    this.searchForm = document.getElementById("search-form");
    this.searchInput = document.getElementById("search-input");
    this.refreshUsersButton = document.getElementById("refresh-users-button");
    this.refreshAuditButton = document.getElementById("refresh-audit-button");
    this.usersTableBody = document.getElementById("users-table-body");
    this.auditTableBody = document.getElementById("audit-table-body");
    this.adminsTableBody = document.getElementById("admins-table-body");
    this.editorForm = document.getElementById("editor-form");
    this.editorUserBadge = document.getElementById("editor-user-badge");
    this.editorUsername = document.getElementById("editor-username");
    this.editorScore = document.getElementById("editor-score");
    this.editorRating = document.getElementById("editor-rating");
    this.adminCreateForm = document.getElementById("admin-create-form");
    this.adminCreatePanel = document.getElementById("admin-create-panel");
    this.adminLoginInput = document.getElementById("admin-login-input");
    this.adminPasswordInput = document.getElementById("admin-password-input");
    this.screens = {
      overview: document.getElementById("screen-overview"),
      users: document.getElementById("screen-users"),
      admins: document.getElementById("screen-admins"),
      audit: document.getElementById("screen-audit"),
    };
  }

  bindEvents() {
    this.loginForm.addEventListener("submit", (event) => this.handleLogin(event));
    this.logoutButton.addEventListener("click", () => this.handleLogout());
    this.searchForm.addEventListener("submit", (event) => this.handleUserSearch(event));
    this.refreshUsersButton.addEventListener("click", () => this.loadUsers());
    this.refreshAuditButton.addEventListener("click", () => this.loadAuditLogs());
    this.editorForm.addEventListener("submit", (event) => this.handleUserUpdate(event));
    this.adminCreateForm.addEventListener("submit", (event) => this.handleAdminCreate(event));

    let index = 0;
    while (index < this.screenLinks.length) {
      const screenLink = this.screenLinks[index];
      screenLink.addEventListener("click", () => this.showScreen(screenLink.dataset.screenLink));
      index += 1;
    }
  }

  detectEnvironment() {
    const path = window.location.pathname.toLowerCase();
    if (path.indexOf("/staging") === 0) {
      return "staging";
    }
    return "production";
  }

  environmentLabel() {
    return this.state.environment === "staging" ? "Staging" : "Production";
  }

  apiBaseUrl() {
    return window.location.origin + "/" + this.state.environment + "/api";
  }

  renderEnvironment() {
    const label = this.environmentLabel();
    let index = 0;

    this.loginEnvBadge.textContent = label;
    this.currentEnvBadge.textContent = label;

    while (index < this.envLinks.length) {
      if (this.envLinks[index].dataset.envLink === this.state.environment) {
        this.envLinks[index].classList.add("active");
      } else {
        this.envLinks[index].classList.remove("active");
      }
      index += 1;
    }
  }

  storageKey() {
    return "wobbly-admin-session-" + this.state.environment;
  }

  restoreSession() {
    const raw = window.localStorage.getItem(this.storageKey());
    if (!raw) {
      this.renderLoggedOut();
      return;
    }

    try {
      this.state.session = JSON.parse(raw);
    } catch {
      this.clearSession();
      this.renderLoggedOut();
      return;
    }

    this.loadDashboard().catch(() => {
      this.clearSession();
      this.renderLoggedOut();
      this.showError(this.loginStatus, "Сессия истекла, войди заново");
    });
  }

  handleLogin(event) {
    event.preventDefault();
    this.showInfo(this.loginStatus, "Входим...");
    this.login().catch((error) => this.showError(this.loginStatus, error.message));
  }

  async login() {
    const response = await this.request(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({
          login: document.getElementById("login-input").value.trim(),
          password: document.getElementById("password-input").value,
        }),
      },
      false,
    );

    this.state.session = {
      token: response.accessToken,
      role: response.role,
      login: document.getElementById("login-input").value.trim(),
    };
    window.localStorage.setItem(this.storageKey(), JSON.stringify(this.state.session));
    await this.loadDashboard();
    this.showOk(this.loginStatus, "Вход выполнен");
  }

  async handleLogout() {
    try {
      await this.request("/auth/logout", { method: "POST" });
    } catch {
      // Если logout не дошел, локальную сессию все равно очищаем.
    }

    this.clearSession();
    this.renderLoggedOut();
    this.showOk(this.loginStatus, "Сессия завершена");
  }

  clearSession() {
    this.state.session = null;
    window.localStorage.removeItem(this.storageKey());
  }

  async loadDashboard() {
    const me = await this.request("/me");
    this.state.session.login = me.login;
    this.state.session.role = me.role;
    window.localStorage.setItem(this.storageKey(), JSON.stringify(this.state.session));

    this.currentAdminBadge.textContent = me.login;
    this.currentAdminTopbarBadge.textContent = me.login;
    this.roleBadge.textContent = me.role;
    this.adminsRoleBadge.textContent = me.role;

    if (me.role !== "owner") {
      this.adminCreatePanel.classList.add("section-hidden");
    } else {
      this.adminCreatePanel.classList.remove("section-hidden");
    }

    this.renderLoggedIn();
    await this.loadOverview();
    await this.loadUsers();
    await this.loadAdmins();
    await this.loadAuditLogs();
    this.showScreen(this.state.activeScreen);
  }

  renderLoggedIn() {
    this.loginView.classList.add("section-hidden");
    this.dashboardView.classList.remove("section-hidden");
    this.screenNav.classList.remove("section-hidden");
    this.sidebarFooter.classList.remove("section-hidden");
  }

  renderLoggedOut() {
    this.loginView.classList.remove("section-hidden");
    this.dashboardView.classList.add("section-hidden");
    this.screenNav.classList.add("section-hidden");
    this.sidebarFooter.classList.add("section-hidden");
    this.currentAdminBadge.textContent = "—";
    this.currentAdminTopbarBadge.textContent = "—";
  }

  showScreen(screenName) {
    this.state.activeScreen = screenName;
    let index = 0;
    const screenTitles = {
      overview: "Обзор",
      users: "Пользователи",
      admins: "Администраторы",
      audit: "Audit log",
    };

    this.screenTitle.textContent = screenTitles[screenName];

    while (index < this.screenLinks.length) {
      if (this.screenLinks[index].dataset.screenLink === screenName) {
        this.screenLinks[index].classList.add("active");
      } else {
        this.screenLinks[index].classList.remove("active");
      }
      index += 1;
    }

    Object.keys(this.screens).forEach((key) => {
      if (key === screenName) {
        this.screens[key].classList.remove("section-hidden");
      } else {
        this.screens[key].classList.add("section-hidden");
      }
    });
  }

  async loadOverview() {
    const overview = await this.request("/overview");
    this.state.overview = overview;
    this.renderOverview();
    this.showOk(this.overviewStatus, "Сводка обновлена");
  }

  renderOverview() {
    const items = [
      ["Всего пользователей", this.state.overview.totalUsers],
      ["В рейтинге", this.state.overview.ratingEnabledUsers],
      ["Всего админов", this.state.overview.totalAdmins],
      ["Активных админов", this.state.overview.activeAdmins],
      ["Записей audit log", this.state.overview.auditLogEntries],
    ];

    let markup = "";
    let index = 0;
    while (index < items.length) {
      markup += `
        <article class="stat-card">
          <p class="muted">${items[index][0]}</p>
          <h3>${items[index][1]}</h3>
        </article>
      `;
      index += 1;
    }
    this.overviewGrid.innerHTML = markup;
  }

  handleUserSearch(event) {
    event.preventDefault();
    this.loadUsers().catch((error) => this.showError(this.usersStatus, error.message));
  }

  async loadUsers() {
    const search = this.searchInput.value.trim();
    const suffix = search ? "?search=" + encodeURIComponent(search) : "";
    const response = await this.request("/users" + suffix);
    this.state.users = response.items;
    this.renderUsers();
    this.showOk(this.usersStatus, "Пользователи обновлены");
  }

  renderUsers() {
    let markup = "";
    let index = 0;

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
      const button = buttons[index];
      button.addEventListener("click", () => this.selectUser(button.dataset.userId));
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
    const response = await this.request("/users/" + this.state.selectedUserId, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    this.replaceUser(response);
    this.renderUsers();
    this.selectUser(response.id);
    await this.loadOverview();
    await this.loadAuditLogs();
    this.showOk(this.editorStatus, "Пользователь сохранен");
  }

  async loadAdmins() {
    const response = await this.request("/admin-users");
    this.state.admins = response.items;
    this.renderAdmins();
    this.showOk(this.adminsStatus, "Администраторы обновлены");
  }

  renderAdmins() {
    let markup = "";
    let index = 0;

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
      const button = buttons[index];
      button.addEventListener("click", () => this.toggleAdmin(button));
      index += 1;
    }
  }

  async toggleAdmin(button) {
    const adminId = Number(button.dataset.adminId);
    const isActive = button.dataset.adminActive === "true";

    await this.request("/admin-users/" + adminId, {
      method: "PATCH",
      body: JSON.stringify({ isActive: !isActive }),
    });

    await this.loadAdmins();
    await this.loadAuditLogs();
  }

  handleAdminCreate(event) {
    event.preventDefault();
    this.createAdmin().catch((error) => this.showError(this.adminsStatus, error.message));
  }

  async createAdmin() {
    await this.request("/admin-users", {
      method: "POST",
      body: JSON.stringify({
        login: this.adminLoginInput.value.trim(),
        password: this.adminPasswordInput.value,
      }),
    });

    this.adminLoginInput.value = "";
    this.adminPasswordInput.value = "";
    await this.loadAdmins();
    await this.loadOverview();
    await this.loadAuditLogs();
    this.showOk(this.adminsStatus, "Новый admin создан");
  }

  async loadAuditLogs() {
    const response = await this.request("/audit-log");
    this.state.audit = response.items;
    this.renderAuditLogs();
    this.showOk(this.auditStatus, "Audit log обновлен");
  }

  renderAuditLogs() {
    let markup = "";
    let index = 0;

    while (index < this.state.audit.length) {
      const entry = this.state.audit[index];
      markup += `
        <tr>
          <td>${this.formatDate(entry.createdAt)}</td>
          <td>${entry.adminLogin}</td>
          <td>${entry.action}</td>
          <td>${entry.targetType}${entry.targetId ? " #" + entry.targetId : ""}</td>
          <td><div class="audit-details">${this.formatDetails(entry.details)}</div></td>
        </tr>
      `;
      index += 1;
    }

    this.auditTableBody.innerHTML = markup || '<tr><td colspan="5">Нет записей</td></tr>';
  }

  async request(path, options, withAuth) {
    const finalOptions = options || {};
    const headers = {
      "Content-Type": "application/json",
    };

    if (withAuth !== false && this.state.session && this.state.session.token) {
      headers.Authorization = "Bearer " + this.state.session.token;
    }

    if (finalOptions.headers) {
      Object.assign(headers, finalOptions.headers);
    }

    const response = await fetch(this.apiBaseUrl() + path, {
      method: finalOptions.method || "GET",
      headers,
      body: finalOptions.body,
      credentials: "same-origin",
    });

    if (response.status === 401 && withAuth !== false) {
      this.clearSession();
    }

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

  formatDetails(details) {
    try {
      return JSON.stringify(details, null, 2);
    } catch {
      return "—";
    }
  }

  showOk(node, message) {
    node.textContent = message;
    node.className = "status status-ok";
  }

  showError(node, message) {
    node.textContent = message;
    node.className = "status status-error";
  }

  showInfo(node, message) {
    node.textContent = message;
    node.className = "status status-warning";
  }
}

window.addEventListener("DOMContentLoaded", () => {
  const consoleApp = new AdminConsole();
  consoleApp.init();
});
