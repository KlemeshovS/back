from contextlib import contextmanager

from psycopg import connect
from psycopg.rows import dict_row

from app.core.config import settings


def init_db() -> None:
    with connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    username VARCHAR(64) UNIQUE,
                    auth_token_hash VARCHAR(64) UNIQUE,
                    is_rating_enabled BOOLEAN NOT NULL DEFAULT FALSE,
                    score INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute("ALTER TABLE users ALTER COLUMN username DROP NOT NULL;")
            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS auth_token_hash VARCHAR(64) UNIQUE;
                """
            )
            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS is_rating_enabled BOOLEAN NOT NULL DEFAULT FALSE;
                """
            )
            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
                """
            )
            cur.execute(
                """
                UPDATE users
                SET is_rating_enabled = TRUE
                WHERE username IS NOT NULL AND is_rating_enabled = FALSE;
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_users_score
                ON users (score, username);
                """
            )
            cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_users_auth_token_hash
                ON users (auth_token_hash)
                WHERE auth_token_hash IS NOT NULL;
                """
            )
        conn.commit()


@contextmanager
def get_connection():
    with connect(settings.database_url, row_factory=dict_row) as conn:
        yield conn
