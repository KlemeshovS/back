"""Add social auth schema and guest migration scaffolding.

Revision ID: 20260405_000005
Revises: 20260402_000004
Create Date: 2026-04-05 13:45:00
"""

from __future__ import annotations

from alembic import op


revision = "20260405_000005"
down_revision = "20260402_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS account_status VARCHAR(16) NOT NULL DEFAULT 'guest';
        """
    )
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS guest_migration_key VARCHAR(64);
        """
    )
    op.execute(
        """
        UPDATE users
        SET guest_migration_key = auth_token_hash
        WHERE guest_migration_key IS NULL
          AND auth_token_hash IS NOT NULL;
        """
    )
    op.execute(
        """
        ALTER TABLE users
        DROP CONSTRAINT IF EXISTS users_account_status_valid;
        """
    )
    op.execute(
        """
        ALTER TABLE users
        ADD CONSTRAINT users_account_status_valid
        CHECK (account_status IN ('guest', 'active'));
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_guest_migration_key
        ON users (guest_migration_key)
        WHERE guest_migration_key IS NOT NULL;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_identities (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            provider VARCHAR(16) NOT NULL,
            provider_user_id VARCHAR(255) NOT NULL,
            provider_email VARCHAR(320),
            provider_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
            provider_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT user_identities_provider_valid
                CHECK (provider IN ('google', 'apple', 'yandex'))
        );
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_user_identities_provider_subject
        ON user_identities (provider, provider_user_id);
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_user_identities_user_provider
        ON user_identities (user_id, provider);
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_sessions (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            access_token_hash VARCHAR(64),
            refresh_token_hash VARCHAR(64),
            session_type VARCHAR(16) NOT NULL,
            provider VARCHAR(16),
            device_id VARCHAR(255),
            client_platform VARCHAR(64),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ,
            last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            revoked_at TIMESTAMPTZ,
            CONSTRAINT user_sessions_session_type_valid
                CHECK (session_type IN ('guest', 'authenticated')),
            CONSTRAINT user_sessions_provider_valid
                CHECK (provider IS NULL OR provider IN ('google', 'apple', 'yandex'))
        );
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_user_sessions_access_token_hash
        ON user_sessions (access_token_hash)
        WHERE access_token_hash IS NOT NULL;
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_user_sessions_refresh_token_hash
        ON user_sessions (refresh_token_hash)
        WHERE refresh_token_hash IS NOT NULL;
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id
        ON user_sessions (user_id);
        """
    )

    op.execute(
        """
        INSERT INTO user_sessions (
            user_id,
            access_token_hash,
            session_type,
            created_at,
            last_seen_at
        )
        SELECT
            users.id,
            users.auth_token_hash,
            'guest',
            users.created_at,
            users.last_seen_at
        FROM users
        WHERE users.auth_token_hash IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM user_sessions
              WHERE user_sessions.access_token_hash = users.auth_token_hash
          );
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_user_sessions_user_id;")
    op.execute("DROP INDEX IF EXISTS idx_user_sessions_refresh_token_hash;")
    op.execute("DROP INDEX IF EXISTS idx_user_sessions_access_token_hash;")
    op.execute("DROP TABLE IF EXISTS user_sessions;")

    op.execute("DROP INDEX IF EXISTS idx_user_identities_user_provider;")
    op.execute("DROP INDEX IF EXISTS idx_user_identities_provider_subject;")
    op.execute("DROP TABLE IF EXISTS user_identities;")

    op.execute("DROP INDEX IF EXISTS idx_users_guest_migration_key;")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_account_status_valid;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS guest_migration_key;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS account_status;")
