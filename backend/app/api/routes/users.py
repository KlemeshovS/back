from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.domain.schemas import CalendarResponse
from app.services import calendar_service

router = APIRouter(prefix="/users", tags=["users"])
current_user_dependency = Depends(get_current_user)


@router.get(
    "/{user_id}/calendar",
    response_model=CalendarResponse,
    summary="Получить календарь друга",
    description=(
        "Возвращает календарь пользователя по его ID. "
        "Доступно только если есть взаимная подписка (дружба). "
        "Если подписка не взаимная — возвращает `403 NOT_FRIENDS`."
    ),
    responses={
        403: {"description": "NOT_FRIENDS"},
        404: {"description": "USER_NOT_FOUND"},
    },
)
def get_friend_calendar(
    user_id: int,
    current_user: dict = current_user_dependency,
) -> CalendarResponse:
    return calendar_service.get_friend_calendar(current_user["id"], user_id)
