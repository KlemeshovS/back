from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.domain.schemas import CalendarResponse, CalendarSaveRequest
from app.services import calendar_service

router = APIRouter(prefix="/me/calendar", tags=["calendar"])
current_user_dependency = Depends(get_current_user)


@router.put(
    "",
    response_model=CalendarResponse,
    summary="Сохранить календарь пользователя",
    description=(
        "Сохраняет ежедневные записи пользователя. "
        "Ключ — дата в формате `YYYY-M-D`, значение — целое число (DrinkLevel):\n"
        "- `0` — трезвый\n"
        "- `1` — мало\n"
        "- `2` — средне\n"
        "- `3` — много\n"
        "- `4` — спорт\n"
        "- `5` — мало + спорт\n"
        "- `6` — средне + спорт\n"
        "- `7` — много + спорт"
    ),
)
def save_calendar(
    body: CalendarSaveRequest,
    current_user: dict = current_user_dependency,
) -> CalendarResponse:
    return calendar_service.save_calendar(current_user["user_id"], body.days)


@router.get(
    "",
    response_model=CalendarResponse,
    summary="Получить календарь пользователя",
)
def get_calendar(
    current_user: dict = current_user_dependency,
) -> CalendarResponse:
    return calendar_service.get_calendar(current_user["user_id"])
