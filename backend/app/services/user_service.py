from __future__ import annotations

from typing import Optional

from fastapi import status
from psycopg.errors import UniqueViolation

from app.core.auth import generate_access_token, hash_access_token
from app.core.errors import ApiError, ApiErrorCode
from app.core.usernames import (
    build_anonymous_username,
    has_public_username,
    normalize_public_username,
)
from app.db.database import get_connection
from app.domain.schemas import (
    AnonymousAuthResponse,
    LeaderboardResponse,
    ProfileResponse,
    UserScoreResponse,
)


def save_profile(
    user_id: int,
    username: Optional[str],
    participate_in_rating: bool,
) -> ProfileResponse:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT username
                    FROM users
                    WHERE id = %s;
                    """,
                    (user_id,),
                )
                existing_user = cur.fetchone()

                if existing_user is None:
                    raise ApiError(
                        status_code=status.HTTP_404_NOT_FOUND,
                        code=ApiErrorCode.USER_NOT_FOUND,
                        message="User not found",
                    )

                existing_public_username = normalize_public_username(existing_user["username"])
                requested_public_username = normalize_public_username(username)

                if username is None:
                    normalized_username = (
                        existing_public_username
                        if existing_public_username is not None
                        else existing_user["username"]
                    )
                else:
                    normalized_username = requested_public_username

                if participate_in_rating and not normalized_username:
                    raise ApiError(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        code=ApiErrorCode.USERNAME_REQUIRED_FOR_RATING,
                        message="Username is required to participate in rating",
                    )

                cur.execute(
                    """
                    UPDATE users
                    SET username = %s,
                        is_rating_enabled = %s,
                        updated_at = NOW(),
                        last_seen_at = NOW()
                    WHERE id = %s
                    RETURNING id, username, is_rating_enabled;
                    """,
                    (normalized_username, participate_in_rating, user_id),
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
        username=normalize_public_username(user["username"]),
        participate_in_rating=user["is_rating_enabled"],
    )


def create_anonymous_user() -> AnonymousAuthResponse:
    access_token = generate_access_token()
    token_hash = hash_access_token(access_token)
    anonymous_username = build_anonymous_username(token_hash)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (auth_token_hash, username)
                VALUES (%s)
                RETURNING id;
                """,
                (token_hash, anonymous_username),
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

            if not has_public_username(existing_user["username"]):
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

    return UserScoreResponse(
        username=normalize_public_username(user["username"]),
        score=user["score"],
    )


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
                  AND username NOT LIKE 'anon_user_%%'
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
                  AND username NOT LIKE 'anon_user_%%'
                  AND score {score_filter}
                ORDER BY score {order}, username ASC
                LIMIT %s;
                """,
                (limit,),
            )
            rows = cur.fetchall()

    return LeaderboardResponse(
        items=[
            UserScoreResponse(
                username=normalize_public_username(row["username"]),
                score=row["score"],
            )
            for row in rows
        ],
        total=total_row["total"],
    )
