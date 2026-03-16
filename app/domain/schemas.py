from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from typing_extensions import Annotated

Username = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=3,
        max_length=64,
        pattern=r"^[A-Za-z0-9_.-]+$",
    ),
]


class RegisterUserRequest(BaseModel):
    username: Username


class AnonymousAuthResponse(BaseModel):
    user_id: int
    access_token: str
    token_type: str = "bearer"


class ProfileUpdateRequest(BaseModel):
    username: Username | None = None
    participate_in_rating: bool


class RatingParticipationUpdateRequest(BaseModel):
    participate_in_rating: bool


class ProfileResponse(BaseModel):
    id: int
    username: str | None = None
    participate_in_rating: bool


class ScoreUpdateRequest(BaseModel):
    score: int = Field(ge=-2_147_483_648, le=2_147_483_647)


class UpdateScoreRequest(BaseModel):
    user_id: int | None = Field(default=None, ge=1)
    username: Username | None = None
    score: int = Field(ge=-2_147_483_648, le=2_147_483_647)

    @model_validator(mode="after")
    def validate_identifier(self) -> "UpdateScoreRequest":
        if self.user_id is None and self.username is None:
            raise ValueError("Either user_id or username must be provided")

        return self


class UserScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str | None = None
    score: int


class LeaderboardResponse(BaseModel):
    items: list[UserScoreResponse]
    total: int


class StatusResponse(BaseModel):
    status: str
    id: int
    username: str
