from __future__ import annotations

from alembic import op


revision = "20260320_000003"
down_revision = "20260319_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_audit_log (
            id BIGSERIAL PRIMARY KEY,
            admin_id BIGINT NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
            admin_login VARCHAR(64) NOT NULL,
            action VARCHAR(64) NOT NULL,
            target_type VARCHAR(32) NOT NULL,
            target_id BIGINT NULL,
            details JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_admin_audit_log_created_at
        ON admin_audit_log (created_at DESC);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_admin_audit_log_admin_id
        ON admin_audit_log (admin_id);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_admin_audit_log_admin_id;")
    op.execute("DROP INDEX IF EXISTS idx_admin_audit_log_created_at;")
    op.execute("DROP TABLE IF EXISTS admin_audit_log;")
