import { requestJson } from "@/shared/api/http";

import type {
  AdminAuditLogListResponse,
  AdminAuthResponse,
  AdminMeResponse,
  AdminOverviewResponse,
  AdminUserCreateRequest,
  AdminUserListResponse,
  AdminUserResponse,
  AdminUserUpdateRequest,
  ManagedUserListResponse,
  ManagedUserResponse,
  ManagedUserUpdateRequest,
} from "./types";

function buildHeaders(token?: string): HeadersInit {
  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}

export function createAdminApi(environment: "production" | "staging") {
  const baseUrl = `${window.location.origin}/${environment}/api`;

  return {
    login(login: string, password: string) {
      return requestJson<AdminAuthResponse>(`${baseUrl}/auth/login`, {
        method: "POST",
        body: JSON.stringify({ login, password }),
      });
    },
    logout(token: string) {
      return requestJson<{ status: string }>(`${baseUrl}/auth/logout`, {
        method: "POST",
        headers: buildHeaders(token),
      });
    },
    me(token: string) {
      return requestJson<AdminMeResponse>(`${baseUrl}/me`, {
        headers: buildHeaders(token),
      });
    },
    overview(token: string) {
      return requestJson<AdminOverviewResponse>(`${baseUrl}/overview`, {
        headers: buildHeaders(token),
      });
    },
    users(token: string, search: string) {
      const suffix = search ? `?search=${encodeURIComponent(search)}` : "";
      return requestJson<ManagedUserListResponse>(`${baseUrl}/users${suffix}`, {
        headers: buildHeaders(token),
      });
    },
    user(token: string, userId: number) {
      return requestJson<ManagedUserResponse>(`${baseUrl}/users/${userId}`, {
        headers: buildHeaders(token),
      });
    },
    updateUser(
      token: string,
      userId: number,
      payload: ManagedUserUpdateRequest,
    ) {
      return requestJson<ManagedUserResponse>(`${baseUrl}/users/${userId}`, {
        method: "PATCH",
        headers: buildHeaders(token),
        body: JSON.stringify(payload),
      });
    },
    deleteUser(token: string, userId: number) {
      return requestJson<void>(`${baseUrl}/users/${userId}`, {
        method: "DELETE",
        headers: buildHeaders(token),
      });
    },
    admins(token: string) {
      return requestJson<AdminUserListResponse>(`${baseUrl}/admin-users`, {
        headers: buildHeaders(token),
      });
    },
    createAdmin(token: string, payload: AdminUserCreateRequest) {
      return requestJson<AdminUserResponse>(`${baseUrl}/admin-users`, {
        method: "POST",
        headers: buildHeaders(token),
        body: JSON.stringify(payload),
      });
    },
    updateAdmin(
      token: string,
      adminId: number,
      payload: AdminUserUpdateRequest,
    ) {
      return requestJson<AdminUserResponse>(
        `${baseUrl}/admin-users/${adminId}`,
        {
          method: "PATCH",
          headers: buildHeaders(token),
          body: JSON.stringify(payload),
        },
      );
    },
    deleteAdmin(token: string, adminId: number) {
      return requestJson<void>(`${baseUrl}/admin-users/${adminId}`, {
        method: "DELETE",
        headers: buildHeaders(token),
      });
    },
    auditLog(token: string) {
      return requestJson<AdminAuditLogListResponse>(`${baseUrl}/audit-log`, {
        headers: buildHeaders(token),
      });
    },
  };
}
