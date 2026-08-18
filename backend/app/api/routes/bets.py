from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user
from app.core.errors import ApiError, ApiErrorCode
from app.domain.schemas import (
    BetCreateRequest,
    BetListResponse,
    BetResponse,
    SessionType,
)
from app.services import bets_service

router = APIRouter(prefix="/me/bets", tags=["bets"])
current_user_dependency = Depends(get_current_user)


def _require_authenticated(current_user: dict) -> None:
    if current_user["session_type"] != SessionType.AUTHENTICATED:
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ApiErrorCode.AUTH_REQUIRED_FOR_RATING,
            message="Пари доступны только авторизованным пользователям",
        )


@router.post(
    "",
    response_model=BetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Бросить вызов другу",
    description=(
        "Создаёт пари со взаимным другом. Тип пари: `sobriety` (кто сорвётся первым — "
        "проиграл), `sport` (у кого больше спортивных дней за срок), `score_up` (у кого "
        "больше очков за срок, считая с нуля от старта), `score_down` (у кого очков "
        "меньше). Срок задаётся либо периодом (`duration_days`), либо конкретной датой "
        "(`targetEndDate`). Пари стартует не сразу, а с момента принятия оппонентом — "
        "до этого момента статус `pending`. Дедлайн на принятие равен самому сроку пари "
        "(тот же период/дата)."
    ),
    responses={
        403: {"description": "AUTH_REQUIRED_FOR_RATING или BET_NOT_MUTUAL_FRIEND"},
        404: {"description": "USER_NOT_FOUND"},
        422: {"description": "BET_CANNOT_CHALLENGE_SELF или VALIDATION_ERROR"},
    },
)
def create_bet(
    body: BetCreateRequest,
    current_user: dict = current_user_dependency,
) -> BetResponse:
    _require_authenticated(current_user)
    return bets_service.create_bet(
        current_user["id"],
        body.opponent_user_id,
        body.bet_type,
        body.duration_mode,
        body.duration_days,
        body.target_end_date,
    )


@router.get(
    "",
    response_model=BetListResponse,
    summary="Все пари пользователя (входящие, активные, история)",
    description=(
        "Возвращает все пари, где пользователь — challenger или opponent, отсортированные "
        "по дате создания (новые сверху). Просроченные/истёкшие пари резолвятся лениво "
        "прямо при этом запросе. Разбивку на входящие/активные/историю делает клиент по "
        "полям `status`/`resolutionType`/`opponent.userId`."
    ),
    responses={403: {"description": "AUTH_REQUIRED_FOR_RATING"}},
)
def get_bets(current_user: dict = current_user_dependency) -> BetListResponse:
    _require_authenticated(current_user)
    return bets_service.get_bets(current_user["id"])


@router.get(
    "/{bet_id}",
    response_model=BetResponse,
    summary="Детали одного пари",
    responses={
        403: {"description": "AUTH_REQUIRED_FOR_RATING или BET_FORBIDDEN"},
        404: {"description": "BET_NOT_FOUND"},
    },
)
def get_bet(
    bet_id: int,
    current_user: dict = current_user_dependency,
) -> BetResponse:
    _require_authenticated(current_user)
    return bets_service.get_bet(current_user["id"], bet_id)


@router.post(
    "/{bet_id}/accept",
    response_model=BetResponse,
    summary="Принять вызов",
    description=(
        "Только оппонент, только пока пари в статусе pending. "
        "Запускает отсчёт срока с этого момента."
    ),
    responses={
        403: {"description": "AUTH_REQUIRED_FOR_RATING или BET_FORBIDDEN"},
        404: {"description": "BET_NOT_FOUND"},
        409: {"description": "BET_INVALID_STATE"},
    },
)
def accept_bet(
    bet_id: int,
    current_user: dict = current_user_dependency,
) -> BetResponse:
    _require_authenticated(current_user)
    return bets_service.accept_bet(current_user["id"], bet_id)


@router.post(
    "/{bet_id}/decline",
    response_model=BetResponse,
    summary="Отклонить вызов",
    description="Только оппонент, только пока пари в статусе pending.",
    responses={
        403: {"description": "AUTH_REQUIRED_FOR_RATING или BET_FORBIDDEN"},
        404: {"description": "BET_NOT_FOUND"},
        409: {"description": "BET_INVALID_STATE"},
    },
)
def decline_bet(
    bet_id: int,
    current_user: dict = current_user_dependency,
) -> BetResponse:
    _require_authenticated(current_user)
    return bets_service.decline_bet(current_user["id"], bet_id)


@router.post(
    "/{bet_id}/cancel",
    response_model=BetResponse,
    summary="Отозвать брошенный вызов",
    description="Только автор (challenger), только пока пари в статусе pending.",
    responses={
        403: {"description": "AUTH_REQUIRED_FOR_RATING или BET_FORBIDDEN"},
        404: {"description": "BET_NOT_FOUND"},
        409: {"description": "BET_INVALID_STATE"},
    },
)
def cancel_bet(
    bet_id: int,
    current_user: dict = current_user_dependency,
) -> BetResponse:
    _require_authenticated(current_user)
    return bets_service.cancel_bet(current_user["id"], bet_id)


@router.post(
    "/{bet_id}/forfeit",
    response_model=BetResponse,
    summary="Слиться из активного пари",
    description="Любой участник, только пока пари active. Автоматическая победа второго участника.",
    responses={
        403: {"description": "AUTH_REQUIRED_FOR_RATING или BET_FORBIDDEN"},
        404: {"description": "BET_NOT_FOUND"},
        409: {"description": "BET_INVALID_STATE"},
    },
)
def forfeit_bet(
    bet_id: int,
    current_user: dict = current_user_dependency,
) -> BetResponse:
    _require_authenticated(current_user)
    return bets_service.forfeit_bet(current_user["id"], bet_id)
