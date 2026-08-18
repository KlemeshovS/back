from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from fastapi import status

from app.core.errors import ApiError, ApiErrorCode
from app.db.database import get_connection
from app.domain.bet_resolution import resolve_bet
from app.domain.schemas import BetListResponse, BetParticipant, BetResponse
from app.services.user_service import build_avatar_url

_BET_SELECT = """
    SELECT
        b.*,
        cu.username AS challenger_username, cu.avatar_path AS challenger_avatar_path,
        ou.username AS opponent_username, ou.avatar_path AS opponent_avatar_path
    FROM bets b
    JOIN users cu ON cu.id = b.challenger_id
    JOIN users ou ON ou.id = b.opponent_id
"""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _end_of_day_utc(d: date) -> datetime:
    """Начало следующего дня после `d` в UTC — эксклюзивная граница "до конца d включительно"."""
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc) + timedelta(days=1)


def _row_to_response(row: dict) -> BetResponse:
    return BetResponse(
        id=row["id"],
        challenger=BetParticipant(
            user_id=row["challenger_id"],
            username=row["challenger_username"],
            avatar_url=build_avatar_url(row["challenger_avatar_path"]),
        ),
        opponent=BetParticipant(
            user_id=row["opponent_id"],
            username=row["opponent_username"],
            avatar_url=build_avatar_url(row["opponent_avatar_path"]),
        ),
        bet_type=row["bet_type"],
        duration_mode=row["duration_mode"],
        duration_days=row["duration_days"],
        target_end_date=row["target_end_date"],
        status=row["status"],
        resolution_type=row["resolution_type"],
        winner_id=row["winner_id"],
        forfeited_by=row["forfeited_by"],
        respond_by=row["respond_by"],
        start_at=row["start_at"],
        end_at=row["end_at"],
        result_snapshot=row["result_snapshot"],
        created_at=row["created_at"],
        accepted_at=row["accepted_at"],
        resolved_at=row["resolved_at"],
    )


def _get_calendar_days(conn, user_id: int) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute("SELECT calendar_data FROM users WHERE id = %s;", (user_id,))
        row = cur.fetchone()
    return (row["calendar_data"] if row else None) or {}


def _resolve_row_if_due(conn, row: dict) -> dict:
    """Ленивая резолюция: пересчитывает статус пари на чтении, если истёк дедлайн.

    Возвращает актуальную (возможно уже обновлённую в БД) строку.
    """
    now = _now()

    if row["status"] == "pending":
        if now <= row["respond_by"]:
            return row
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE bets
                SET status = 'resolved', resolution_type = 'expired', resolved_at = %s
                WHERE id = %s AND status = 'pending'
                RETURNING *;
                """,
                (now, row["id"]),
            )
            updated = cur.fetchone()
        conn.commit()
        return {**row, **updated} if updated else row

    if row["status"] != "active":
        return row

    start_date = row["start_at"].date()
    deadline_passed = now >= row["end_at"]
    last_date = min((row["end_at"] - timedelta(seconds=1)).date(), now.date())

    if last_date < start_date and not deadline_passed:
        return row

    challenger_days = _get_calendar_days(conn, row["challenger_id"])
    opponent_days = _get_calendar_days(conn, row["opponent_id"])

    if row["bet_type"] == "sobriety":
        outcome = resolve_bet("sobriety", challenger_days, opponent_days, start_date, last_date)
        # "На вылет": срыв уже произошёл — резолвим немедленно, не дожидаясь дедлайна.
        should_resolve_now = outcome.winner is not None or deadline_passed
        if not should_resolve_now:
            return row
    else:
        if not deadline_passed:
            return row
        end_date = (row["end_at"] - timedelta(seconds=1)).date()
        outcome = resolve_bet(row["bet_type"], challenger_days, opponent_days, start_date, end_date)

    winner_id = None
    if outcome.winner == "challenger":
        winner_id = row["challenger_id"]
    elif outcome.winner == "opponent":
        winner_id = row["opponent_id"]

    snapshot = {
        "challengerValue": outcome.challenger_value,
        "opponentValue": outcome.opponent_value,
    }

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE bets
            SET status = 'resolved', resolution_type = 'natural',
                winner_id = %s, result_snapshot = %s::jsonb, resolved_at = %s
            WHERE id = %s AND status = 'active'
            RETURNING *;
            """,
            (winner_id, json.dumps(snapshot), now, row["id"]),
        )
        updated = cur.fetchone()
    conn.commit()
    return {**row, **updated} if updated else row


def create_bet(
    challenger_id: int,
    opponent_user_id: int,
    bet_type: str,
    duration_mode: str,
    duration_days: int | None,
    target_end_date: date | None,
) -> BetResponse:
    if challenger_id == opponent_user_id:
        raise ApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=ApiErrorCode.BET_CANNOT_CHALLENGE_SELF,
            message="Нельзя бросить вызов самому себе",
        )

    now = _now()
    if duration_mode == "period":
        respond_by = now + timedelta(days=duration_days)
    else:
        if target_end_date <= now.date():
            raise ApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code=ApiErrorCode.VALIDATION_ERROR,
                message="target_end_date должна быть в будущем",
            )
        respond_by = _end_of_day_utc(target_end_date)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE id = %s AND account_status = 'active';",
                (opponent_user_id,),
            )
            if cur.fetchone() is None:
                raise ApiError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code=ApiErrorCode.USER_NOT_FOUND,
                    message="Пользователь не найден",
                )

            cur.execute(
                """
                SELECT COUNT(*) = 2 AS is_mutual FROM follows
                WHERE (follower_id = %s AND followed_id = %s)
                   OR (follower_id = %s AND followed_id = %s);
                """,
                (challenger_id, opponent_user_id, opponent_user_id, challenger_id),
            )
            if not cur.fetchone()["is_mutual"]:
                raise ApiError(
                    status_code=status.HTTP_403_FORBIDDEN,
                    code=ApiErrorCode.BET_NOT_MUTUAL_FRIEND,
                    message="Бросить вызов можно только взаимному другу",
                )

            cur.execute(
                """
                INSERT INTO bets (
                    challenger_id, opponent_id, bet_type, duration_mode,
                    duration_days, target_end_date, respond_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    challenger_id,
                    opponent_user_id,
                    bet_type,
                    duration_mode,
                    duration_days,
                    target_end_date,
                    respond_by,
                ),
            )
            bet_id = cur.fetchone()["id"]
        conn.commit()

    return get_bet(challenger_id, bet_id)


def _fetch_and_resolve(conn, bet_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(_BET_SELECT + " WHERE b.id = %s;", (bet_id,))
        row = cur.fetchone()
    if row is None:
        return None
    return _resolve_row_if_due(conn, row)


def get_bet(user_id: int, bet_id: int) -> BetResponse:
    with get_connection() as conn:
        row = _fetch_and_resolve(conn, bet_id)

    if row is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ApiErrorCode.BET_NOT_FOUND,
            message="Пари не найдено",
        )
    if user_id not in (row["challenger_id"], row["opponent_id"]):
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ApiErrorCode.BET_FORBIDDEN,
            message="Это пари вам недоступно",
        )
    return _row_to_response(row)


def get_bets(user_id: int) -> BetListResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _BET_SELECT
                + " WHERE b.challenger_id = %s OR b.opponent_id = %s ORDER BY b.created_at DESC;",
                (user_id, user_id),
            )
            rows = cur.fetchall()
        resolved_rows = [_resolve_row_if_due(conn, row) for row in rows]

    items = [_row_to_response(row) for row in resolved_rows]
    return BetListResponse(items=items, total=len(items))


def accept_bet(user_id: int, bet_id: int) -> BetResponse:
    with get_connection() as conn:
        row = _fetch_and_resolve(conn, bet_id)
        if row is None:
            raise ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ApiErrorCode.BET_NOT_FOUND,
                message="Пари не найдено",
            )
        if row["opponent_id"] != user_id:
            raise ApiError(
                status_code=status.HTTP_403_FORBIDDEN,
                code=ApiErrorCode.BET_FORBIDDEN,
                message="Принять пари может только тот, кому бросили вызов",
            )
        if row["status"] != "pending":
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code=ApiErrorCode.BET_INVALID_STATE,
                message="Пари уже не ожидает принятия",
            )

        now = _now()
        start_at = now
        if row["duration_mode"] == "period":
            end_at = _end_of_day_utc((start_at + timedelta(days=row["duration_days"] - 1)).date())
        else:
            end_at = _end_of_day_utc(row["target_end_date"])

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE bets
                SET status = 'active', accepted_at = %s, start_at = %s, end_at = %s
                WHERE id = %s AND status = 'pending'
                RETURNING id;
                """,
                (now, start_at, end_at, bet_id),
            )
            if cur.fetchone() is None:
                raise ApiError(
                    status_code=status.HTTP_409_CONFLICT,
                    code=ApiErrorCode.BET_INVALID_STATE,
                    message="Пари уже не ожидает принятия",
                )
        conn.commit()

    return get_bet(user_id, bet_id)


def decline_bet(user_id: int, bet_id: int) -> BetResponse:
    return _resolve_pending_action(
        user_id=user_id,
        bet_id=bet_id,
        required_role="opponent",
        resolution_type="declined",
    )


def cancel_bet(user_id: int, bet_id: int) -> BetResponse:
    return _resolve_pending_action(
        user_id=user_id,
        bet_id=bet_id,
        required_role="challenger",
        resolution_type="cancelled",
    )


def _resolve_pending_action(
    *, user_id: int, bet_id: int, required_role: str, resolution_type: str
) -> BetResponse:
    with get_connection() as conn:
        row = _fetch_and_resolve(conn, bet_id)
        if row is None:
            raise ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ApiErrorCode.BET_NOT_FOUND,
                message="Пари не найдено",
            )
        expected_user_id = (
            row["opponent_id"] if required_role == "opponent" else row["challenger_id"]
        )
        if expected_user_id != user_id:
            raise ApiError(
                status_code=status.HTTP_403_FORBIDDEN,
                code=ApiErrorCode.BET_FORBIDDEN,
                message="Недостаточно прав для этого действия",
            )
        if row["status"] != "pending":
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code=ApiErrorCode.BET_INVALID_STATE,
                message="Пари уже не в статусе ожидания",
            )

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE bets
                SET status = 'resolved', resolution_type = %s, resolved_at = %s
                WHERE id = %s AND status = 'pending'
                RETURNING id;
                """,
                (resolution_type, _now(), bet_id),
            )
            if cur.fetchone() is None:
                raise ApiError(
                    status_code=status.HTTP_409_CONFLICT,
                    code=ApiErrorCode.BET_INVALID_STATE,
                    message="Пари уже не в статусе ожидания",
                )
        conn.commit()

    return get_bet(user_id, bet_id)


def forfeit_bet(user_id: int, bet_id: int) -> BetResponse:
    with get_connection() as conn:
        row = _fetch_and_resolve(conn, bet_id)
        if row is None:
            raise ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ApiErrorCode.BET_NOT_FOUND,
                message="Пари не найдено",
            )
        if user_id not in (row["challenger_id"], row["opponent_id"]):
            raise ApiError(
                status_code=status.HTTP_403_FORBIDDEN,
                code=ApiErrorCode.BET_FORBIDDEN,
                message="Это пари вам недоступно",
            )
        if row["status"] != "active":
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code=ApiErrorCode.BET_INVALID_STATE,
                message="Слиться можно только в активном пари",
            )

        winner_id = row["opponent_id"] if user_id == row["challenger_id"] else row["challenger_id"]

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE bets
                SET status = 'resolved', resolution_type = 'forfeit',
                    winner_id = %s, forfeited_by = %s, resolved_at = %s
                WHERE id = %s AND status = 'active'
                RETURNING id;
                """,
                (winner_id, user_id, _now(), bet_id),
            )
            if cur.fetchone() is None:
                raise ApiError(
                    status_code=status.HTTP_409_CONFLICT,
                    code=ApiErrorCode.BET_INVALID_STATE,
                    message="Слиться можно только в активном пари",
                )
        conn.commit()

    return get_bet(user_id, bet_id)
