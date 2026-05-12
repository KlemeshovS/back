from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user
from app.core.errors import ApiError, ApiErrorCode
from app.domain.schemas import (
    FriendActionRequest,
    FriendListResponse,
    FriendRequestCreate,
    FriendResponse,
    SessionType,
)
from app.services import friends_service

router = APIRouter(prefix="/friends", tags=["friends"])
current_user_dependency = Depends(get_current_user)


def _require_authenticated(current_user: dict) -> None:
    if current_user["session_type"] != SessionType.AUTHENTICATED:
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ApiErrorCode.AUTH_REQUIRED_FOR_RATING,
            message="Authentication is required to use friends",
        )


@router.post(
    "",
    response_model=FriendResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Отправить заявку в друзья",
    description=(
        "Отправляет заявку в друзья пользователю по его username. "
        "Доступно только для авторизованных пользователей. "
        "Лимит принятых дружб — 200. "
        "Нельзя отправить заявку самому себе или повторно, если заявка уже существует."
    ),
    responses={
        403: {"description": "Требуется авторизация (AUTH_REQUIRED_FOR_RATING)"},
        404: {"description": "Пользователь не найден (USER_NOT_FOUND)"},
        409: {"description": "ALREADY_FRIENDS или FRIEND_REQUEST_ALREADY_SENT"},
        422: {"description": "CANNOT_ADD_SELF или FRIENDS_LIMIT_REACHED"},
    },
)
def send_friend_request(
    payload: FriendRequestCreate,
    current_user: dict = current_user_dependency,
) -> FriendResponse:
    _require_authenticated(current_user)
    return friends_service.send_friend_request(current_user["id"], payload.username)


@router.get(
    "",
    response_model=FriendListResponse,
    summary="Список друзей",
    description="Возвращает список принятых дружб текущего пользователя (status=accepted).",
    responses={
        403: {"description": "Требуется авторизация (AUTH_REQUIRED_FOR_RATING)"},
    },
)
def get_friends(
    current_user: dict = current_user_dependency,
) -> FriendListResponse:
    _require_authenticated(current_user)
    return friends_service.get_friends(current_user["id"], status_filter="accepted")


@router.get(
    "/requests",
    response_model=FriendListResponse,
    summary="Входящие и исходящие заявки",
    description=(
        "Возвращает все pending-заявки текущего пользователя. "
        "Для разделения входящих и исходящих использовать поле isRequester: "
        "false — входящая (можно принять/отклонить), true — исходящая (можно отменить)."
    ),
    responses={
        403: {"description": "Требуется авторизация (AUTH_REQUIRED_FOR_RATING)"},
    },
)
def get_friend_requests(
    current_user: dict = current_user_dependency,
) -> FriendListResponse:
    _require_authenticated(current_user)
    return friends_service.get_friends(current_user["id"], status_filter="pending")


@router.patch(
    "/{friendship_id}",
    response_model=FriendResponse,
    summary="Принять или отклонить заявку",
    description=(
        "Только адресат заявки (isRequester=false) может принять или отклонить её. "
        "Допустимые значения action: accept, decline."
    ),
    responses={
        403: {"description": "Требуется авторизация (AUTH_REQUIRED_FOR_RATING)"},
        404: {"description": "FRIEND_REQUEST_NOT_FOUND"},
        409: {"description": "Заявка больше не в статусе pending (FRIEND_REQUEST_NOT_FOUND)"},
    },
)
def respond_to_friend_request(
    friendship_id: int,
    payload: FriendActionRequest,
    current_user: dict = current_user_dependency,
) -> FriendResponse:
    _require_authenticated(current_user)
    return friends_service.respond_to_friend_request(
        current_user["id"], friendship_id, payload.action
    )


@router.delete(
    "/{friendship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить друга или отменить заявку",
    description=(
        "Удаляет дружбу или отменяет заявку. Доступно любой из сторон. "
        "Возвращает 204 No Content при успехе."
    ),
    responses={
        403: {"description": "Требуется авторизация (AUTH_REQUIRED_FOR_RATING)"},
        404: {"description": "NOT_FRIENDS"},
    },
)
def remove_friend(
    friendship_id: int,
    current_user: dict = current_user_dependency,
) -> None:
    _require_authenticated(current_user)
    friends_service.remove_friend(current_user["id"], friendship_id)
