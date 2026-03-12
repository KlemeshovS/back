from contextlib import contextmanager

from psycopg import connect
from psycopg.rows import dict_row

from app.config import settings


def init_db() -> None:
    with connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    username VARCHAR(64) NOT NULL UNIQUE,
                    score INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_users_score
                ON users (score, username);
                """
            )
        conn.commit()


@contextmanager
def get_connection():
    with connect(settings.database_url, row_factory=dict_row) as conn:
        yield conn
