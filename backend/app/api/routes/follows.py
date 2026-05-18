from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user
from app.core.errors import ApiError, ApiErrorCode
from app.domain.schemas import (
    FollowCreate,
    FollowListResponse,
    FollowResponse,
    SessionType,
)
from app.services import follows_service

router = APIRouter(prefix="/follows", tags=["follows"])
current_user_dependency = Depends(get_current_user)


def _require_authenticated(current_user: dict) -> None:
    if current_user["session_type"] != SessionType.AUTHENTICATED:
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ApiErrorCode.AUTH_REQUIRED_FOR_RATING,
            message="Требуется авторизация для работы с подписками",
        )


@router.post(
    "",
    response_model=FollowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Подписаться на пользователя",
    description=(
        "Подписывается на пользователя по username. Если другой пользователь уже подписан "
        "на вас, подписка становится взаимной (isMutual=true) — это означает дружбу. "
        "Лимит подписок — 500. Только для авторизованных пользователей."
    ),
    responses={
        403: {"description": "AUTH_REQUIRED_FOR_RATING"},
        404: {"description": "USER_NOT_FOUND"},
        409: {"description": "ALREADY_FOLLOWING"},
        422: {"description": "CANNOT_FOLLOW_SELF или FOLLOWS_LIMIT_REACHED"},
    },
)
def follow_user(
    payload: FollowCreate,
    current_user: dict = current_user_dependency,
) -> FollowResponse:
    _require_authenticated(current_user)
    return follows_service.follow_user(current_user["id"], payload.username)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отписаться от пользователя",
    description="Отписывается от пользователя по его userId. Возвращает 204 No Content.",
    responses={
        403: {"description": "AUTH_REQUIRED_FOR_RATING"},
        404: {"description": "NOT_FOLLOWING"},
    },
)
def unfollow_user(
    user_id: int,
    current_user: dict = current_user_dependency,
) -> None:
    _require_authenticated(current_user)
    follows_service.unfollow_user(current_user["id"], user_id)


@router.get(
    "",
    response_model=FollowListResponse,
    summary="Мои подписки (кого читаю). isMutual=true — взаимная подписка.",
    responses={
        403: {"description": "AUTH_REQUIRED_FOR_RATING"},
    },
)
def get_follows(
    current_user: dict = current_user_dependency,
) -> FollowListResponse:
    _require_authenticated(current_user)
    return follows_service.get_follows(current_user["id"])


@router.get(
    "/followers",
    response_model=FollowListResponse,
    summary="Мои подписчики (кто читает меня). isMutual=true — взаимная подписка.",
    responses={
        403: {"description": "AUTH_REQUIRED_FOR_RATING"},
    },
)
def get_followers(
    current_user: dict = current_user_dependency,
) -> FollowListResponse:
    _require_authenticated(current_user)
    return follows_service.get_followers(current_user["id"])


@router.get(
    "/friends",
    response_model=FollowListResponse,
    summary="Взаимные подписки (друзья)",
    description="Пользователи с взаимной подпиской (друзья). Все элементы имеют isMutual=true.",
    responses={
        403: {"description": "AUTH_REQUIRED_FOR_RATING"},
    },
)
def get_friends(
    current_user: dict = current_user_dependency,
) -> FollowListResponse:
    _require_authenticated(current_user)
    return follows_service.get_mutual_follows(current_user["id"])
