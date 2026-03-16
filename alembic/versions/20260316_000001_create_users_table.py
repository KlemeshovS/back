from __future__ import annotations

from alembic import op


revision = "20260316_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            username VARCHAR(64) UNIQUE,
            auth_token_hash VARCHAR(64) UNIQUE,
            is_rating_enabled BOOLEAN NOT NULL DEFAULT FALSE,
            score INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute("ALTER TABLE users ALTER COLUMN username DROP NOT NULL;")
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS auth_token_hash VARCHAR(64) UNIQUE;
        """
    )
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS is_rating_enabled BOOLEAN NOT NULL DEFAULT FALSE;
        """
    )
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
        """
    )
    op.execute(
        """
        UPDATE users
        SET is_rating_enabled = TRUE
        WHERE username IS NOT NULL AND is_rating_enabled = FALSE;
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_users_score
        ON users (score, username);
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_auth_token_hash
        ON users (auth_token_hash)
        WHERE auth_token_hash IS NOT NULL;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_users_auth_token_hash;")
    op.execute("DROP INDEX IF EXISTS idx_users_score;")
    op.execute("DROP TABLE IF EXISTS users;")
