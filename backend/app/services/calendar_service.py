from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import status

from app.core.errors import ApiError, ApiErrorCode
from app.db.database import get_connection
from app.domain.schemas import CalendarResponse

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

_CALENDAR_MAX_BYTES = 512 * 1024  # 512 KB


def save_calendar(
    user_id: int,
    days: dict[str, int],
    client_updated_at: datetime | None = None,
) -> CalendarResponse:
    encoded = json.dumps(days)
    if len(encoded.encode()) > _CALENDAR_MAX_BYTES:
        raise ApiError(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code=ApiErrorCode.CALENDAR_TOO_LARGE,
            message="Calendar data is too large",
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            if client_updated_at is not None:
                cur.execute(
                    "SELECT calendar_updated_at FROM users WHERE id = %s;",
                    (user_id,),
                )
                row = cur.fetchone()
                if row and row["calendar_updated_at"] is not None:
                    if row["calendar_updated_at"] > client_updated_at:
                        raise ApiError(
                            status_code=status.HTTP_409_CONFLICT,
                            code=ApiErrorCode.CALENDAR_CONFLICT,
                            message="Данные календаря были обновлены другим устройством",
                        )

            cur.execute(
                """
                UPDATE users
                SET calendar_data = %s::jsonb,
                    calendar_updated_at = NOW(),
                    last_seen_at = NOW()
                WHERE id = %s
                RETURNING calendar_data, calendar_updated_at;
                """,
                (encoded, user_id),
            )
            row = cur.fetchone()
        conn.commit()

    return CalendarResponse(days=row["calendar_data"] or {}, updated_at=row["calendar_updated_at"])


def get_friend_calendar(requester_id: int, target_user_id: int) -> CalendarResponse:
    if requester_id == target_user_id:
        return get_calendar(requester_id)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    calendar_data,
                    calendar_updated_at,
                    updated_at,
                    (
                        SELECT COUNT(*) = 2 FROM follows
                        WHERE (follower_id = %s AND followed_id = %s)
                           OR (follower_id = %s AND followed_id = %s)
                    ) AS is_mutual
                FROM users WHERE id = %s;
                """,
                (requester_id, target_user_id, target_user_id, requester_id, target_user_id),
            )
            row = cur.fetchone()

    if row is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ApiErrorCode.USER_NOT_FOUND,
            message="Пользователь не найден",
        )

    if not row["is_mutual"]:
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ApiErrorCode.NOT_FRIENDS,
            message="Календарь доступен только друзьям",
        )

    calendar_data = row["calendar_data"]
    if calendar_data is None:
        updated_at = _EPOCH
    elif row["calendar_updated_at"] is not None:
        updated_at = row["calendar_updated_at"]
    else:
        updated_at = row["updated_at"]

    return CalendarResponse(days=calendar_data or {}, updated_at=updated_at)


def get_calendar(user_id: int) -> CalendarResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT calendar_data, calendar_updated_at, updated_at FROM users WHERE id = %s;",
                (user_id,),
            )
            row = cur.fetchone()

    if row is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ApiErrorCode.USER_NOT_FOUND,
            message="User not found",
        )

    calendar_data = row["calendar_data"]
    if calendar_data is None:
        # Никогда не сохранялось — клиент всегда выиграет сравнение дат
        updated_at = _EPOCH
    elif row["calendar_updated_at"] is not None:
        updated_at = row["calendar_updated_at"]
    else:
        # Данные сохранены до calendar_updated_at — используем updated_at как прокси
        updated_at = row["updated_at"]

    return CalendarResponse(days=calendar_data or {}, updated_at=updated_at)
