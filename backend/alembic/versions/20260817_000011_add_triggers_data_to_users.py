"""add triggers_data to users

Revision ID: 20260817_000011
Revises: 20260523_000010
Create Date: 2026-08-17
"""

from alembic import op

revision = "20260817_000011"
down_revision = "20260523_000010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS triggers_data JSONB;")
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS triggers_updated_at TIMESTAMPTZ;"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS triggers_updated_at;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS triggers_data;")
