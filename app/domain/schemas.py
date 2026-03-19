from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

USERNAME_PATTERN = r"^[A-Za-z0-9_.-]+$"
Username = str


class AdminRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"


class AnonymousAuthResponse(ApiModel):
    user_id: int
    access_token: str
    token_type: str = "bearer"


class ProfileUpdateRequest(ApiModel):
    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=64,
        pattern=USERNAME_PATTERN,
    )
    participate_in_rating: bool


class RatingParticipationUpdateRequest(ApiModel):
    participate_in_rating: bool


class ProfileResponse(ApiModel):
    id: int
    username: Optional[str] = None
    participate_in_rating: bool


class ScoreUpdateRequest(ApiModel):
    score: int = Field(ge=-2_147_483_648, le=2_147_483_647)


class UserScoreResponse(ApiModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    username: Optional[str] = None
    score: int


class LeaderboardResponse(ApiModel):
    items: list[UserScoreResponse]
    total: int


class ErrorResponse(ApiModel):
    code: str
    message: str


class AdminLoginRequest(ApiModel):
    login: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=256)


class AdminAuthResponse(ApiModel):
    access_token: str
    token_type: str = "bearer"
    role: AdminRole


class AdminLogoutResponse(ApiModel):
    status: str = "loggedOut"


class AdminMeResponse(ApiModel):
    id: int
    login: str
    role: AdminRole
    is_active: bool


class AdminOverviewResponse(ApiModel):
    total_users: int
    rating_enabled_users: int
    total_admins: int
    active_admins: int
    audit_log_entries: int


class ManagedUserResponse(ApiModel):
    id: int
    username: Optional[str] = None
    score: int
    participate_in_rating: bool
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime


class ManagedUserListResponse(ApiModel):
    items: list[ManagedUserResponse]
    total: int


class ManagedUserUpdateRequest(ApiModel):
    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=64,
        pattern=USERNAME_PATTERN,
    )
    score: Optional[int] = Field(default=None, ge=-2_147_483_648, le=2_147_483_647)
    participate_in_rating: Optional[bool] = None


class AdminUserResponse(ApiModel):
    id: int
    login: str
    role: AdminRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminUserListResponse(ApiModel):
    items: list[AdminUserResponse]
    total: int


class AdminUserCreateRequest(ApiModel):
    login: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=256)


class AdminUserUpdateRequest(ApiModel):
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=256)


class AdminAuditLogEntryResponse(ApiModel):
    id: int
    admin_id: int
    admin_login: str
    action: str
    target_type: str
    target_id: Optional[int] = None
    details: dict
    created_at: datetime


class AdminAuditLogListResponse(ApiModel):
    items: list[AdminAuditLogEntryResponse]
    total: int
