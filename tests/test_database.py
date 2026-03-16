from app.db.database import to_sqlalchemy_database_url


def test_to_sqlalchemy_database_url_adds_psycopg_driver() -> None:
    assert (
        to_sqlalchemy_database_url("postgresql://app:pass@db:5432/app")
        == "postgresql+psycopg://app:pass@db:5432/app"
    )


def test_to_sqlalchemy_database_url_keeps_existing_driver() -> None:
    assert (
        to_sqlalchemy_database_url("postgresql+psycopg://app:pass@db:5432/app")
        == "postgresql+psycopg://app:pass@db:5432/app"
    )
