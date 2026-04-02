from __future__ import annotations

from typing import Optional

from fastapi import status
from psycopg.errors import UniqueViolation

from app.core.auth import generate_access_token, hash_access_token
from app.core.errors import ApiError, ApiErrorCode
from app.db.database import get_connection
from app.domain.schemas import (
    AnonymousAuthResponse,
    LeaderboardResponse,
    ProfileResponse,
    UserScoreResponse,
)


def _normalize_username(username: Optional[str]) -> Optional[str]:
    if username is None:
        return None

    normalized = username.strip()
    return normalized or None


def save_profile(
    user_id: int,
    username: Optional[str],
    participate_in_rating: bool,
) -> ProfileResponse:
    normalized_username = _normalize_username(username)

    if participate_in_rating and not normalized_username:
        raise ApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=ApiErrorCode.USERNAME_REQUIRED_FOR_RATING,
            message="Username is required to participate in rating",
        )

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET username = %s,
                        is_rating_enabled = %s,
                        score = CASE WHEN %s IS NULL THEN 0 ELSE score END,
                        updated_at = NOW(),
                        last_seen_at = NOW()
                    WHERE id = %s
                    RETURNING id, username, is_rating_enabled;
                    """,
                    (normalized_username, participate_in_rating, normalized_username, user_id),
                )
                user = cur.fetchone()
            conn.commit()
    except UniqueViolation as exc:
        raise ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code=ApiErrorCode.USERNAME_ALREADY_EXISTS,
            message="Username already exists",
        ) from exc

    return ProfileResponse(
        id=user["id"],
        username=user["username"],
        participate_in_rating=user["is_rating_enabled"],
    )


def create_anonymous_user() -> AnonymousAuthResponse:
    access_token = generate_access_token()
    token_hash = hash_access_token(access_token)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (auth_token_hash)
                VALUES (%s)
                RETURNING id;
                """,
                (token_hash,),
            )
            user = cur.fetchone()
        conn.commit()

    return AnonymousAuthResponse(user_id=user["id"], access_token=access_token)


def update_my_score(user_id: int, score: int) -> UserScoreResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT username, is_rating_enabled
                FROM users
                WHERE id = %s;
                """,
                (user_id,),
            )
            existing_user = cur.fetchone()

            if not existing_user["username"]:
                raise ApiError(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code=ApiErrorCode.USERNAME_REQUIRED_FOR_RATING,
                    message="Username is required to submit score",
                )

            if not existing_user["is_rating_enabled"]:
                raise ApiError(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code=ApiErrorCode.RATING_DISABLED_FOR_SCORE,
                    message="Rating must be enabled to submit score",
                )

            cur.execute(
                """
                UPDATE users
                SET score = %s,
                    updated_at = NOW(),
                    last_seen_at = NOW()
                WHERE id = %s
                RETURNING username, score;
                """,
                (score, user_id),
            )
            user = cur.fetchone()
        conn.commit()

    return UserScoreResponse(**user)


def fetch_leaderboard(order: str, score_filter: str, limit: int) -> LeaderboardResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM users
                WHERE is_rating_enabled = TRUE
                  AND username IS NOT NULL
                  AND BTRIM(username) <> ''
                  AND score {score_filter};
                """
            )
            total_row = cur.fetchone()
            cur.execute(
                f"""
                SELECT username, score
                FROM users
                WHERE is_rating_enabled = TRUE
                  AND username IS NOT NULL
                  AND BTRIM(username) <> ''
                  AND score {score_filter}
                ORDER BY score {order}, username ASC
                LIMIT %s;
                """,
                (limit,),
            )
            rows = cur.fetchall()

    return LeaderboardResponse(
        items=[UserScoreResponse(**row) for row in rows],
        total=total_row["total"],
    )
