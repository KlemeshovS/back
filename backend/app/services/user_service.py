from __future__ import annotations

import json
from typing import Optional

from fastapi import status
from psycopg.errors import UniqueViolation

from app.core.auth import generate_access_token, hash_access_token
from app.core.config import settings
from app.core.errors import ApiError, ApiErrorCode
from app.core.media import (
    build_avatar_storage_path,
    build_avatar_url,
    delete_avatar_file,
    ensure_media_directories,
    validate_avatar_image,
)
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

_ACTIVE_RATING_USER_FILTER = (
    "is_rating_enabled = TRUE\n"
    "  AND username IS NOT NULL\n"
    "  AND BTRIM(username) <> ''\n"
    "  AND username NOT LIKE 'anon_user_%%'\n"
    "  AND last_seen_at >= NOW() - INTERVAL '30 days'"
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
                    SELECT username, avatar_path
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
                    public_username_for_rules = existing_public_username
                    stored_username = (
                        existing_public_username
                        if existing_public_username is not None
                        else existing_user["username"]
                    )
                else:
                    public_username_for_rules = requested_public_username
                    stored_username = requested_public_username

                if participate_in_rating and not public_username_for_rules:
                    raise ApiError(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        code=ApiErrorCode.USERNAME_REQUIRED_FOR_RATING,
                        message="Username is required to participate in rating",
                    )

                if (
                    existing_public_username
                    and username is not None
                    and requested_public_username is None
                ):
                    raise ApiError(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        code=ApiErrorCode.USERNAME_CANNOT_BE_CLEARED,
                        message="Username cannot be cleared once set",
                    )

                if stored_username is None and existing_public_username is None:
                    stored_username = existing_user["username"]

                cur.execute(
                    """
                    UPDATE users
                    SET username = %s,
                        is_rating_enabled = %s,
                        updated_at = NOW(),
                        last_seen_at = NOW()
                    WHERE id = %s
                    RETURNING id, username, is_rating_enabled, avatar_path;
                    """,
                    (stored_username, participate_in_rating, user_id),
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
        avatar_url=build_avatar_url(user.get("avatar_path")),
    )


def create_anonymous_user(client_platform: Optional[str] = None) -> AnonymousAuthResponse:
    access_token = generate_access_token()
    token_hash = hash_access_token(access_token)
    anonymous_username = build_anonymous_username(token_hash)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (auth_token_hash, username, account_status, guest_migration_key)
                VALUES (%s, %s, 'guest', %s)
                RETURNING id, created_at, last_seen_at;
                """,
                (token_hash, anonymous_username, token_hash),
            )
            user = cur.fetchone()
            cur.execute(
                """
                INSERT INTO user_sessions (
                    user_id,
                    access_token_hash,
                    session_type,
                    client_platform,
                    created_at,
                    last_seen_at
                )
                VALUES (%s, %s, 'guest', %s, %s, %s);
                """,
                (
                    user["id"],
                    token_hash,
                    client_platform,
                    user["created_at"],
                    user["last_seen_at"],
                ),
            )
        conn.commit()

    return AnonymousAuthResponse(user_id=user["id"], access_token=access_token)


def update_my_score(user_id: int, score: int) -> UserScoreResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT username, is_rating_enabled
                    , avatar_path
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
                RETURNING username, score, avatar_path;
                """,
                (score, user_id),
            )
            user = cur.fetchone()
        conn.commit()

    return UserScoreResponse(
        username=normalize_public_username(user["username"]),
        score=user["score"],
        avatar_url=build_avatar_url(user.get("avatar_path")),
    )


def save_my_avatar(
    user_id: int,
    *,
    payload: bytes,
    content_type: str | None,
) -> ProfileResponse:
    if len(payload) > settings.avatar_max_bytes:
        raise ApiError(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code=ApiErrorCode.AVATAR_TOO_LARGE,
            message="Avatar file is too large",
        )

    ensure_media_directories()
    extension = validate_avatar_image(content_type, payload)
    relative_path, absolute_path = build_avatar_storage_path(user_id=user_id, extension=extension)

    old_avatar_path: str | None = None
    try:
        absolute_path.write_bytes(payload)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT avatar_path
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
                old_avatar_path = existing_user["avatar_path"]

                cur.execute(
                    """
                    UPDATE users
                    SET avatar_path = %s,
                        updated_at = NOW(),
                        last_seen_at = NOW()
                    WHERE id = %s
                    RETURNING id, username, is_rating_enabled, avatar_path;
                    """,
                    (relative_path, user_id),
                )
                user = cur.fetchone()
            conn.commit()
    except Exception:
        absolute_path.unlink(missing_ok=True)
        raise

    if old_avatar_path and old_avatar_path != relative_path:
        delete_avatar_file(old_avatar_path)

    return ProfileResponse(
        id=user["id"],
        username=normalize_public_username(user["username"]),
        participate_in_rating=user["is_rating_enabled"],
        avatar_url=build_avatar_url(user["avatar_path"]),
    )


def delete_my_avatar(user_id: int) -> ProfileResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT avatar_path
                FROM users
                WHERE id = %s;
                """,
                (user_id,),
            )
            existing = cur.fetchone()
            if existing is None:
                raise ApiError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code=ApiErrorCode.USER_NOT_FOUND,
                    message="User not found",
                )

            old_avatar_path = existing["avatar_path"]
            cur.execute(
                """
                UPDATE users
                SET avatar_path = NULL,
                    updated_at = NOW(),
                    last_seen_at = NOW()
                WHERE id = %s
                RETURNING id, username, is_rating_enabled, avatar_path;
                """,
                (user_id,),
            )
            user = cur.fetchone()
        conn.commit()

    delete_avatar_file(old_avatar_path)

    return ProfileResponse(
        id=user["id"],
        username=normalize_public_username(user["username"]),
        participate_in_rating=user["is_rating_enabled"],
        avatar_url=None,
    )


def delete_my_account(user_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT username, score, is_rating_enabled, avatar_path
                FROM users
                WHERE id = %s;
                """,
                (user_id,),
            )
            existing = cur.fetchone()
            if existing is None:
                raise ApiError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code=ApiErrorCode.USER_NOT_FOUND,
                    message="User not found",
                )
            avatar_path = existing["avatar_path"]

            cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))

            cur.execute(
                """
                INSERT INTO admin_audit_log (
                    admin_id, admin_login, action, target_type, target_id, details
                )
                VALUES (NULL, 'user_self', 'user.self_delete', 'user', %s, %s::jsonb);
                """,
                (
                    user_id,
                    json.dumps({
                        "before": {
                            "id": user_id,
                            "username": existing["username"],
                            "score": existing["score"],
                            "is_rating_enabled": existing["is_rating_enabled"],
                        }
                    }),
                ),
            )
        conn.commit()

    if avatar_path:
        delete_avatar_file(avatar_path)


def fetch_leaderboard(order: str, score_filter: str, limit: int) -> LeaderboardResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM users
                WHERE {_ACTIVE_RATING_USER_FILTER}
                  AND score {score_filter};
                """
            )
            total_row = cur.fetchone()
            cur.execute(
                f"""
                SELECT username, score, avatar_path
                FROM users
                WHERE {_ACTIVE_RATING_USER_FILTER}
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
                avatar_url=build_avatar_url(row.get("avatar_path")),
            )
            for row in rows
        ],
        total=total_row["total"],
    )
