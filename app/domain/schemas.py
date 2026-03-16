from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class RegisterUserRequest(ApiModel):
    username: str = Field(min_length=3, max_length=64, pattern=USERNAME_PATTERN)


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


class UpdateScoreRequest(ApiModel):
    user_id: Optional[int] = Field(default=None, ge=1)
    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=64,
        pattern=USERNAME_PATTERN,
    )
    score: int = Field(ge=-2_147_483_648, le=2_147_483_647)

    @model_validator(mode="after")
    def validate_identifier(self) -> "UpdateScoreRequest":
        if self.user_id is None and self.username is None:
            raise ValueError("Either user_id or username must be provided")

        return self


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


class StatusResponse(ApiModel):
    status: str
    id: int
    username: str


class ErrorResponse(ApiModel):
    code: str
    message: str
