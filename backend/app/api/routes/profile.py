from typing import Annotated

from fastapi import APIRouter, Depends, File, Request, UploadFile, status

from app.api.dependencies import enforce_rate_limit, get_client_ip, get_current_user
from app.core.config import settings
from app.core.errors import ApiError, ApiErrorCode
from app.domain.schemas import (
    ProfileResponse,
    ProfileUpdateRequest,
    RatingParticipationUpdateRequest,
    ScoreUpdateRequest,
    UserScoreResponse,
)
from app.services import user_service

router = APIRouter()
current_user_dependency = Depends(get_current_user)


def _raise_guest_rating_error(
    *,
    wants_username_save: bool = False,
    wants_rating_enable: bool = False,
) -> None:
    if wants_username_save:
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ApiErrorCode.AUTH_REQUIRED_FOR_USERNAME,
            message="Authentication is required to save username",
        )

    if wants_rating_enable:
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ApiErrorCode.GUEST_CANNOT_ENABLE_RATING,
            message="Guest users cannot enable rating participation",
        )

    raise ApiError(
        status_code=status.HTTP_403_FORBIDDEN,
        code=ApiErrorCode.AUTH_REQUIRED_FOR_RATING,
        message="Authentication is required for rating features",
    )


def _enforce_authenticated_rating_user(
    current_user: dict,
    *,
    wants_username_save: bool = False,
    wants_rating_enable: bool = False,
) -> None:
    if settings.allow_guest_rating:
        return

    if current_user["session_type"] != "authenticated":
        _raise_guest_rating_error(
            wants_username_save=wants_username_save,
            wants_rating_enable=wants_rating_enable,
        )


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(current_user: dict = current_user_dependency) -> ProfileResponse:
    return ProfileResponse(
        id=current_user["id"],
        username=current_user["username"],
        participate_in_rating=current_user["is_rating_enabled"],
        avatar_url=user_service.build_avatar_url(current_user.get("avatar_path")),
    )


@router.patch("/me/profile", response_model=ProfileResponse)
def update_my_profile(
    payload: ProfileUpdateRequest,
    current_user: dict = current_user_dependency,
) -> ProfileResponse:
    _enforce_authenticated_rating_user(
        current_user,
        wants_username_save=payload.username is not None,
        wants_rating_enable=payload.participate_in_rating,
    )
    username = payload.username if payload.username is not None else current_user["username"]
    return user_service.save_profile(current_user["id"], username, payload.participate_in_rating)


@router.patch("/me/rating", response_model=ProfileResponse)
def update_my_rating_participation(
    payload: RatingParticipationUpdateRequest,
    current_user: dict = current_user_dependency,
) -> ProfileResponse:
    _enforce_authenticated_rating_user(
        current_user,
        wants_rating_enable=payload.participate_in_rating,
    )
    return user_service.save_profile(
        current_user["id"],
        current_user["username"],
        payload.participate_in_rating,
    )


@router.post("/me/score", response_model=UserScoreResponse)
def update_my_score(
    payload: ScoreUpdateRequest,
    request: Request,
    current_user: dict = current_user_dependency,
) -> UserScoreResponse:
    _enforce_authenticated_rating_user(current_user)
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


@router.post("/me/avatar", response_model=ProfileResponse)
async def upload_my_avatar(
    file: Annotated[UploadFile, File(...)],
    current_user: dict = current_user_dependency,
) -> ProfileResponse:
    payload = await file.read()
    return user_service.save_my_avatar(
        current_user["id"],
        payload=payload,
        content_type=file.content_type,
    )


@router.delete("/me/avatar", response_model=ProfileResponse)
def delete_my_avatar(current_user: dict = current_user_dependency) -> ProfileResponse:
    return user_service.delete_my_avatar(current_user["id"])
