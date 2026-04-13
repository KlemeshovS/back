from __future__ import annotations

from typing import Optional

from fastapi import status

from app.core.auth import generate_access_token, generate_refresh_token, hash_access_token
from app.core.config import settings
from app.core.errors import ApiError, ApiErrorCode
from app.core.media import build_avatar_url
from app.core.usernames import normalize_public_username
from app.db.database import get_connection
from app.domain.schemas import AuthSessionResponse, LogoutResponse, SessionRestoreResponse


def issue_authenticated_session(
    user_id: int, provider: str, client_platform: Optional[str] = None
) -> AuthSessionResponse:
    access_token = generate_access_token()
    refresh_token = generate_refresh_token()
    access_token_hash = hash_access_token(access_token)
    refresh_token_hash = hash_access_token(refresh_token)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE user_sessions
                SET revoked_at = NOW()
                WHERE user_id = %s
                  AND revoked_at IS NULL;
                """,
                (user_id,),
            )
            cur.execute(
                """
                INSERT INTO user_sessions (
                    user_id,
                    access_token_hash,
                    refresh_token_hash,
                    session_type,
                    provider,
                    client_platform,
                    expires_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    'authenticated',
                    %s,
                    %s,
                    NOW() + make_interval(secs => %s)
                );
                """,
                (
                    user_id,
                    access_token_hash,
                    refresh_token_hash,
                    provider,
                    client_platform,
                    settings.auth_refresh_token_ttl_seconds,
                ),
            )
            cur.execute(
                """
                UPDATE users
                SET auth_token_hash = %s,
                    account_status = 'active',
                    updated_at = NOW(),
                    last_seen_at = NOW()
                WHERE id = %s;
                """,
                (access_token_hash, user_id),
            )
        conn.commit()

    return AuthSessionResponse(
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
    )


def refresh_authenticated_session(refresh_token: str) -> AuthSessionResponse:
    refresh_token_hash = hash_access_token(refresh_token)
    access_token = generate_access_token()
    new_refresh_token = generate_refresh_token()
    access_token_hash = hash_access_token(access_token)
    new_refresh_token_hash = hash_access_token(new_refresh_token)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id
                FROM user_sessions
                WHERE refresh_token_hash = %s
                  AND session_type = 'authenticated'
                  AND revoked_at IS NULL
                  AND (expires_at IS NULL OR expires_at > NOW());
                """,
                (refresh_token_hash,),
            )
            session = cur.fetchone()

            if session is None:
                raise ApiError(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ApiErrorCode.INVALID_REFRESH_TOKEN,
                    message="Invalid refresh token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            cur.execute(
                """
                UPDATE user_sessions
                SET access_token_hash = %s,
                    refresh_token_hash = %s,
                    expires_at = NOW() + make_interval(secs => %s),
                    last_seen_at = NOW()
                WHERE id = %s;
                """,
                (
                    access_token_hash,
                    new_refresh_token_hash,
                    settings.auth_refresh_token_ttl_seconds,
                    session["id"],
                ),
            )
            cur.execute(
                """
                UPDATE users
                SET auth_token_hash = %s,
                    updated_at = NOW(),
                    last_seen_at = NOW()
                WHERE id = %s;
                """,
                (access_token_hash, session["user_id"]),
            )
        conn.commit()

    return AuthSessionResponse(
        user_id=session["user_id"],
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


def restore_session(current_session: dict) -> SessionRestoreResponse:
    return SessionRestoreResponse(
        user_id=current_session["id"],
        username=current_session["username"],
        participate_in_rating=current_session["is_rating_enabled"],
        session_type=current_session["session_type"],
        provider=current_session["provider"],
        avatar_url=build_avatar_url(current_session.get("avatar_path")),
    )


def logout_session(current_session: dict) -> LogoutResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if current_session["session_id"] is not None:
                cur.execute(
                    """
                    UPDATE user_sessions
                    SET revoked_at = NOW()
                    WHERE id = %s
                      AND revoked_at IS NULL;
                    """,
                    (current_session["session_id"],),
                )
            cur.execute(
                """
                UPDATE users
                SET auth_token_hash = NULL,
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (current_session["id"],),
            )
        conn.commit()

    return LogoutResponse()


def resolve_current_user_by_access_token(token: str) -> dict | None:
    token_hash = hash_access_token(token)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    u.id,
                    u.username,
                    u.score,
                    u.is_rating_enabled,
                    u.avatar_path,
                    us.id AS session_id,
                    us.session_type,
                    us.provider
                FROM user_sessions us
                JOIN users u ON u.id = us.user_id
                WHERE us.access_token_hash = %s
                  AND us.revoked_at IS NULL
                ORDER BY us.id DESC
                LIMIT 1;
                """,
                (token_hash,),
            )
            user = cur.fetchone()

            if user is not None:
                cur.execute(
                    """
                    UPDATE user_sessions
                    SET last_seen_at = NOW()
                    WHERE id = %s;
                    """,
                    (user["session_id"],),
                )
                cur.execute(
                    """
                    UPDATE users
                    SET last_seen_at = NOW()
                    WHERE id = %s;
                    """,
                    (user["id"],),
                )
                conn.commit()
            else:
                cur.execute(
                    """
                    SELECT id, username, score, is_rating_enabled, account_status
                    , avatar_path
                    FROM users
                    WHERE auth_token_hash = %s;
                    """,
                    (token_hash,),
                )
                legacy_user = cur.fetchone()
                if legacy_user is None:
                    return None

                user = {
                    "id": legacy_user["id"],
                    "username": legacy_user["username"],
                    "score": legacy_user["score"],
                    "is_rating_enabled": legacy_user["is_rating_enabled"],
                    "session_id": None,
                    "session_type": legacy_user["account_status"],
                    "provider": None,
                    "avatar_path": legacy_user["avatar_path"],
                }

    user["username"] = normalize_public_username(user["username"])
    return user
