"""add user avatar path

Revision ID: 20260412_000006
Revises: 20260405_000005
Create Date: 2026-04-12 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260412_000006"
down_revision = "20260405_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_path", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_path")
