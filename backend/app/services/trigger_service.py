from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import status

from app.core.errors import ApiError, ApiErrorCode
from app.db.database import get_connection
from app.domain.schemas import TriggersResponse

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

# Дневник триггеров на порядки меньше календаря (несколько тегов на день,
# не на каждый день), но держим тот же защитный потолок на всякий случай.
_TRIGGERS_MAX_BYTES = 512 * 1024  # 512 KB


def save_triggers(
    user_id: int,
    triggers: dict[str, list[str]],
    client_updated_at: datetime | None = None,
) -> TriggersResponse:
    encoded = json.dumps(triggers)
    if len(encoded.encode()) > _TRIGGERS_MAX_BYTES:
        raise ApiError(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code=ApiErrorCode.TRIGGERS_TOO_LARGE,
            message="Triggers data is too large",
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            if client_updated_at is not None:
                cur.execute(
                    "SELECT triggers_updated_at FROM users WHERE id = %s;",
                    (user_id,),
                )
                row = cur.fetchone()
                if row and row["triggers_updated_at"] is not None:
                    if row["triggers_updated_at"] > client_updated_at:
                        raise ApiError(
                            status_code=status.HTTP_409_CONFLICT,
                            code=ApiErrorCode.TRIGGERS_CONFLICT,
                            message="Данные триггеров были обновлены другим устройством",
                        )

            cur.execute(
                """
                UPDATE users
                SET triggers_data = %s::jsonb,
                    triggers_updated_at = NOW(),
                    last_seen_at = NOW()
                WHERE id = %s
                RETURNING triggers_data, triggers_updated_at;
                """,
                (encoded, user_id),
            )
            row = cur.fetchone()
        conn.commit()

    return TriggersResponse(
        triggers=row["triggers_data"] or {}, updated_at=row["triggers_updated_at"]
    )


def get_triggers(user_id: int) -> TriggersResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT triggers_data, triggers_updated_at, updated_at FROM users WHERE id = %s;",
                (user_id,),
            )
            row = cur.fetchone()

    if row is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ApiErrorCode.USER_NOT_FOUND,
            message="User not found",
        )

    triggers_data = row["triggers_data"]
    if triggers_data is None:
        # Никогда не сохранялось — клиент всегда выиграет сравнение дат
        updated_at = _EPOCH
    elif row["triggers_updated_at"] is not None:
        updated_at = row["triggers_updated_at"]
    else:
        updated_at = row["updated_at"]

    return TriggersResponse(triggers=triggers_data or {}, updated_at=updated_at)
