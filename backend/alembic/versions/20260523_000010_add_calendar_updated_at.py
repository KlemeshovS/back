"""add calendar_updated_at to users

Revision ID: 20260523_000010
Revises: 20260518_000009
Create Date: 2026-05-23
"""

from alembic import op

revision = "20260523_000010"
down_revision = "20260518_000009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS calendar_updated_at TIMESTAMPTZ;"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS calendar_updated_at;")
