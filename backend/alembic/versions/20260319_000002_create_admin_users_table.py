from __future__ import annotations

from alembic import op


revision = "20260319_000002"
down_revision = "20260316_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_users (
            id BIGSERIAL PRIMARY KEY,
            login VARCHAR(64) NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role VARCHAR(16) NOT NULL DEFAULT 'admin',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            auth_token_hash VARCHAR(64) UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_admin_users_auth_token_hash
        ON admin_users (auth_token_hash)
        WHERE auth_token_hash IS NOT NULL;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_admin_users_auth_token_hash;")
    op.execute("DROP TABLE IF EXISTS admin_users;")
