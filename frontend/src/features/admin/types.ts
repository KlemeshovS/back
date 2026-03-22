export type AdminRole = "owner" | "admin";

export interface AdminSession {
  token: string;
  role: AdminRole;
  login: string;
}

export interface AdminAuthResponse {
  accessToken: string;
  tokenType: string;
  role: AdminRole;
}

export interface AdminMeResponse {
  id: number;
  login: string;
  role: AdminRole;
  isActive: boolean;
}

export interface AdminOverviewResponse {
  totalUsers: number;
  ratingEnabledUsers: number;
  totalAdmins: number;
  activeAdmins: number;
  auditLogEntries: number;
}

export interface ManagedUserResponse {
  id: number;
  username: string | null;
  score: number;
  participateInRating: boolean;
  createdAt: string;
  updatedAt: string;
  lastSeenAt: string;
}

export interface ManagedUserListResponse {
  items: ManagedUserResponse[];
  total: number;
}

export interface ManagedUserUpdateRequest {
  username?: string | null;
  score?: number;
  participateInRating?: boolean;
}

export interface AdminUserResponse {
  id: number;
  login: string;
  role: AdminRole;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface AdminUserListResponse {
  items: AdminUserResponse[];
  total: number;
}

export interface AdminUserCreateRequest {
  login: string;
  password: string;
}

export interface AdminUserUpdateRequest {
  role?: AdminRole;
  isActive?: boolean;
  password?: string;
}

export interface AdminAuditLogEntryResponse {
  id: number;
  adminId: number;
  adminLogin: string;
  action: string;
  targetType: string;
  targetId: number | null;
  details: Record<string, unknown>;
  createdAt: string;
}

export interface AdminAuditLogListResponse {
  items: AdminAuditLogEntryResponse[];
  total: number;
}

export interface StatusState {
  kind: "idle" | "info" | "success" | "error";
  text: string;
}
