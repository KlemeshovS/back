from __future__ import annotations

import json

from fastapi import status

from app.core.errors import ApiError, ApiErrorCode
from app.db.database import get_connection
from app.domain.schemas import CalendarResponse

_CALENDAR_MAX_BYTES = 512 * 1024  # 512 KB


def save_calendar(user_id: int, days: dict[str, int]) -> CalendarResponse:
    encoded = json.dumps(days)
    if len(encoded.encode()) > _CALENDAR_MAX_BYTES:
        raise ApiError(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code=ApiErrorCode.CALENDAR_TOO_LARGE,
            message="Calendar data is too large",
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET calendar_data = %s::jsonb,
                    updated_at = NOW(),
                    last_seen_at = NOW()
                WHERE id = %s
                RETURNING calendar_data, updated_at;
                """,
                (encoded, user_id),
            )
            row = cur.fetchone()
        conn.commit()

    return CalendarResponse(days=row["calendar_data"] or {}, updated_at=row["updated_at"])


def get_calendar(user_id: int) -> CalendarResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT calendar_data, updated_at FROM users WHERE id = %s;",
                (user_id,),
            )
            row = cur.fetchone()

    if row is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ApiErrorCode.USER_NOT_FOUND,
            message="User not found",
        )

    return CalendarResponse(days=row["calendar_data"] or {}, updated_at=row["updated_at"])
