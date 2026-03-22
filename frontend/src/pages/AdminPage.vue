<template>
  <div
    class="admin-app"
    :class="{ 'login-mode': !consoleState.isAuthenticated }"
  >
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-avatar">{{ consoleState.displayInitials }}</div>
        <p class="eyebrow">Wobbly Admin</p>
      </div>

      <nav
        class="screen-nav"
        :class="{ 'section-hidden': !consoleState.isAuthenticated }"
        aria-label="Admin navigation"
      >
        <button
          v-for="screen in screens"
          v-show="screen.id !== 'admins' || consoleState.isOwner"
          :key="screen.id"
          class="nav-button"
          :class="{ active: consoleState.activeScreen === screen.id }"
          type="button"
          @click="consoleState.activeScreen = screen.id"
        >
          {{ screen.label }}
        </button>
      </nav>

      <div
        class="sidebar-footer"
        :class="{ 'section-hidden': !consoleState.isAuthenticated }"
      >
        <button class="ghost-button" type="button" @click="consoleState.logout">
          Выйти
        </button>
      </div>
    </aside>

    <main class="content-shell">
      <section
        class="login-view"
        :class="{ 'section-hidden': consoleState.isAuthenticated }"
      >
        <section class="panel login-panel">
          <nav
            class="environment-switcher login-environment-switcher"
            aria-label="Environment switcher"
          >
            <a
              href="/production/"
              :class="{ active: consoleState.environment === 'production' }"
              >Production</a
            >
            <a
              href="/staging/"
              :class="{ active: consoleState.environment === 'staging' }"
              >Staging</a
            >
          </nav>

          <form class="form-grid" @submit.prevent="consoleState.submitLogin">
            <label>
              <span>Login</span>
              <input
                v-model="consoleState.login"
                type="text"
                autocomplete="username"
                required
              />
            </label>
            <label>
              <span>Password</span>
              <div class="password-field">
                <input
                  v-model="consoleState.password"
                  :type="consoleState.showPassword ? 'text' : 'password'"
                  autocomplete="current-password"
                  required
                />
                <button
                  class="password-toggle"
                  type="button"
                  :aria-label="
                    consoleState.showPassword
                      ? 'Скрыть пароль'
                      : 'Показать пароль'
                  "
                  @click="
                    consoleState.showPassword = !consoleState.showPassword
                  "
                >
                  <span aria-hidden="true">👁</span>
                </button>
              </div>
            </label>
            <button type="submit">Войти</button>
          </form>
          <p class="status" :class="statusClass(consoleState.loginStatus)">
            {{ consoleState.loginStatus.text }}
          </p>
        </section>
      </section>

      <section
        class="dashboard"
        :class="{ 'section-hidden': !consoleState.isAuthenticated }"
      >
        <header class="dashboard-topbar">
          <div>
            <p class="eyebrow">Control Center</p>
            <h2>{{ currentScreenLabel }}</h2>
          </div>
          <div class="topbar-meta">
            <nav class="environment-switcher" aria-label="Environment switcher">
              <a
                href="/production/"
                :class="{ active: consoleState.environment === 'production' }"
                >Production</a
              >
              <a
                href="/staging/"
                :class="{ active: consoleState.environment === 'staging' }"
                >Staging</a
              >
            </nav>
          </div>
        </header>

        <section
          v-show="consoleState.activeScreen === 'overview'"
          class="screen"
        >
          <div class="stats-grid">
            <article
              v-for="item in overviewItems"
              :key="item.label"
              class="stat-card"
            >
              <p class="muted">{{ item.label }}</p>
              <h3>{{ item.value }}</h3>
            </article>
          </div>
          <p class="status" :class="statusClass(consoleState.overviewStatus)">
            {{ consoleState.overviewStatus.text }}
          </p>
        </section>

        <section v-show="consoleState.activeScreen === 'users'" class="screen">
          <div class="panel">
            <div class="panel-head">
              <div>
                <h3>Пользователи</h3>
                <p class="muted">
                  Поиск, фильтрация и быстрые действия через контекстное меню.
                </p>
              </div>
              <button
                class="ghost-button"
                type="button"
                @click="consoleState.loadUsers"
              >
                Обновить
              </button>
            </div>

            <form class="toolbar" @submit.prevent="consoleState.loadUsers">
              <input
                v-model="consoleState.search"
                type="search"
                placeholder="Поиск по username"
              />
              <button class="primary-button" type="submit">Искать</button>
            </form>

            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Username</th>
                    <th>Score</th>
                    <th>Rating</th>
                    <th>Updated</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!consoleState.users.length">
                    <td colspan="6">Нет пользователей</td>
                  </tr>
                  <tr v-for="user in consoleState.users" :key="user.id">
                    <td>{{ user.id }}</td>
                    <td>{{ user.username ?? "—" }}</td>
                    <td>{{ user.score }}</td>
                    <td>{{ user.participateInRating ? "on" : "off" }}</td>
                    <td>{{ consoleState.formatDate(user.updatedAt) }}</td>
                    <td class="actions-cell">
                      <div class="user-actions">
                        <button
                          class="ghost-button action-menu-trigger"
                          type="button"
                          aria-label="User actions"
                          @click.stop="
                            consoleState.toggleUserMenu($event, user.id)
                          "
                        >
                          <span class="dots-icon" aria-hidden="true">•••</span>
                        </button>
                        <Teleport to="body">
                          <div
                            v-if="consoleState.isUserMenuOpen(user.id)"
                            class="user-actions-menu"
                            :style="{
                              top: `${consoleState.menuState.top}px`,
                              left: `${consoleState.menuState.left}px`,
                            }"
                            @click.stop
                          >
                            <button
                              class="menu-item"
                              type="button"
                              @click="consoleState.selectUser(user)"
                            >
                              Редактировать
                            </button>
                            <button
                              class="menu-item menu-item-danger"
                              type="button"
                              @click="consoleState.confirmDeleteUser(user)"
                            >
                              Удалить
                            </button>
                          </div>
                        </Teleport>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="status" :class="statusClass(consoleState.usersStatus)">
              {{ consoleState.usersStatus.text }}
            </p>
          </div>
        </section>

        <section
          v-show="
            consoleState.activeScreen === 'admins' && consoleState.isOwner
          "
          class="screen"
        >
          <div class="split-layout admins-layout">
            <div class="panel">
              <div class="panel-head">
                <div>
                  <h3>Администраторы</h3>
                  <p class="muted">
                    Доступы, роли и активация админских аккаунтов.
                  </p>
                </div>
                <div class="panel-head-actions">
                  <button
                    class="ghost-button"
                    type="button"
                    @click="consoleState.isAdminCreateModalOpen = true"
                  >
                    Создать admin
                  </button>
                  <span class="badge">{{ consoleState.session?.role }}</span>
                </div>
              </div>

              <div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Login</th>
                      <th>Role</th>
                      <th>Active</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-if="!consoleState.admins.length">
                      <td colspan="5">Нет администраторов</td>
                    </tr>
                    <tr v-for="admin in consoleState.admins" :key="admin.id">
                      <td>{{ admin.id }}</td>
                      <td>{{ admin.login }}</td>
                      <td>{{ admin.role }}</td>
                      <td>{{ admin.isActive ? "yes" : "no" }}</td>
                      <td class="actions-cell">
                        <div class="user-actions">
                          <button
                            class="ghost-button action-menu-trigger"
                            type="button"
                            aria-label="Admin actions"
                            @click.stop="
                              consoleState.toggleAdminMenu($event, admin.id)
                            "
                          >
                            <span class="dots-icon" aria-hidden="true"
                              >•••</span
                            >
                          </button>
                          <Teleport to="body">
                            <div
                              v-if="consoleState.isAdminMenuOpen(admin.id)"
                              class="user-actions-menu"
                              :style="{
                                top: `${consoleState.menuState.top}px`,
                                left: `${consoleState.menuState.left}px`,
                              }"
                              @click.stop
                            >
                              <button
                                class="menu-item"
                                type="button"
                                @click="consoleState.selectAdmin(admin)"
                              >
                                Редактировать
                              </button>
                              <button
                                class="menu-item menu-item-danger"
                                type="button"
                                @click="consoleState.confirmDeleteAdmin(admin)"
                              >
                                Удалить
                              </button>
                            </div>
                          </Teleport>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p class="status" :class="statusClass(consoleState.adminsStatus)">
                {{ consoleState.adminsStatus.text }}
              </p>
            </div>

            <div class="stack-layout">
              <div class="panel">
                <div class="panel-head">
                  <div>
                    <h3>Управление доступами</h3>
                    <p class="muted">
                      Owner управляет ролями и активностью, а UI оставляет весь
                      поток в одном месте.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section v-show="consoleState.activeScreen === 'audit'" class="screen">
          <div class="panel">
            <div class="panel-head">
              <div>
                <h3>Audit log</h3>
                <p class="muted">
                  Кто и что менял в админке: пользователи, роли, логины, logout.
                </p>
              </div>
              <button
                class="ghost-button"
                type="button"
                @click="consoleState.loadAudit"
              >
                Обновить
              </button>
            </div>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Admin</th>
                    <th>Action</th>
                    <th>Target</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!consoleState.audit.length">
                    <td colspan="5">Нет записей</td>
                  </tr>
                  <tr v-for="item in consoleState.audit" :key="item.id">
                    <td>{{ item.when }}</td>
                    <td>{{ item.adminLogin }}</td>
                    <td>{{ item.action }}</td>
                    <td>{{ item.target }}</td>
                    <td>
                      <code>{{ item.details }}</code>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="status" :class="statusClass(consoleState.auditStatus)">
              {{ consoleState.auditStatus.text }}
            </p>
          </div>
        </section>

        <section
          v-show="consoleState.activeScreen === 'profile'"
          class="screen"
        >
          <div class="panel">
            <div class="panel-head">
              <div>
                <h3>Профиль админа</h3>
                <p class="muted">
                  Текущая сессия и базовая информация по аккаунту.
                </p>
              </div>
            </div>

            <div class="profile-card">
              <div class="profile-card-avatar">
                {{ consoleState.displayInitials }}
              </div>
              <div class="profile-card-copy">
                <strong>{{ consoleState.displayLogin }}</strong>
                <span class="muted"
                  >Роль: {{ consoleState.session?.role ?? "—" }}</span
                >
                <span class="muted"
                  >Среда: {{ consoleState.environmentLabel }}</span
                >
              </div>
            </div>
          </div>
        </section>
      </section>
    </main>

    <div
      class="modal-shell"
      :class="{ 'section-hidden': !consoleState.isUserModalOpen }"
    >
      <div
        class="modal-backdrop"
        @click="consoleState.isUserModalOpen = false"
      ></div>
      <section class="modal-panel" role="dialog" aria-modal="true">
        <div class="panel-head">
          <div>
            <h3>Редактирование пользователя</h3>
            <p class="muted">
              Правки сохраняются в модальном окне, без редактирования сырого
              JSON.
            </p>
          </div>
          <div class="modal-head-actions">
            <span class="badge">
              {{
                consoleState.selectedUser
                  ? `#${consoleState.selectedUser.id}`
                  : "Не выбран"
              }}
            </span>
            <button
              class="ghost-button"
              type="button"
              @click="consoleState.isUserModalOpen = false"
            >
              Закрыть
            </button>
          </div>
        </div>
        <form class="form-grid" @submit.prevent="consoleState.saveUser">
          <label>
            <span>Username</span>
            <input v-model="consoleState.userForm.username" type="text" />
          </label>
          <label>
            <span>Score</span>
            <input v-model.number="consoleState.userForm.score" type="number" />
          </label>
          <label class="checkbox-row">
            <input
              v-model="consoleState.userForm.participateInRating"
              type="checkbox"
            />
            <span>Участвует в рейтинге</span>
          </label>
          <button class="primary-button" type="submit">
            Сохранить пользователя
          </button>
        </form>
        <p class="status" :class="statusClass(consoleState.editorStatus)">
          {{ consoleState.editorStatus.text }}
        </p>
      </section>
    </div>

    <div
      class="modal-shell"
      :class="{ 'section-hidden': !consoleState.isAdminModalOpen }"
    >
      <div
        class="modal-backdrop"
        @click="consoleState.isAdminModalOpen = false"
      ></div>
      <section class="modal-panel" role="dialog" aria-modal="true">
        <div class="panel-head">
          <div>
            <h3>Редактирование admin</h3>
            <p class="muted">
              Редактируем роль, статус и при необходимости пароль аккаунта.
            </p>
          </div>
          <div class="modal-head-actions">
            <span class="badge">
              {{
                consoleState.selectedAdmin
                  ? consoleState.selectedAdmin.login
                  : "Не выбран"
              }}
            </span>
            <button
              class="ghost-button"
              type="button"
              @click="consoleState.isAdminModalOpen = false"
            >
              Закрыть
            </button>
          </div>
        </div>
        <form class="form-grid" @submit.prevent="consoleState.saveAdmin">
          <label>
            <span>Role</span>
            <select v-model="consoleState.adminEditForm.role">
              <option value="admin">admin</option>
              <option value="owner">owner</option>
            </select>
          </label>
          <label class="checkbox-row">
            <input
              v-model="consoleState.adminEditForm.isActive"
              type="checkbox"
            />
            <span>Аккаунт активен</span>
          </label>
          <label>
            <span>New password</span>
            <input
              v-model="consoleState.adminEditForm.password"
              type="password"
            />
          </label>
          <button class="primary-button" type="submit">Сохранить admin</button>
        </form>
        <p class="status" :class="statusClass(consoleState.adminEditorStatus)">
          {{ consoleState.adminEditorStatus.text }}
        </p>
      </section>
    </div>

    <div
      class="modal-shell"
      :class="{ 'section-hidden': !consoleState.isAdminCreateModalOpen }"
    >
      <div
        class="modal-backdrop"
        @click="consoleState.isAdminCreateModalOpen = false"
      ></div>
      <section class="modal-panel" role="dialog" aria-modal="true">
        <div class="panel-head">
          <div>
            <h3>Создать admin</h3>
            <p class="muted">
              Создание нового админского аккаунта доступно только owner.
            </p>
          </div>
          <div class="modal-head-actions">
            <button
              class="ghost-button"
              type="button"
              @click="consoleState.isAdminCreateModalOpen = false"
            >
              Закрыть
            </button>
          </div>
        </div>
        <form class="form-grid" @submit.prevent="consoleState.createAdmin">
          <label>
            <span>Login</span>
            <input
              v-model="consoleState.adminCreateForm.login"
              type="text"
              required
            />
          </label>
          <label>
            <span>Password</span>
            <input
              v-model="consoleState.adminCreateForm.password"
              type="password"
              required
            />
          </label>
          <button class="primary-button" type="submit">Создать admin</button>
        </form>
        <p class="status" :class="statusClass(consoleState.adminEditorStatus)">
          {{ consoleState.adminEditorStatus.text }}
        </p>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";

import { useAdminConsole } from "@/features/admin/useAdminConsole";
import "@/shared/styles/admin.css";

const consoleState = useAdminConsole();

const screens = [
  { id: "overview", label: "Обзор" },
  { id: "users", label: "Пользователи" },
  { id: "admins", label: "Администраторы" },
  { id: "audit", label: "Audit log" },
  { id: "profile", label: "Профиль" },
] as const;

const currentScreenLabel = computed(
  () =>
    screens.find((screen) => screen.id === consoleState.activeScreen)?.label ??
    "Обзор",
);

const overviewItems = computed(() => [
  {
    label: "Всего пользователей",
    value: consoleState.overview?.totalUsers ?? "—",
  },
  {
    label: "В рейтинге",
    value: consoleState.overview?.ratingEnabledUsers ?? "—",
  },
  { label: "Всего админов", value: consoleState.overview?.totalAdmins ?? "—" },
  {
    label: "Активных админов",
    value: consoleState.overview?.activeAdmins ?? "—",
  },
  {
    label: "Записей audit log",
    value: consoleState.overview?.auditLogEntries ?? "—",
  },
]);

function statusClass(status: { kind: string }) {
  if (status.kind === "error") {
    return "status-error";
  }
  if (status.kind === "success") {
    return "status-ok";
  }
  return "";
}

onMounted(async () => {
  document.title = `Wobbly Admin ${consoleState.environmentLabel}`;
  await consoleState.initialize();
});
</script>
