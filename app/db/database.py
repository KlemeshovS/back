from contextlib import contextmanager
from pathlib import Path

from psycopg import connect
from psycopg.rows import dict_row

from app.core.config import settings


def init_db() -> None:
    import alembic.command as alembic_command
    import alembic.config as alembic_config

    root_dir = Path(__file__).resolve().parents[2]
    config = alembic_config.Config(str(root_dir / "alembic.ini"))
    config.set_main_option("script_location", str(root_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    alembic_command.upgrade(config, "head")


@contextmanager
def get_connection():
    with connect(settings.database_url, row_factory=dict_row) as conn:
        yield conn
