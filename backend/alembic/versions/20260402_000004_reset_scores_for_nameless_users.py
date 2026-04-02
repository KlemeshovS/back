"""Reset scores for nameless users and disable rating for them.

Revision ID: 20260402_000004
Revises: 20260320_000003
Create Date: 2026-04-02 12:10:00
"""

from alembic import op


revision = "20260402_000004"
down_revision = "20260320_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET score = 0,
            is_rating_enabled = FALSE,
            updated_at = NOW()
        WHERE username IS NULL
           OR BTRIM(username) = '';
        """
    )


def downgrade() -> None:
    pass
