from fastapi import APIRouter, Depends, Request

from app.api.dependencies import enforce_rate_limit, get_client_ip, get_current_user
from app.core.config import settings
from app.domain.schemas import (
    ProfileResponse,
    ProfileUpdateRequest,
    RatingParticipationUpdateRequest,
    ScoreUpdateRequest,
    UserScoreResponse,
)
from app.services import user_service

router = APIRouter()


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(current_user: dict = Depends(get_current_user)) -> ProfileResponse:
    return ProfileResponse(
        id=current_user["id"],
        username=current_user["username"],
        participate_in_rating=current_user["is_rating_enabled"],
    )


@router.patch("/me/profile", response_model=ProfileResponse)
def update_my_profile(
    payload: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> ProfileResponse:
    username = payload.username if payload.username is not None else current_user["username"]
    return user_service.save_profile(current_user["id"], username, payload.participate_in_rating)


@router.patch("/me/rating", response_model=ProfileResponse)
def update_my_rating_participation(
    payload: RatingParticipationUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> ProfileResponse:
    return user_service.save_profile(
        current_user["id"],
        current_user["username"],
        payload.participate_in_rating,
    )


@router.post("/me/score", response_model=UserScoreResponse)
def update_my_score(
    payload: ScoreUpdateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> UserScoreResponse:
    client_ip = get_client_ip(request)
    enforce_rate_limit(
        key=f"score:ip:{client_ip}",
        limit=settings.score_ip_rate_limit,
        window_seconds=settings.score_ip_window_seconds,
        detail="Too many score updates from this IP. Please try again later.",
    )
    enforce_rate_limit(
        key=f"score:user:id:{current_user['id']}",
        limit=settings.score_username_rate_limit,
        window_seconds=settings.score_username_window_seconds,
        detail="Too many score updates for this user. Please try again later.",
    )
    return user_service.update_my_score(current_user["id"], payload.score)
