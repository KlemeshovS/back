from __future__ import annotations

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
