from pydantic import BaseModel, ConfigDict, Field, StringConstraints
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


class UpdateScoreRequest(BaseModel):
    username: Username
    score: int = Field(ge=-2_147_483_648, le=2_147_483_647)


class UserScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    score: int


class LeaderboardResponse(BaseModel):
    items: list[UserScoreResponse]
    total: int


class StatusResponse(BaseModel):
    status: str
    username: str
