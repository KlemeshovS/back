"""Add bets table

Revision ID: 20260818_000012
Revises: 20260817_000011
Create Date: 2026-08-18
"""

from alembic import op

revision = "20260818_000012"
down_revision = "20260817_000011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE bets (
            id              BIGSERIAL PRIMARY KEY,
            challenger_id   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            opponent_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            bet_type        TEXT NOT NULL,
            duration_mode   TEXT NOT NULL,
            duration_days   INTEGER,
            target_end_date DATE,
            status          TEXT NOT NULL DEFAULT 'pending',
            resolution_type TEXT,
            winner_id       BIGINT REFERENCES users(id) ON DELETE SET NULL,
            forfeited_by    BIGINT REFERENCES users(id) ON DELETE SET NULL,
            respond_by      TIMESTAMPTZ NOT NULL,
            start_at        TIMESTAMPTZ,
            end_at          TIMESTAMPTZ,
            result_snapshot JSONB,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            accepted_at     TIMESTAMPTZ,
            resolved_at     TIMESTAMPTZ,
            CONSTRAINT bets_no_self CHECK (challenger_id <> opponent_id),
            CONSTRAINT bets_type_valid CHECK (
                bet_type IN ('sobriety', 'sport', 'score_up', 'score_down')
            ),
            CONSTRAINT bets_duration_mode_valid CHECK (
                duration_mode IN ('period', 'fixed_date')
            ),
            CONSTRAINT bets_status_valid CHECK (
                status IN ('pending', 'active', 'resolved')
            ),
            CONSTRAINT bets_resolution_type_valid CHECK (
                resolution_type IS NULL OR resolution_type IN
                ('declined', 'cancelled', 'expired', 'natural', 'forfeit')
            )
        );
    """)
    op.execute("CREATE INDEX ON bets (challenger_id);")
    op.execute("CREATE INDEX ON bets (opponent_id);")
    op.execute("CREATE INDEX ON bets (status);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS bets CASCADE;")
