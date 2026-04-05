from __future__ import annotations

import json

from app.core.apple_auth import build_apple_placeholder_username, verify_apple_id_token
from app.core.google_auth import build_google_placeholder_username, verify_google_id_token
from app.core.yandex_auth import build_yandex_placeholder_username, verify_yandex_access_token
from app.db.database import get_connection
from app.domain.schemas import AuthSessionResponse
from app.services.session_service import issue_authenticated_session


def authenticate_google(id_token: str) -> AuthSessionResponse:
    identity = verify_google_id_token(id_token)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.id
                FROM user_identities ui
                JOIN users u ON u.id = ui.user_id
                WHERE ui.provider = 'google'
                  AND ui.provider_user_id = %s;
                """,
                (identity.subject,),
            )
            existing_user = cur.fetchone()

            if existing_user is None:
                cur.execute(
                    """
                    INSERT INTO users (
                        username,
                        account_status
                    )
                    VALUES (%s, 'active')
                    RETURNING id;
                    """,
                    (build_google_placeholder_username(identity.subject),),
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
                    VALUES (%s, 'google', %s, %s, %s, %s::jsonb);
                    """,
                    (
                        user_id,
                        identity.subject,
                        identity.email,
                        identity.email_verified,
                        json.dumps(identity.payload),
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
                      AND provider = 'google'
                      AND provider_user_id = %s;
                    """,
                    (
                        identity.email,
                        identity.email_verified,
                        json.dumps(identity.payload),
                        user_id,
                        identity.subject,
                    ),
                )
        conn.commit()

    return issue_authenticated_session(user_id, "google")


def authenticate_apple(id_token: str) -> AuthSessionResponse:
    identity = verify_apple_id_token(id_token)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.id
                FROM user_identities ui
                JOIN users u ON u.id = ui.user_id
                WHERE ui.provider = 'apple'
                  AND ui.provider_user_id = %s;
                """,
                (identity.subject,),
            )
            existing_user = cur.fetchone()

            if existing_user is None:
                cur.execute(
                    """
                    INSERT INTO users (
                        username,
                        account_status
                    )
                    VALUES (%s, 'active')
                    RETURNING id;
                    """,
                    (build_apple_placeholder_username(identity.subject),),
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
                    VALUES (%s, 'apple', %s, %s, %s, %s::jsonb);
                    """,
                    (
                        user_id,
                        identity.subject,
                        identity.email,
                        identity.email_verified,
                        json.dumps(identity.payload),
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
                      AND provider = 'apple'
                      AND provider_user_id = %s;
                    """,
                    (
                        identity.email,
                        identity.email_verified,
                        json.dumps(identity.payload),
                        user_id,
                        identity.subject,
                    ),
                )
        conn.commit()

    return issue_authenticated_session(user_id, "apple")


def authenticate_yandex(access_token: str) -> AuthSessionResponse:
    identity = verify_yandex_access_token(access_token)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.id
                FROM user_identities ui
                JOIN users u ON u.id = ui.user_id
                WHERE ui.provider = 'yandex'
                  AND ui.provider_user_id = %s;
                """,
                (identity.subject,),
            )
            existing_user = cur.fetchone()

            if existing_user is None:
                cur.execute(
                    """
                    INSERT INTO users (
                        username,
                        account_status
                    )
                    VALUES (%s, 'active')
                    RETURNING id;
                    """,
                    (build_yandex_placeholder_username(identity.subject),),
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
                    VALUES (%s, 'yandex', %s, %s, %s, %s::jsonb);
                    """,
                    (
                        user_id,
                        identity.subject,
                        identity.email,
                        identity.email_verified,
                        json.dumps(identity.payload),
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
                      AND provider = 'yandex'
                      AND provider_user_id = %s;
                    """,
                    (
                        identity.email,
                        identity.email_verified,
                        json.dumps(identity.payload),
                        user_id,
                        identity.subject,
                    ),
                )
        conn.commit()

    return issue_authenticated_session(user_id, "yandex")
