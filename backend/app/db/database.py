from contextlib import contextmanager
from pathlib import Path

from psycopg import connect
from psycopg.rows import dict_row

from app.core.admin_auth import hash_password
from app.core.config import settings


def to_sqlalchemy_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def init_db() -> None:
    import alembic.command as alembic_command
    import alembic.config as alembic_config

    root_dir = Path(__file__).resolve().parents[2]
    config = alembic_config.Config(str(root_dir / "alembic.ini"))
    config.set_main_option("script_location", str(root_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", to_sqlalchemy_database_url(settings.database_url))
    alembic_command.upgrade(config, "head")
    ensure_bootstrap_admin()


def ensure_bootstrap_admin() -> None:
    if not settings.admin_bootstrap_login or not settings.admin_bootstrap_password:
        return

    with connect(settings.database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM admin_users
                WHERE role = 'owner'
                LIMIT 1;
                """
            )
            existing_owner = cur.fetchone()
            if existing_owner is not None:
                return

            cur.execute(
                """
                INSERT INTO admin_users (login, password_hash, role, is_active)
                VALUES (%s, %s, 'owner', TRUE);
                """,
                (
                    settings.admin_bootstrap_login,
                    hash_password(settings.admin_bootstrap_password),
                ),
            )
        conn.commit()


@contextmanager
def get_connection():
    with connect(settings.database_url, row_factory=dict_row) as conn:
        yield conn
