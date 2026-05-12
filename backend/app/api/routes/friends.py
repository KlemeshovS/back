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


@router.post("", response_model=FriendResponse, status_code=status.HTTP_201_CREATED)
def send_friend_request(
    payload: FriendRequestCreate,
    current_user: dict = current_user_dependency,
) -> FriendResponse:
    _require_authenticated(current_user)
    return friends_service.send_friend_request(current_user["id"], payload.username)


@router.get("", response_model=FriendListResponse)
def get_friends(
    current_user: dict = current_user_dependency,
) -> FriendListResponse:
    _require_authenticated(current_user)
    return friends_service.get_friends(current_user["id"], status_filter="accepted")


@router.get("/requests", response_model=FriendListResponse)
def get_friend_requests(
    current_user: dict = current_user_dependency,
) -> FriendListResponse:
    _require_authenticated(current_user)
    return friends_service.get_friends(current_user["id"], status_filter="pending")


@router.patch("/{friendship_id}", response_model=FriendResponse)
def respond_to_friend_request(
    friendship_id: int,
    payload: FriendActionRequest,
    current_user: dict = current_user_dependency,
) -> FriendResponse:
    _require_authenticated(current_user)
    return friends_service.respond_to_friend_request(
        current_user["id"], friendship_id, payload.action
    )


@router.delete("/{friendship_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_friend(
    friendship_id: int,
    current_user: dict = current_user_dependency,
) -> None:
    _require_authenticated(current_user)
    friends_service.remove_friend(current_user["id"], friendship_id)
