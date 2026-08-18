from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


def validate_username_input(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    trimmed = value.strip()
    if trimmed == "":
        return ""

    if len(trimmed) < 3:
        raise ValueError("String should have at least 3 characters")

    if len(trimmed) > 64:
        raise ValueError("String should have at most 64 characters")

    import re

    if re.fullmatch(USERNAME_PATTERN, trimmed) is None:
        raise ValueError("String should match pattern '^[A-Za-z0-9_.-]+$'")

    return trimmed


class AdminRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"


class SessionType(str, Enum):
    GUEST = "guest"
    AUTHENTICATED = "authenticated"


class AccountStatus(str, Enum):
    GUEST = "guest"
    ACTIVE = "active"


class AnonymousAuthResponse(ApiModel):
    user_id: int
    access_token: str
    token_type: str = "bearer"


class GoogleAuthRequest(ApiModel):
    id_token: str = Field(min_length=10, max_length=4096)


class AppleAuthRequest(ApiModel):
    id_token: str = Field(min_length=10, max_length=4096)


class YandexAuthRequest(ApiModel):
    access_token: str = Field(min_length=10, max_length=4096)


class AuthSessionResponse(ApiModel):
    user_id: int
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class LinkedIdentityResponse(ApiModel):
    provider: str
    provider_email: Optional[str] = None
    provider_email_verified: bool
    created_at: datetime
    updated_at: datetime


class LinkedIdentityListResponse(ApiModel):
    items: list[LinkedIdentityResponse]


class RefreshSessionRequest(ApiModel):
    refresh_token: str = Field(min_length=10, max_length=4096)


class LogoutResponse(ApiModel):
    status: str = "loggedOut"


class SessionRestoreResponse(ApiModel):
    user_id: int
    username: Optional[str] = None
    participate_in_rating: bool
    session_type: str
    provider: Optional[str] = None
    avatar_url: Optional[str] = None


class ProfileUpdateRequest(ApiModel):
    username: Optional[str] = None
    participate_in_rating: bool

    _validate_username = field_validator("username")(validate_username_input)


class RatingParticipationUpdateRequest(ApiModel):
    participate_in_rating: bool


class ProfileResponse(ApiModel):
    id: int
    username: Optional[str] = None
    participate_in_rating: bool
    avatar_url: Optional[str] = None


class ScoreUpdateRequest(ApiModel):
    score: int = Field(ge=-2_147_483_648, le=2_147_483_647)


class UserScoreResponse(ApiModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    user_id: Optional[int] = None
    username: Optional[str] = None
    score: int
    avatar_url: Optional[str] = None


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


class AdminPasswordChangeRequest(ApiModel):
    current_password: str = Field(min_length=8, max_length=256)
    new_password: str = Field(min_length=8, max_length=256)


class AdminPasswordChangeResponse(ApiModel):
    status: str = "passwordUpdated"


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
    account_status: str
    identity_providers: list[str]
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime


class ManagedUserListResponse(ApiModel):
    items: list[ManagedUserResponse]
    total: int


class ManagedUserUpdateRequest(ApiModel):
    username: Optional[str] = None
    score: Optional[int] = Field(default=None, ge=-2_147_483_648, le=2_147_483_647)
    participate_in_rating: Optional[bool] = None

    _validate_username = field_validator("username")(validate_username_input)


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
    role: Optional[AdminRole] = None
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


# Calendar


class CalendarSaveRequest(ApiModel):
    days: dict[str, int]
    client_updated_at: Optional[datetime] = None


class CalendarResponse(ApiModel):
    days: dict[str, int]
    updated_at: datetime


# Triggers (дневник причин выпить — почему конкретный день отмечен алкоголем)

VALID_TRIGGERS = {
    "stress",
    "boredom",
    "party",
    "company",
    "loneliness",
    "conflict",
    "habit",
    "other",
}


def validate_triggers_input(value: dict[str, list[str]]) -> dict[str, list[str]]:
    for _day_key, tags in value.items():
        for tag in tags:
            if tag not in VALID_TRIGGERS:
                raise ValueError(f"Unknown trigger value: {tag!r}")
    return value


class TriggersSaveRequest(ApiModel):
    triggers: dict[str, list[str]]
    client_updated_at: Optional[datetime] = None

    _validate_triggers = field_validator("triggers")(validate_triggers_input)


class TriggersResponse(ApiModel):
    triggers: dict[str, list[str]]
    updated_at: datetime


# Bets (пари между взаимными друзьями)

VALID_BET_TYPES = {"sobriety", "sport", "score_up", "score_down"}
VALID_DURATION_MODES = {"period", "fixed_date"}
_BET_DURATION_DAYS_MIN = 1
_BET_DURATION_DAYS_MAX = 366


class BetParticipant(ApiModel):
    user_id: int
    username: Optional[str] = None
    avatar_url: Optional[str] = None


class BetCreateRequest(ApiModel):
    opponent_user_id: int
    bet_type: str
    duration_mode: str
    duration_days: Optional[int] = None
    target_end_date: Optional[date] = None

    @field_validator("bet_type")
    @classmethod
    def _validate_bet_type(cls, value: str) -> str:
        if value not in VALID_BET_TYPES:
            raise ValueError(f"Unknown bet_type: {value!r}")
        return value

    @field_validator("duration_mode")
    @classmethod
    def _validate_duration_mode(cls, value: str) -> str:
        if value not in VALID_DURATION_MODES:
            raise ValueError(f"Unknown duration_mode: {value!r}")
        return value

    @field_validator("duration_days")
    @classmethod
    def _validate_duration_days(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and not (_BET_DURATION_DAYS_MIN <= value <= _BET_DURATION_DAYS_MAX):
            raise ValueError(
                "duration_days must be between "
                f"{_BET_DURATION_DAYS_MIN} and {_BET_DURATION_DAYS_MAX}"
            )
        return value

    @model_validator(mode="after")
    def _validate_duration_fields(self) -> "BetCreateRequest":
        if self.duration_mode == "period" and self.duration_days is None:
            raise ValueError("duration_days is required when duration_mode is 'period'")
        if self.duration_mode == "fixed_date" and self.target_end_date is None:
            raise ValueError("target_end_date is required when duration_mode is 'fixed_date'")
        return self


class BetResponse(ApiModel):
    id: int
    challenger: BetParticipant
    opponent: BetParticipant
    bet_type: str
    duration_mode: str
    duration_days: Optional[int] = None
    target_end_date: Optional[date] = None
    status: str
    resolution_type: Optional[str] = None
    winner_id: Optional[int] = None
    forfeited_by: Optional[int] = None
    respond_by: datetime
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    result_snapshot: Optional[dict] = None
    created_at: datetime
    accepted_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class BetListResponse(ApiModel):
    items: list[BetResponse]
    total: int


# Follows


class FollowCreate(ApiModel):
    username: str = Field(min_length=3, max_length=64)


class FollowResponse(ApiModel):
    user_id: int
    username: str
    avatar_url: Optional[str] = None
    is_mutual: bool
    created_at: datetime


class FollowListResponse(ApiModel):
    items: list[FollowResponse]
    total: int
