from __future__ import annotations

import json

from app.core.apple_auth import build_apple_placeholder_username, verify_apple_id_token
from app.core.auth import generate_access_token, hash_access_token
from app.core.google_auth import build_google_placeholder_username, verify_google_id_token
from app.core.yandex_auth import build_yandex_placeholder_username, verify_yandex_access_token
from app.db.database import get_connection
from app.domain.schemas import AuthSessionResponse


def authenticate_google(id_token: str) -> AuthSessionResponse:
    identity = verify_google_id_token(id_token)
    access_token = generate_access_token()
    token_hash = hash_access_token(access_token)

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
                        auth_token_hash,
                        account_status
                    )
                    VALUES (%s, %s, 'active')
                    RETURNING id;
                    """,
                    (
                        build_google_placeholder_username(identity.subject),
                        token_hash,
                    ),
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
                    SET auth_token_hash = %s,
                        account_status = 'active',
                        updated_at = NOW(),
                        last_seen_at = NOW()
                    WHERE id = %s;
                    """,
                    (token_hash, user_id),
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

            cur.execute(
                """
                UPDATE user_sessions
                SET revoked_at = NOW()
                WHERE user_id = %s
                  AND session_type = 'authenticated'
                  AND revoked_at IS NULL;
                """,
                (user_id,),
            )
            cur.execute(
                """
                INSERT INTO user_sessions (
                    user_id,
                    access_token_hash,
                    session_type,
                    provider
                )
                VALUES (%s, %s, 'authenticated', 'google');
                """,
                (user_id, token_hash),
            )
        conn.commit()

    return AuthSessionResponse(user_id=user_id, access_token=access_token)


def authenticate_apple(id_token: str) -> AuthSessionResponse:
    identity = verify_apple_id_token(id_token)
    access_token = generate_access_token()
    token_hash = hash_access_token(access_token)

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
                        auth_token_hash,
                        account_status
                    )
                    VALUES (%s, %s, 'active')
                    RETURNING id;
                    """,
                    (
                        build_apple_placeholder_username(identity.subject),
                        token_hash,
                    ),
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
                    SET auth_token_hash = %s,
                        account_status = 'active',
                        updated_at = NOW(),
                        last_seen_at = NOW()
                    WHERE id = %s;
                    """,
                    (token_hash, user_id),
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

            cur.execute(
                """
                UPDATE user_sessions
                SET revoked_at = NOW()
                WHERE user_id = %s
                  AND session_type = 'authenticated'
                  AND revoked_at IS NULL;
                """,
                (user_id,),
            )
            cur.execute(
                """
                INSERT INTO user_sessions (
                    user_id,
                    access_token_hash,
                    session_type,
                    provider
                )
                VALUES (%s, %s, 'authenticated', 'apple');
                """,
                (user_id, token_hash),
            )
        conn.commit()

    return AuthSessionResponse(user_id=user_id, access_token=access_token)


def authenticate_yandex(access_token: str) -> AuthSessionResponse:
    identity = verify_yandex_access_token(access_token)
    session_access_token = generate_access_token()
    token_hash = hash_access_token(session_access_token)

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
                        auth_token_hash,
                        account_status
                    )
                    VALUES (%s, %s, 'active')
                    RETURNING id;
                    """,
                    (
                        build_yandex_placeholder_username(identity.subject),
                        token_hash,
                    ),
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
                    SET auth_token_hash = %s,
                        account_status = 'active',
                        updated_at = NOW(),
                        last_seen_at = NOW()
                    WHERE id = %s;
                    """,
                    (token_hash, user_id),
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

            cur.execute(
                """
                UPDATE user_sessions
                SET revoked_at = NOW()
                WHERE user_id = %s
                  AND session_type = 'authenticated'
                  AND revoked_at IS NULL;
                """,
                (user_id,),
            )
            cur.execute(
                """
                INSERT INTO user_sessions (
                    user_id,
                    access_token_hash,
                    session_type,
                    provider
                )
                VALUES (%s, %s, 'authenticated', 'yandex');
                """,
                (user_id, token_hash),
            )
        conn.commit()

    return AuthSessionResponse(user_id=user_id, access_token=session_access_token)
