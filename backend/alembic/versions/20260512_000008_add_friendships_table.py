"""add friendships table

Revision ID: 20260512_000008
Revises: 20260418_000007
Create Date: 2026-05-12 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "20260512_000008"
down_revision = "20260418_000007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE friendships (
            id          BIGSERIAL PRIMARY KEY,
            requester_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            addressee_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status      VARCHAR(16) NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending', 'accepted', 'declined')),
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT friendships_unique UNIQUE (requester_id, addressee_id),
            CONSTRAINT friendships_no_self CHECK (requester_id <> addressee_id)
        );
    """)
    op.execute("CREATE INDEX idx_friendships_requester ON friendships (requester_id);")
    op.execute("CREATE INDEX idx_friendships_addressee ON friendships (addressee_id);")
    op.execute("CREATE INDEX idx_friendships_status ON friendships (status);")


def downgrade() -> None:
    op.drop_table("friendships")
