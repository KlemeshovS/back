"""Replace friendships with follows

Revision ID: 20260513_000009
Revises: 20260512_000008
Create Date: 2026-05-13
"""

from __future__ import annotations

from alembic import op

revision = "20260513_000009"
down_revision = "20260512_000008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS friendships CASCADE;")
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
    op.execute("""
        CREATE TABLE friendships (
            id           BIGSERIAL PRIMARY KEY,
            requester_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            addressee_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status       VARCHAR(16) NOT NULL DEFAULT 'pending'
                         CHECK (status IN ('pending', 'accepted', 'declined')),
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT friendships_unique  UNIQUE (requester_id, addressee_id),
            CONSTRAINT friendships_no_self CHECK  (requester_id <> addressee_id)
        );
    """)
