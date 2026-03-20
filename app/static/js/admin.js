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
      selectedAdminId: null,
      openUserMenuId: null,
      openAdminMenuId: null,
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
    this.adminsScreenLink = document.querySelector('[data-screen-link="admins"]');
    this.screenTitle = document.getElementById("screen-title");
    this.loginEnvBadge = document.getElementById("login-env-badge");
    this.sidebarAvatar = document.getElementById("sidebar-avatar");
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
    this.userModalShell = document.getElementById("user-modal-shell");
    this.adminModalShell = document.getElementById("admin-modal-shell");
    this.adminCreateModalShell = document.getElementById("admin-create-modal-shell");
    this.adminCreateForm = document.getElementById("admin-create-form");
    this.openAdminCreateModalButton = document.getElementById("open-admin-create-modal-button");
    this.adminLoginInput = document.getElementById("admin-login-input");
    this.adminPasswordInput = document.getElementById("admin-password-input");
    this.adminEditForm = document.getElementById("admin-edit-form");
    this.adminEditLogin = document.getElementById("admin-edit-login");
    this.adminEditRole = document.getElementById("admin-edit-role");
    this.adminEditPassword = document.getElementById("admin-edit-password");
    this.adminEditPasswordRow = document.getElementById("admin-edit-password-row");
    this.adminEditSelfNote = document.getElementById("admin-edit-self-note");
    this.adminEditActive = document.getElementById("admin-edit-active");
    this.adminEditorBadge = document.getElementById("admin-editor-badge");
    this.adminEditorStatus = document.getElementById("admin-editor-status");
    this.profileLogin = document.getElementById("profile-login");
    this.profileRole = document.getElementById("profile-role");
    this.profileEnvironment = document.getElementById("profile-environment");
    this.profileAvatar = document.getElementById("profile-avatar");
    this.profilePasswordForm = document.getElementById("profile-password-form");
    this.profileCurrentPassword = document.getElementById("profile-current-password");
    this.profileNewPassword = document.getElementById("profile-new-password");
    this.profileStatus = document.getElementById("profile-status");
    this.screens = {
      overview: document.getElementById("screen-overview"),
      users: document.getElementById("screen-users"),
      admins: document.getElementById("screen-admins"),
      audit: document.getElementById("screen-audit"),
      profile: document.getElementById("screen-profile"),
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
    this.adminEditForm.addEventListener("submit", (event) => this.handleAdminUpdate(event));
    this.profilePasswordForm.addEventListener("submit", (event) => this.handlePasswordChange(event));
    this.openAdminCreateModalButton.addEventListener("click", () => this.openAdminCreateModal());
    document.addEventListener("click", (event) => this.handleGlobalClick(event));
    document.addEventListener("keydown", (event) => this.handleKeyDown(event));

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

    while (index < this.envLinks.length) {
      if (this.envLinks[index].dataset.envLink === this.state.environment) {
        this.envLinks[index].classList.add("active");
      } else {
        this.envLinks[index].classList.remove("active");
      }
      index += 1;
    }
  }

  initialsFor(value) {
    const safeValue = (value || "AD").trim();
    if (!safeValue) {
      return "AD";
    }

    const compact = safeValue.replace(/[^A-Za-z0-9А-Яа-я]/g, "");
    return compact.slice(0, 2).toUpperCase() || "AD";
  }

  renderAdminIdentity(login, role) {
    const initials = this.initialsFor(login);
    this.profileAvatar.textContent = initials;
    this.sidebarAvatar.textContent = initials;
    this.profileLogin.textContent = login;
    this.profileRole.textContent = "Роль: " + role;
    this.profileEnvironment.textContent = "Среда: " + this.environmentLabel();
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

    this.renderAdminIdentity(me.login, me.role);
    this.adminsRoleBadge.textContent = me.role;

    if (me.role !== "owner") {
      this.openAdminCreateModalButton.classList.add("section-hidden");
      this.adminsScreenLink.classList.add("section-hidden");
    } else {
      this.openAdminCreateModalButton.classList.remove("section-hidden");
      this.adminsScreenLink.classList.remove("section-hidden");
    }

    this.renderLoggedIn();
    await this.loadOverview();
    await this.loadUsers();
    if (me.role === "owner") {
      await this.loadAdmins();
    } else {
      this.state.admins = [];
      this.renderAdmins();
      this.showInfo(this.adminsStatus, "Управление admin-доступами доступно только owner");
    }
    await this.loadAuditLogs();
    if (me.role !== "owner" && this.state.activeScreen === "admins") {
      this.state.activeScreen = "overview";
    }
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
    this.profileAvatar.textContent = "—";
    this.profileLogin.textContent = "—";
    this.profileRole.textContent = "—";
    this.profileEnvironment.textContent = "—";
    this.sidebarAvatar.textContent = "WA";
  }

  showScreen(screenName) {
    this.state.activeScreen = screenName;
    let index = 0;
    const screenTitles = {
      overview: "Обзор",
      users: "Пользователи",
      admins: "Администраторы",
      audit: "Audit log",
      profile: "Профиль",
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
      const menuClass = this.state.openUserMenuId === user.id ? "user-actions-menu" : "user-actions-menu section-hidden";
      markup += `
        <tr>
          <td>${user.id}</td>
          <td>${user.username || "—"}</td>
          <td>${user.score}</td>
          <td>${user.participateInRating ? "on" : "off"}</td>
          <td>${this.formatDate(user.updatedAt)}</td>
          <td class="actions-cell">
            <div class="user-actions">
              <button class="ghost-button action-menu-trigger" type="button" data-user-menu-trigger="${user.id}" aria-label="User actions">
                <span class="dots-icon" aria-hidden="true">•••</span>
              </button>
              <div class="${menuClass}" data-user-menu="${user.id}">
                <button class="menu-item" type="button" data-user-edit="${user.id}">Редактировать</button>
                <button class="menu-item menu-item-danger" type="button" data-user-delete="${user.id}">
                  <span class="trash-icon" aria-hidden="true">🗑</span>
                  <span>Удалить</span>
                </button>
              </div>
            </div>
          </td>
        </tr>
      `;
      index += 1;
    }

    this.usersTableBody.innerHTML = markup || '<tr><td colspan="6">Нет пользователей</td></tr>';
    this.bindUserButtons();
  }

  bindUserButtons() {
    const editButtons = this.usersTableBody.querySelectorAll("[data-user-edit]");
    const menuButtons = this.usersTableBody.querySelectorAll("[data-user-menu-trigger]");
    const deleteButtons = this.usersTableBody.querySelectorAll("[data-user-delete]");
    let index = 0;

    while (index < editButtons.length) {
      const button = editButtons[index];
      button.addEventListener("click", () => this.selectUser(button.dataset.userEdit));
      index += 1;
    }

    index = 0;
    while (index < menuButtons.length) {
      const button = menuButtons[index];
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        this.toggleUserMenu(button.dataset.userMenuTrigger);
      });
      index += 1;
    }

    index = 0;
    while (index < deleteButtons.length) {
      const button = deleteButtons[index];
      button.addEventListener("click", () => this.confirmDeleteUser(button.dataset.userDelete));
      index += 1;
    }
  }

  handleGlobalClick(event) {
    if (event.target && event.target.dataset && event.target.dataset.closeUserModal === "true") {
      this.closeUserModal();
      return;
    }

    if (event.target && event.target.dataset && event.target.dataset.closeAdminModal === "true") {
      this.closeAdminModal();
      return;
    }

    if (event.target && event.target.dataset && event.target.dataset.closeAdminCreateModal === "true") {
      this.closeAdminCreateModal();
      return;
    }

    if (this.state.openUserMenuId !== null) {
      const target = event.target;
      const insideMenu = target.closest("[data-user-menu]");
      const insideTrigger = target.closest("[data-user-menu-trigger]");
      if (!insideMenu && !insideTrigger) {
        this.state.openUserMenuId = null;
        this.renderUsers();
      }
    }

    if (this.state.openAdminMenuId !== null) {
      const target = event.target;
      const insideMenu = target.closest("[data-admin-menu]");
      const insideTrigger = target.closest("[data-admin-menu-trigger]");
      if (!insideMenu && !insideTrigger) {
        this.state.openAdminMenuId = null;
        this.renderAdmins();
      }
    }
  }

  handleKeyDown(event) {
    if (event.key === "Escape") {
      this.closeUserModal();
      this.closeAdminModal();
      this.closeAdminCreateModal();
      if (this.state.openUserMenuId !== null) {
        this.state.openUserMenuId = null;
        this.renderUsers();
      }
      if (this.state.openAdminMenuId !== null) {
        this.state.openAdminMenuId = null;
        this.renderAdmins();
      }
    }
  }

  toggleUserMenu(userIdValue) {
    const userId = Number(userIdValue);
    if (this.state.openUserMenuId === userId) {
      this.state.openUserMenuId = null;
    } else {
      this.state.openUserMenuId = userId;
    }
    this.renderUsers();
  }

  openUserModal() {
    this.userModalShell.classList.remove("section-hidden");
  }

  closeUserModal() {
    this.userModalShell.classList.add("section-hidden");
  }

  openAdminModal() {
    this.adminModalShell.classList.remove("section-hidden");
  }

  closeAdminModal() {
    this.adminModalShell.classList.add("section-hidden");
  }

  openAdminCreateModal() {
    this.adminCreateModalShell.classList.remove("section-hidden");
  }

  closeAdminCreateModal() {
    this.adminCreateModalShell.classList.add("section-hidden");
  }

  selectUser(userIdValue) {
    const userId = Number(userIdValue);
    const user = this.findById(this.state.users, userId);
    if (!user) {
      return;
    }

    this.state.selectedUserId = user.id;
    this.state.openUserMenuId = null;
    this.renderUsers();
    this.editorUserBadge.textContent = "#" + user.id;
    this.editorUsername.value = user.username || "";
    this.editorScore.value = String(user.score);
    this.editorRating.checked = Boolean(user.participateInRating);
    this.openUserModal();
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
    this.closeUserModal();
    await this.loadOverview();
    await this.loadAuditLogs();
    this.showOk(this.editorStatus, "Пользователь сохранен");
  }

  async confirmDeleteUser(userIdValue) {
    const userId = Number(userIdValue);
    const user = this.findById(this.state.users, userId);
    if (!user) {
      return;
    }

    const confirmed = window.confirm(`Точно удалить пользователя ${user.username || "#" + user.id}?`);
    if (!confirmed) {
      this.state.openUserMenuId = null;
      this.renderUsers();
      return;
    }

    try {
      await this.request("/users/" + user.id, { method: "DELETE" });
      this.removeUser(user.id);
      this.state.openUserMenuId = null;
      this.renderUsers();
      this.closeUserModal();
      await this.loadOverview();
      await this.loadAuditLogs();
      this.showOk(this.usersStatus, "Пользователь удален");
    } catch (error) {
      this.showError(this.usersStatus, error.message);
    }
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
      const menuClass = this.state.openAdminMenuId === admin.id ? "admin-actions-menu" : "admin-actions-menu section-hidden";
      markup += `
        <tr>
          <td>${admin.id}</td>
          <td>${admin.login}</td>
          <td>${admin.role}</td>
          <td>${admin.isActive ? "yes" : "no"}</td>
          <td class="actions-cell">
            <div class="admin-actions">
              <button class="ghost-button action-menu-trigger" type="button" data-admin-menu-trigger="${admin.id}" aria-label="Admin actions">
                <span class="dots-icon" aria-hidden="true">•••</span>
              </button>
              <div class="${menuClass}" data-admin-menu="${admin.id}">
                <button class="menu-item" type="button" data-admin-edit="${admin.id}">Редактировать</button>
                <button class="menu-item menu-item-danger" type="button" data-admin-delete="${admin.id}">
                  <span class="trash-icon" aria-hidden="true">🗑</span>
                  <span>Удалить</span>
                </button>
              </div>
            </div>
          </td>
        </tr>
      `;
      index += 1;
    }

    this.adminsTableBody.innerHTML = markup || '<tr><td colspan="5">Нет админов</td></tr>';
    this.bindAdminButtons();
  }

  bindAdminButtons() {
    const editButtons = this.adminsTableBody.querySelectorAll("[data-admin-edit]");
    const menuButtons = this.adminsTableBody.querySelectorAll("[data-admin-menu-trigger]");
    const deleteButtons = this.adminsTableBody.querySelectorAll("[data-admin-delete]");
    let index = 0;

    while (index < editButtons.length) {
      const button = editButtons[index];
      button.addEventListener("click", () => this.selectAdmin(button.dataset.adminEdit));
      index += 1;
    }

    index = 0;
    while (index < menuButtons.length) {
      const button = menuButtons[index];
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        this.toggleAdminMenu(button.dataset.adminMenuTrigger);
      });
      index += 1;
    }

    index = 0;
    while (index < deleteButtons.length) {
      const button = deleteButtons[index];
      button.addEventListener("click", () => this.confirmDeleteAdmin(button.dataset.adminDelete));
      index += 1;
    }
  }

  toggleAdminMenu(adminIdValue) {
    const adminId = Number(adminIdValue);
    if (this.state.openAdminMenuId === adminId) {
      this.state.openAdminMenuId = null;
    } else {
      this.state.openAdminMenuId = adminId;
    }
    this.renderAdmins();
  }

  selectAdmin(adminIdValue) {
    const adminId = Number(adminIdValue);
    const admin = this.findById(this.state.admins, adminId);
    if (!admin) {
      return;
    }

    this.state.selectedAdminId = admin.id;
    this.state.openAdminMenuId = null;
    this.renderAdmins();
    this.adminEditLogin.value = admin.login;
    this.adminEditRole.value = admin.role;
    this.adminEditPassword.value = "";
    this.adminEditActive.checked = Boolean(admin.isActive);
    this.adminEditorBadge.textContent = "#" + admin.id;
    if (this.state.session && admin.login === this.state.session.login) {
      this.adminEditPasswordRow.classList.add("section-hidden");
      this.adminEditSelfNote.classList.remove("section-hidden");
    } else {
      this.adminEditPasswordRow.classList.remove("section-hidden");
      this.adminEditSelfNote.classList.add("section-hidden");
    }
    this.openAdminModal();
    this.showOk(this.adminEditorStatus, "Admin загружен в форму");
  }

  handleAdminUpdate(event) {
    event.preventDefault();
    if (!this.state.selectedAdminId) {
      this.showError(this.adminEditorStatus, "Сначала выбери admin из таблицы");
      return;
    }

    this.updateAdmin().catch((error) => this.showError(this.adminEditorStatus, error.message));
  }

  async updateAdmin() {
    const payload = {
      role: this.adminEditRole.value,
      isActive: this.adminEditActive.checked,
      password: this.adminEditPassword.value.trim() || undefined,
    };

    const response = await this.request("/admin-users/" + this.state.selectedAdminId, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });

    this.replaceAdmin(response);
    this.renderAdmins();
    this.closeAdminModal();
    await this.loadOverview();
    await this.loadAuditLogs();
    this.showOk(this.adminEditorStatus, "Admin сохранен");
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
    this.closeAdminCreateModal();
    await this.loadAdmins();
    await this.loadOverview();
    await this.loadAuditLogs();
    this.showOk(this.adminsStatus, "Новый admin создан");
  }

  async confirmDeleteAdmin(adminIdValue) {
    const adminId = Number(adminIdValue);
    const admin = this.findById(this.state.admins, adminId);
    if (!admin) {
      return;
    }

    const confirmed = window.confirm(`Точно удалить admin ${admin.login}?`);
    if (!confirmed) {
      this.state.openAdminMenuId = null;
      this.renderAdmins();
      return;
    }

    try {
      await this.request("/admin-users/" + admin.id, { method: "DELETE" });
      this.removeAdmin(admin.id);
      this.state.openAdminMenuId = null;
      this.renderAdmins();
      this.closeAdminModal();
      await this.loadOverview();
      await this.loadAuditLogs();
      this.showOk(this.adminsStatus, "Admin удален");
    } catch (error) {
      this.showError(this.adminsStatus, error.message);
    }
  }

  handlePasswordChange(event) {
    event.preventDefault();
    this.changeOwnPassword().catch((error) => this.showError(this.profileStatus, error.message));
  }

  async changeOwnPassword() {
    await this.request("/me/password", {
      method: "PATCH",
      body: JSON.stringify({
        currentPassword: this.profileCurrentPassword.value,
        newPassword: this.profileNewPassword.value,
      }),
    });

    this.profileCurrentPassword.value = "";
    this.profileNewPassword.value = "";
    await this.loadAuditLogs();
    this.showOk(this.profileStatus, "Пароль обновлен");
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

    if (response.status === 204 || response.status === 205) {
      return null;
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

  removeUser(userId) {
    let index = 0;
    while (index < this.state.users.length) {
      if (this.state.users[index].id === userId) {
        this.state.users.splice(index, 1);
        return;
      }
      index += 1;
    }
  }

  replaceAdmin(updatedAdmin) {
    let index = 0;
    while (index < this.state.admins.length) {
      if (this.state.admins[index].id === updatedAdmin.id) {
        this.state.admins[index] = updatedAdmin;
        return;
      }
      index += 1;
    }
    this.state.admins.unshift(updatedAdmin);
  }

  removeAdmin(adminId) {
    let index = 0;
    while (index < this.state.admins.length) {
      if (this.state.admins[index].id === adminId) {
        this.state.admins.splice(index, 1);
        return;
      }
      index += 1;
    }
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
