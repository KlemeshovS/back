from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import status

from app.core.apple_auth import build_apple_placeholder_username, verify_apple_id_token
from app.core.errors import ApiError, ApiErrorCode
from app.core.google_auth import build_google_placeholder_username, verify_google_id_token
from app.core.usernames import has_public_username, normalize_public_username
from app.core.yandex_auth import build_yandex_placeholder_username, verify_yandex_access_token
from app.db.database import get_connection
from app.domain.schemas import AuthSessionResponse, LinkedIdentityListResponse
from app.services.session_service import (
    issue_authenticated_session,
    resolve_current_user_by_access_token,
)


def authenticate_google(
    id_token: str,
    guest_access_token: Optional[str] = None,
    client_platform: Optional[str] = None,
) -> AuthSessionResponse:
    identity = verify_google_id_token(id_token)
    user_id = _authenticate_social_identity(
        provider="google",
        provider_user_id=identity.subject,
        provider_email=identity.email,
        provider_email_verified=identity.email_verified,
        provider_payload=identity.payload,
        placeholder_username=build_google_placeholder_username(identity.subject),
        guest_access_token=guest_access_token,
    )
    return issue_authenticated_session(user_id, "google", client_platform)


def authenticate_apple(
    id_token: str,
    guest_access_token: Optional[str] = None,
    client_platform: Optional[str] = None,
) -> AuthSessionResponse:
    identity = verify_apple_id_token(id_token)
    user_id = _authenticate_social_identity(
        provider="apple",
        provider_user_id=identity.subject,
        provider_email=identity.email,
        provider_email_verified=identity.email_verified,
        provider_payload=identity.payload,
        placeholder_username=build_apple_placeholder_username(identity.subject),
        guest_access_token=guest_access_token,
    )
    return issue_authenticated_session(user_id, "apple", client_platform)


def authenticate_yandex(
    access_token: str,
    guest_access_token: Optional[str] = None,
    client_platform: Optional[str] = None,
) -> AuthSessionResponse:
    identity = verify_yandex_access_token(access_token)
    user_id = _authenticate_social_identity(
        provider="yandex",
        provider_user_id=identity.subject,
        provider_email=identity.email,
        provider_email_verified=identity.email_verified,
        provider_payload=identity.payload,
        placeholder_username=build_yandex_placeholder_username(identity.subject),
        guest_access_token=guest_access_token,
    )
    return issue_authenticated_session(user_id, "yandex", client_platform)


def list_linked_identities(current_user: dict) -> LinkedIdentityListResponse:
    _require_authenticated_user(current_user)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT provider, provider_email, provider_email_verified, created_at, updated_at
                FROM user_identities
                WHERE user_id = %s
                ORDER BY provider ASC;
                """,
                (current_user["id"],),
            )
            rows = cur.fetchall()

    return LinkedIdentityListResponse(items=list(rows))


def link_google_identity(current_user: dict, id_token: str) -> LinkedIdentityListResponse:
    identity = verify_google_id_token(id_token)
    return _link_identity(
        current_user=current_user,
        provider="google",
        provider_user_id=identity.subject,
        provider_email=identity.email,
        provider_email_verified=identity.email_verified,
        provider_payload=identity.payload,
    )


def link_apple_identity(current_user: dict, id_token: str) -> LinkedIdentityListResponse:
    identity = verify_apple_id_token(id_token)
    return _link_identity(
        current_user=current_user,
        provider="apple",
        provider_user_id=identity.subject,
        provider_email=identity.email,
        provider_email_verified=identity.email_verified,
        provider_payload=identity.payload,
    )


def link_yandex_identity(current_user: dict, access_token: str) -> LinkedIdentityListResponse:
    identity = verify_yandex_access_token(access_token)
    return _link_identity(
        current_user=current_user,
        provider="yandex",
        provider_user_id=identity.subject,
        provider_email=identity.email,
        provider_email_verified=identity.email_verified,
        provider_payload=identity.payload,
    )


def unlink_identity(current_user: dict, provider: str) -> LinkedIdentityListResponse:
    _require_authenticated_user(current_user)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT provider
                FROM user_identities
                WHERE user_id = %s
                ORDER BY provider ASC;
                """,
                (current_user["id"],),
            )
            linked_rows = cur.fetchall()

            if not linked_rows:
                raise ApiError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code=ApiErrorCode.PROVIDER_NOT_LINKED,
                    message="Provider is not linked",
                )

            linked_providers = {row["provider"] for row in linked_rows}
            if provider not in linked_providers:
                raise ApiError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code=ApiErrorCode.PROVIDER_NOT_LINKED,
                    message="Provider is not linked",
                )

            if len(linked_providers) == 1:
                raise ApiError(
                    status_code=status.HTTP_409_CONFLICT,
                    code=ApiErrorCode.LAST_IDENTITY_REQUIRED,
                    message="At least one login method must remain linked",
                )

            cur.execute(
                """
                DELETE FROM user_identities
                WHERE user_id = %s
                  AND provider = %s;
                """,
                (current_user["id"], provider),
            )
        conn.commit()

    return list_linked_identities(current_user)


def _authenticate_social_identity(
    *,
    provider: str,
    provider_user_id: str,
    provider_email: Optional[str],
    provider_email_verified: bool,
    provider_payload: dict,
    placeholder_username: str,
    guest_access_token: Optional[str],
) -> int:
    guest_user = _resolve_guest_user_for_migration(guest_access_token)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.id
                FROM user_identities ui
                JOIN users u ON u.id = ui.user_id
                WHERE ui.provider = %s
                  AND ui.provider_user_id = %s;
                """,
                (provider, provider_user_id),
            )
            existing_user = cur.fetchone()

            if existing_user is None:
                if guest_user is not None:
                    user_id = guest_user["id"]
                    cur.execute(
                        """
                        UPDATE users
                        SET account_status = 'active',
                            guest_migration_key = NULL,
                            updated_at = NOW(),
                            last_seen_at = NOW()
                        WHERE id = %s;
                        """,
                        (user_id,),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO users (
                            username,
                            account_status
                        )
                        VALUES (%s, 'active')
                        RETURNING id;
                        """,
                        (placeholder_username,),
                    )
                    user = cur.fetchone()
                    user_id = user["id"]

                cur.execute(
                    """
                    INSERT INTO user_identities (
                        user_id,
                        provider,
                        provider_user_id,
                        provider_email,
                        provider_email_verified,
                        provider_payload
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb);
                    """,
                    (
                        user_id,
                        provider,
                        provider_user_id,
                        provider_email,
                        provider_email_verified,
                        json.dumps(provider_payload),
                    ),
                )
            else:
                user_id = existing_user["id"]
                cur.execute(
                    """
                    UPDATE users
                    SET account_status = 'active',
                        updated_at = NOW(),
                        last_seen_at = NOW()
                    WHERE id = %s;
                    """,
                    (user_id,),
                )
                cur.execute(
                    """
                    UPDATE user_identities
                    SET provider_email = %s,
                        provider_email_verified = %s,
                        provider_payload = %s::jsonb,
                        updated_at = NOW()
                    WHERE user_id = %s
                      AND provider = %s
                      AND provider_user_id = %s;
                    """,
                    (
                        provider_email,
                        provider_email_verified,
                        json.dumps(provider_payload),
                        user_id,
                        provider,
                        provider_user_id,
                    ),
                )

                if guest_user is not None and guest_user["id"] != user_id:
                    _merge_guest_into_existing_user(
                        cur,
                        guest_user_id=guest_user["id"],
                        target_user_id=user_id,
                    )

        conn.commit()

    return user_id


def _link_identity(
    *,
    current_user: dict,
    provider: str,
    provider_user_id: str,
    provider_email: Optional[str],
    provider_email_verified: bool,
    provider_payload: dict[str, Any],
) -> LinkedIdentityListResponse:
    _require_authenticated_user(current_user)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id
                FROM user_identities
                WHERE provider = %s
                  AND provider_user_id = %s;
                """,
                (provider, provider_user_id),
            )
            existing_identity = cur.fetchone()

            if existing_identity is not None and existing_identity["user_id"] != current_user["id"]:
                raise ApiError(
                    status_code=status.HTTP_409_CONFLICT,
                    code=ApiErrorCode.IDENTITY_ALREADY_LINKED,
                    message="Identity is already linked to another account",
                )

            cur.execute(
                """
                SELECT provider_user_id
                FROM user_identities
                WHERE user_id = %s
                  AND provider = %s;
                """,
                (current_user["id"], provider),
            )
            current_provider_link = cur.fetchone()

            if (
                current_provider_link is not None
                and current_provider_link["provider_user_id"] != provider_user_id
            ):
                raise ApiError(
                    status_code=status.HTTP_409_CONFLICT,
                    code=ApiErrorCode.PROVIDER_ALREADY_LINKED,
                    message="Provider is already linked to this account",
                )

            if current_provider_link is None:
                cur.execute(
                    """
                    INSERT INTO user_identities (
                        user_id,
                        provider,
                        provider_user_id,
                        provider_email,
                        provider_email_verified,
                        provider_payload
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb);
                    """,
                    (
                        current_user["id"],
                        provider,
                        provider_user_id,
                        provider_email,
                        provider_email_verified,
                        json.dumps(provider_payload),
                    ),
                )
            else:
                cur.execute(
                    """
                    UPDATE user_identities
                    SET provider_email = %s,
                        provider_email_verified = %s,
                        provider_payload = %s::jsonb,
                        updated_at = NOW()
                    WHERE user_id = %s
                      AND provider = %s
                      AND provider_user_id = %s;
                    """,
                    (
                        provider_email,
                        provider_email_verified,
                        json.dumps(provider_payload),
                        current_user["id"],
                        provider,
                        provider_user_id,
                    ),
                )
        conn.commit()

    return list_linked_identities(current_user)


def _resolve_guest_user_for_migration(guest_access_token: Optional[str]) -> Optional[dict]:
    if not guest_access_token:
        return None

    current_user = resolve_current_user_by_access_token(guest_access_token)
    if current_user is None or current_user["session_type"] != "guest":
        return None

    return current_user


def _require_authenticated_user(current_user: dict) -> None:
    if current_user["session_type"] != "authenticated":
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ApiErrorCode.AUTH_REQUIRED_FOR_PROVIDER_MANAGEMENT,
            message="Authentication is required for provider management",
        )


def _merge_guest_into_existing_user(cur, *, guest_user_id: int, target_user_id: int) -> None:
    cur.execute(
        """
        SELECT id, username, score, is_rating_enabled
        FROM users
        WHERE id = %s;
        """,
        (guest_user_id,),
    )
    guest_user = cur.fetchone()
    cur.execute(
        """
        SELECT id, username, score, is_rating_enabled
        FROM users
        WHERE id = %s;
        """,
        (target_user_id,),
    )
    target_user = cur.fetchone()

    target_public_username = normalize_public_username(target_user["username"])
    guest_public_username = normalize_public_username(guest_user["username"])

    if target_public_username is not None:
        merged_username = target_user["username"]
    elif guest_public_username is not None:
        merged_username = guest_public_username
    else:
        merged_username = target_user["username"]

    merged_score = guest_user["score"] if guest_user["score"] != 0 else target_user["score"]
    merged_rating_enabled = target_user["is_rating_enabled"] or (
        guest_user["is_rating_enabled"] and has_public_username(merged_username)
    )

    # Free the guest username before moving it onto the target account, otherwise
    # the unique constraint on users.username blocks the merge inside one transaction.
    if guest_public_username is not None and merged_username == guest_public_username:
        cur.execute(
            """
            UPDATE users
            SET username = %s,
                updated_at = NOW()
            WHERE id = %s;
            """,
            (f"anon_user_{guest_user_id}_merged", guest_user_id),
        )

    cur.execute(
        """
        UPDATE users
        SET username = %s,
            score = %s,
            is_rating_enabled = %s,
            updated_at = NOW(),
            last_seen_at = NOW()
        WHERE id = %s;
        """,
        (
            merged_username,
            merged_score,
            merged_rating_enabled,
            target_user_id,
        ),
    )
    cur.execute(
        """
        DELETE FROM users
        WHERE id = %s;
        """,
        (guest_user_id,),
    )
