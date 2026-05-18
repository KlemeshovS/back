"""Add follows table

Revision ID: 20260512_000008
Revises: 20260418_000007
Create Date: 2026-05-12 00:00:00.000000
"""

from alembic import op

revision = "20260512_000008"
down_revision = "20260418_000007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE follows (
            id          BIGSERIAL PRIMARY KEY,
            follower_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            followed_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT follows_unique  UNIQUE (follower_id, followed_id),
            CONSTRAINT follows_no_self CHECK  (follower_id <> followed_id)
        );
    """)
    op.execute("CREATE INDEX ON follows (follower_id);")
    op.execute("CREATE INDEX ON follows (followed_id);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS follows CASCADE;")
