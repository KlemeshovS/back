from fastapi import APIRouter, Request, status

from app.api.dependencies import enforce_rate_limit, get_client_ip
from app.core.config import settings
from app.domain.schemas import (
    RegisterUserRequest,
    StatusResponse,
    UpdateScoreRequest,
    UserScoreResponse,
)
from app.services import user_service

router = APIRouter()


@router.post(
    "/users/register",
    response_model=StatusResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(payload: RegisterUserRequest, request: Request) -> StatusResponse:
    client_ip = get_client_ip(request)
    enforce_rate_limit(
        key=f"register:ip:{client_ip}",
        limit=settings.register_rate_limit,
        window_seconds=settings.register_window_seconds,
        detail="Too many registration attempts. Please try again later.",
    )
    return user_service.register_user(payload.username)


@router.post("/users/score", response_model=UserScoreResponse)
def update_score(payload: UpdateScoreRequest, request: Request) -> UserScoreResponse:
    client_ip = get_client_ip(request)
    enforce_rate_limit(
        key=f"score:ip:{client_ip}",
        limit=settings.score_ip_rate_limit,
        window_seconds=settings.score_ip_window_seconds,
        detail="Too many score updates from this IP. Please try again later.",
    )
    if payload.user_id is not None:
        user_key = f"id:{payload.user_id}"
    else:
        user_key = f"username:{payload.username.lower()}"

    enforce_rate_limit(
        key=f"score:user:{user_key}",
        limit=settings.score_username_rate_limit,
        window_seconds=settings.score_username_window_seconds,
        detail="Too many score updates for this user. Please try again later.",
    )

    return user_service.update_legacy_score(
        score=payload.score,
        user_id=payload.user_id,
        username=payload.username,
    )
