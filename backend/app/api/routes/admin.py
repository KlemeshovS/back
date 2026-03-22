from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import get_current_admin, require_owner
from app.domain.schemas import (
    AdminAuditLogListResponse,
    AdminAuthResponse,
    AdminLoginRequest,
    AdminLogoutResponse,
    AdminMeResponse,
    AdminOverviewResponse,
    AdminPasswordChangeRequest,
    AdminPasswordChangeResponse,
    AdminUserCreateRequest,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdateRequest,
    ManagedUserListResponse,
    ManagedUserResponse,
    ManagedUserUpdateRequest,
)
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])
current_admin_dependency = Depends(get_current_admin)
owner_admin_dependency = Depends(require_owner)


@router.post(
    "/auth/login",
    response_model=AdminAuthResponse,
    status_code=status.HTTP_200_OK,
)
def login_admin(payload: AdminLoginRequest) -> AdminAuthResponse:
    return admin_service.authenticate_admin(payload)


@router.post("/auth/logout", response_model=AdminLogoutResponse)
def logout_admin(current_admin: dict = current_admin_dependency) -> AdminLogoutResponse:
    return admin_service.logout_admin(current_admin)


@router.get("/me", response_model=AdminMeResponse)
def get_admin_me(current_admin: dict = current_admin_dependency) -> AdminMeResponse:
    return admin_service.build_admin_me_response(current_admin)


@router.patch("/me/password", response_model=AdminPasswordChangeResponse)
def change_admin_password(
    payload: AdminPasswordChangeRequest,
    current_admin: dict = current_admin_dependency,
) -> AdminPasswordChangeResponse:
    return admin_service.change_admin_password(payload, current_admin)


@router.get("/overview", response_model=AdminOverviewResponse)
def get_admin_overview(_: dict = current_admin_dependency) -> AdminOverviewResponse:
    return admin_service.get_admin_overview()


@router.get("/users", response_model=ManagedUserListResponse)
def list_users(
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: dict = current_admin_dependency,
) -> ManagedUserListResponse:
    return admin_service.list_managed_users(search, limit, offset)


@router.get("/users/{user_id}", response_model=ManagedUserResponse)
def get_user(user_id: int, _: dict = current_admin_dependency) -> ManagedUserResponse:
    return admin_service.get_managed_user(user_id)


@router.patch("/users/{user_id}", response_model=ManagedUserResponse)
def update_user(
    user_id: int,
    payload: ManagedUserUpdateRequest,
    current_admin: dict = current_admin_dependency,
) -> ManagedUserResponse:
    return admin_service.update_managed_user(user_id, payload, current_admin)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_admin: dict = current_admin_dependency,
) -> Response:
    admin_service.delete_managed_user(user_id, current_admin)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/admin-users", response_model=AdminUserListResponse)
def list_admin_users(_: dict = owner_admin_dependency) -> AdminUserListResponse:
    return admin_service.list_admin_users()


@router.post("/admin-users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_admin_user(
    payload: AdminUserCreateRequest,
    current_admin: dict = owner_admin_dependency,
) -> AdminUserResponse:
    return admin_service.create_admin_user(payload, current_admin)


@router.patch("/admin-users/{admin_id}", response_model=AdminUserResponse)
def update_admin_user(
    admin_id: int,
    payload: AdminUserUpdateRequest,
    current_admin: dict = owner_admin_dependency,
) -> AdminUserResponse:
    return admin_service.update_admin_user(admin_id, payload, current_admin)


@router.delete("/admin-users/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_user(
    admin_id: int,
    current_admin: dict = owner_admin_dependency,
) -> Response:
    admin_service.delete_admin_user(admin_id, current_admin)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/audit-log", response_model=AdminAuditLogListResponse)
def list_admin_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: dict = current_admin_dependency,
) -> AdminAuditLogListResponse:
    return admin_service.list_audit_logs(limit, offset)
