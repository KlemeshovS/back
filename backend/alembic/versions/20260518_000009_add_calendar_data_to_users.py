"""add calendar_data to users

Revision ID: 20260518_000009
Revises: 20260512_000008
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa

revision = "20260518_000009"
down_revision = "20260512_000008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS calendar_data JSONB;")


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN calendar_data;")
