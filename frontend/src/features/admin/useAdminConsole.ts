import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";

import { HttpError } from "@/shared/api/http";

import { createAdminApi } from "./api";
import type {
  AdminSession,
  AdminUserResponse,
  ManagedUserResponse,
  StatusState,
} from "./types";

type ScreenName = "overview" | "users" | "admins" | "audit" | "profile";
type EnvironmentName = "production" | "staging";

function createStatus(): StatusState {
  return {
    kind: "idle",
    text: "",
  };
}

function errorMessage(error: unknown): string {
  if (error instanceof HttpError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Request failed";
}

export function useAdminConsole() {
  const environment = (
    window.location.pathname.toLowerCase().startsWith("/staging")
      ? "staging"
      : "production"
  ) as EnvironmentName;

  const api = createAdminApi(environment);
  const login = ref("");
  const password = ref("");
  const showPassword = ref(false);
  const session = ref<AdminSession | null>(null);
  const activeScreen = ref<ScreenName>("overview");
  const search = ref("");
  const overview = ref<Record<string, number> | null>(null);
  const users = ref<ManagedUserResponse[]>([]);
  const admins = ref<AdminUserResponse[]>([]);
  const audit = ref<
    {
      id: number;
      when: string;
      adminLogin: string;
      action: string;
      target: string;
      details: string;
    }[]
  >([]);
  const loginStatus = reactive(createStatus());
  const overviewStatus = reactive(createStatus());
  const usersStatus = reactive(createStatus());
  const adminsStatus = reactive(createStatus());
  const auditStatus = reactive(createStatus());
  const editorStatus = reactive(createStatus());
  const adminEditorStatus = reactive(createStatus());
  const selectedUser = ref<ManagedUserResponse | null>(null);
  const selectedAdmin = ref<AdminUserResponse | null>(null);
  const isUserModalOpen = ref(false);
  const isAdminModalOpen = ref(false);
  const isAdminCreateModalOpen = ref(false);
  const menuState = reactive<{
    kind: "user" | "admin" | null;
    id: number | null;
    top: number;
    left: number;
  }>({
    kind: null,
    id: null,
    top: 0,
    left: 0,
  });
  const userForm = reactive({
    username: "",
    score: 0,
    participateInRating: false,
  });
  const adminCreateForm = reactive({
    login: "",
    password: "",
  });
  const adminEditForm = reactive({
    role: "admin" as "owner" | "admin",
    isActive: true,
    password: "",
  });

  const environmentLabel = computed(() =>
    environment === "staging" ? "Staging" : "Production",
  );

  const storageKey = computed(() => `wobbly-admin-session-${environment}`);
  const isAuthenticated = computed(() => session.value !== null);
  const isOwner = computed(() => session.value?.role === "owner");
  const displayLogin = computed(() => session.value?.login ?? "—");
  const displayInitials = computed(() => {
    const value = (session.value?.login ?? "WA").replace(
      /[^A-Za-z0-9А-Яа-я]/g,
      "",
    );
    return value.slice(0, 2).toUpperCase() || "WA";
  });

  function setStatus(
    target: StatusState,
    kind: StatusState["kind"],
    text: string,
  ) {
    target.kind = kind;
    target.text = text;
  }

  function clearStatus(target: StatusState) {
    target.kind = "idle";
    target.text = "";
  }

  function closeMenus() {
    menuState.kind = null;
    menuState.id = null;
  }

  function positionMenu(triggerElement: HTMLElement) {
    const rect = triggerElement.getBoundingClientRect();
    const menuWidth = 220;
    const menuHeight = 132;
    const gap = 8;
    const viewportPadding = 12;
    const spaceBelow = window.innerHeight - rect.bottom;
    const shouldOpenBelow =
      spaceBelow >= menuHeight || rect.top < menuHeight + viewportPadding;

    menuState.top = shouldOpenBelow
      ? rect.bottom + gap
      : Math.max(viewportPadding, rect.top - menuHeight - gap);
    menuState.left = Math.min(
      window.innerWidth - menuWidth - viewportPadding,
      Math.max(viewportPadding, rect.right - menuWidth),
    );
  }

  function toggleUserMenu(event: MouseEvent, userId: number) {
    const triggerElement = event.currentTarget as HTMLElement | null;
    if (!triggerElement) {
      return;
    }

    if (menuState.kind === "user" && menuState.id === userId) {
      closeMenus();
      return;
    }

    positionMenu(triggerElement);
    menuState.kind = "user";
    menuState.id = userId;
  }

  function toggleAdminMenu(event: MouseEvent, adminId: number) {
    const triggerElement = event.currentTarget as HTMLElement | null;
    if (!triggerElement) {
      return;
    }

    if (menuState.kind === "admin" && menuState.id === adminId) {
      closeMenus();
      return;
    }

    positionMenu(triggerElement);
    menuState.kind = "admin";
    menuState.id = adminId;
  }

  function isUserMenuOpen(userId: number) {
    return menuState.kind === "user" && menuState.id === userId;
  }

  function isAdminMenuOpen(adminId: number) {
    return menuState.kind === "admin" && menuState.id === adminId;
  }

  function handleWindowClick() {
    closeMenus();
  }

  function handleViewportChange() {
    closeMenus();
  }

  function restoreSession() {
    const raw = window.localStorage.getItem(storageKey.value);
    if (!raw) {
      return;
    }

    try {
      session.value = JSON.parse(raw) as AdminSession;
    } catch {
      session.value = null;
      window.localStorage.removeItem(storageKey.value);
    }
  }

  function persistSession(next: AdminSession | null) {
    session.value = next;
    if (next) {
      window.localStorage.setItem(storageKey.value, JSON.stringify(next));
      return;
    }
    window.localStorage.removeItem(storageKey.value);
  }

  async function initialize() {
    restoreSession();
    if (!session.value) {
      return;
    }

    try {
      await loadDashboard();
    } catch (error) {
      persistSession(null);
      setStatus(loginStatus, "error", `Сессия истекла: ${errorMessage(error)}`);
    }
  }

  async function submitLogin() {
    setStatus(loginStatus, "info", "Входим...");
    try {
      const response = await api.login(login.value.trim(), password.value);
      persistSession({
        token: response.accessToken,
        role: response.role,
        login: login.value.trim(),
      });
      await loadDashboard();
      password.value = "";
      setStatus(loginStatus, "success", "Вход выполнен");
    } catch (error) {
      setStatus(loginStatus, "error", errorMessage(error));
    }
  }

  async function logout() {
    if (session.value) {
      try {
        await api.logout(session.value.token);
      } catch {
        // Local session cleanup is still desirable.
      }
    }
    persistSession(null);
    activeScreen.value = "overview";
    setStatus(loginStatus, "success", "Сессия завершена");
  }

  async function loadDashboard() {
    if (!session.value) {
      return;
    }

    const me = await api.me(session.value.token);
    persistSession({
      ...session.value,
      login: me.login,
      role: me.role,
    });

    await Promise.all([loadOverview(), loadUsers(), loadAudit()]);
    if (me.role === "owner") {
      await loadAdmins();
    } else {
      admins.value = [];
      if (activeScreen.value === "admins") {
        activeScreen.value = "overview";
      }
      setStatus(
        adminsStatus,
        "info",
        "Управление admin-доступами доступно только owner",
      );
    }
  }

  async function loadOverview() {
    if (!session.value) {
      return;
    }
    try {
      const response = await api.overview(session.value.token);
      overview.value = {
        totalUsers: response.totalUsers,
        ratingEnabledUsers: response.ratingEnabledUsers,
        totalAdmins: response.totalAdmins,
        activeAdmins: response.activeAdmins,
        auditLogEntries: response.auditLogEntries,
      };
      setStatus(overviewStatus, "success", "Сводка обновлена");
    } catch (error) {
      setStatus(overviewStatus, "error", errorMessage(error));
    }
  }

  async function loadUsers() {
    if (!session.value) {
      return;
    }
    try {
      const response = await api.users(
        session.value.token,
        search.value.trim(),
      );
      users.value = response.items;
      setStatus(usersStatus, "success", "Пользователи обновлены");
    } catch (error) {
      setStatus(usersStatus, "error", errorMessage(error));
    }
  }

  async function loadAdmins() {
    if (!session.value) {
      return;
    }
    try {
      const response = await api.admins(session.value.token);
      admins.value = response.items;
      setStatus(adminsStatus, "success", "Администраторы обновлены");
    } catch (error) {
      setStatus(adminsStatus, "error", errorMessage(error));
    }
  }

  async function loadAudit() {
    if (!session.value) {
      return;
    }
    try {
      const response = await api.auditLog(session.value.token);
      audit.value = response.items.map((item) => ({
        id: item.id,
        when: formatDate(item.createdAt),
        adminLogin: item.adminLogin,
        action: item.action,
        target: item.targetId
          ? `${item.targetType} #${item.targetId}`
          : item.targetType,
        details: JSON.stringify(item.details),
      }));
      setStatus(auditStatus, "success", "Audit log обновлен");
    } catch (error) {
      setStatus(auditStatus, "error", errorMessage(error));
    }
  }

  function selectUser(user: ManagedUserResponse) {
    closeMenus();
    selectedUser.value = user;
    userForm.username = user.username ?? "";
    userForm.score = user.score;
    userForm.participateInRating = user.participateInRating;
    clearStatus(editorStatus);
    isUserModalOpen.value = true;
  }

  function selectAdmin(admin: AdminUserResponse) {
    closeMenus();
    selectedAdmin.value = admin;
    adminEditForm.role = admin.role;
    adminEditForm.isActive = admin.isActive;
    adminEditForm.password = "";
    clearStatus(adminEditorStatus);
    isAdminModalOpen.value = true;
  }

  async function saveUser() {
    if (!session.value || !selectedUser.value) {
      return;
    }

    setStatus(editorStatus, "info", "Сохраняем...");
    try {
      await api.updateUser(session.value.token, selectedUser.value.id, {
        username: userForm.username.trim() || null,
        score: userForm.score,
        participateInRating: userForm.participateInRating,
      });
      await loadUsers();
      await loadOverview();
      isUserModalOpen.value = false;
      setStatus(editorStatus, "success", "Пользователь сохранен");
    } catch (error) {
      setStatus(editorStatus, "error", errorMessage(error));
    }
  }

  async function confirmDeleteUser(user: ManagedUserResponse) {
    closeMenus();
    if (
      !session.value ||
      !window.confirm(`Удалить пользователя #${user.id}?`)
    ) {
      return;
    }

    try {
      await api.deleteUser(session.value.token, user.id);
      await loadUsers();
      await loadOverview();
      setStatus(usersStatus, "success", "Пользователь удален");
    } catch (error) {
      setStatus(usersStatus, "error", errorMessage(error));
    }
  }

  async function createAdmin() {
    if (!session.value) {
      return;
    }

    setStatus(adminEditorStatus, "info", "Создаем admin...");
    try {
      await api.createAdmin(session.value.token, {
        login: adminCreateForm.login.trim(),
        password: adminCreateForm.password,
      });
      adminCreateForm.login = "";
      adminCreateForm.password = "";
      isAdminCreateModalOpen.value = false;
      await loadAdmins();
      await loadOverview();
      setStatus(adminsStatus, "success", "Admin создан");
    } catch (error) {
      setStatus(adminEditorStatus, "error", errorMessage(error));
    }
  }

  async function saveAdmin() {
    if (!session.value || !selectedAdmin.value) {
      return;
    }

    setStatus(adminEditorStatus, "info", "Сохраняем admin...");
    try {
      await api.updateAdmin(session.value.token, selectedAdmin.value.id, {
        role: adminEditForm.role,
        isActive: adminEditForm.isActive,
        password: adminEditForm.password || undefined,
      });
      await loadAdmins();
      await loadOverview();
      isAdminModalOpen.value = false;
      setStatus(adminEditorStatus, "success", "Admin сохранен");
    } catch (error) {
      setStatus(adminEditorStatus, "error", errorMessage(error));
    }
  }

  async function confirmDeleteAdmin(admin: AdminUserResponse) {
    closeMenus();
    if (!session.value || !window.confirm(`Удалить admin #${admin.id}?`)) {
      return;
    }

    try {
      await api.deleteAdmin(session.value.token, admin.id);
      await loadAdmins();
      await loadOverview();
      setStatus(adminsStatus, "success", "Admin удален");
    } catch (error) {
      setStatus(adminsStatus, "error", errorMessage(error));
    }
  }

  function formatDate(value: string) {
    return new Date(value).toLocaleString();
  }

  onMounted(() => {
    window.addEventListener("click", handleWindowClick);
    window.addEventListener("resize", handleViewportChange);
    window.addEventListener("scroll", handleViewportChange, true);
  });

  onBeforeUnmount(() => {
    window.removeEventListener("click", handleWindowClick);
    window.removeEventListener("resize", handleViewportChange);
    window.removeEventListener("scroll", handleViewportChange, true);
  });

  return reactive({
    environment,
    environmentLabel,
    login,
    password,
    showPassword,
    session,
    activeScreen,
    search,
    overview,
    users,
    admins,
    audit,
    loginStatus,
    overviewStatus,
    usersStatus,
    adminsStatus,
    auditStatus,
    editorStatus,
    adminEditorStatus,
    selectedUser,
    selectedAdmin,
    isUserModalOpen,
    isAdminModalOpen,
    isAdminCreateModalOpen,
    menuState,
    userForm,
    adminCreateForm,
    adminEditForm,
    isAuthenticated,
    isOwner,
    displayLogin,
    displayInitials,
    initialize,
    submitLogin,
    logout,
    loadUsers,
    loadAdmins,
    loadAudit,
    selectUser,
    selectAdmin,
    toggleUserMenu,
    toggleAdminMenu,
    isUserMenuOpen,
    isAdminMenuOpen,
    closeMenus,
    saveUser,
    confirmDeleteUser,
    createAdmin,
    saveAdmin,
    confirmDeleteAdmin,
    formatDate,
  });
}
