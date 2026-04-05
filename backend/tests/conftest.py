from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from psycopg import connect

from app.api.app import create_app
from app.core import config as config_module
from app.core.rate_limit import rate_limiter
from app.db import database as db_module


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration_db: requires TEST_DATABASE_URL and a real PostgreSQL instance",
    )


@pytest.fixture(scope="session")
def integration_database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    return database_url


@pytest.fixture(scope="session")
def migrated_test_database(integration_database_url: str) -> Iterator[str]:
    original_database_url = config_module.settings.database_url
    original_admin_bootstrap_login = config_module.settings.admin_bootstrap_login
    original_admin_bootstrap_password = config_module.settings.admin_bootstrap_password

    config_module.settings.database_url = integration_database_url
    config_module.settings.admin_bootstrap_login = ""
    config_module.settings.admin_bootstrap_password = ""

    db_module.init_db()

    try:
        yield integration_database_url
    finally:
        config_module.settings.database_url = original_database_url
        config_module.settings.admin_bootstrap_login = original_admin_bootstrap_login
        config_module.settings.admin_bootstrap_password = original_admin_bootstrap_password


@pytest.fixture()
def db_client(migrated_test_database: str) -> Iterator[TestClient]:
    with connect(migrated_test_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                TRUNCATE TABLE admin_audit_log, admin_users, users
                RESTART IDENTITY CASCADE;
                """
            )
        conn.commit()

    rate_limiter._events.clear()

    with TestClient(create_app(init_database=False)) as client:
        yield client
