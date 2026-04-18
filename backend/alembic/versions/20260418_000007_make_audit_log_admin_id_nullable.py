"""make admin_audit_log.admin_id nullable for user self-actions

Revision ID: 20260418_000007
Revises: 20260412_000006
Create Date: 2026-04-18 10:00:00.000000
"""

from alembic import op

revision = "20260418_000007"
down_revision = "20260412_000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE admin_audit_log
            ALTER COLUMN admin_id DROP NOT NULL;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE admin_audit_log SET admin_id = 0 WHERE admin_id IS NULL;
        ALTER TABLE admin_audit_log
            ALTER COLUMN admin_id SET NOT NULL;
        """
    )
