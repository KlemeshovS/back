from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.domain.schemas import (
    CalendarResponse,
    CalendarSaveRequest,
    TriggersResponse,
    TriggersSaveRequest,
)
from app.services import calendar_service, trigger_service

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
    return calendar_service.save_calendar(current_user["id"], body.days, body.client_updated_at)


@router.get(
    "",
    response_model=CalendarResponse,
    summary="Получить календарь пользователя",
)
def get_calendar(
    current_user: dict = current_user_dependency,
) -> CalendarResponse:
    return calendar_service.get_calendar(current_user["id"])


@router.put(
    "/triggers",
    response_model=TriggersResponse,
    summary="Сохранить дневник триггеров пользователя",
    description=(
        "Сохраняет причины употребления алкоголя по дням (дневник триггеров). "
        "Ключ — дата в формате `YYYY-M-D`, значение — список тегов из фиксированного "
        "набора: `stress`, `boredom`, `party`, `company`, `loneliness`, `conflict`, "
        "`habit`, `other`. Приватные данные — не возвращаются в friend-calendar."
    ),
)
def save_triggers(
    body: TriggersSaveRequest,
    current_user: dict = current_user_dependency,
) -> TriggersResponse:
    return trigger_service.save_triggers(current_user["id"], body.triggers, body.client_updated_at)


@router.get(
    "/triggers",
    response_model=TriggersResponse,
    summary="Получить дневник триггеров пользователя",
)
def get_triggers(
    current_user: dict = current_user_dependency,
) -> TriggersResponse:
    return trigger_service.get_triggers(current_user["id"])
