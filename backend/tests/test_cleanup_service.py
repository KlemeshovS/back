from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock

from app.services.cleanup_service import purge_expired_sessions


def test_purge_expired_sessions_returns_deleted_count(monkeypatch) -> None:
    fake_cursor = MagicMock()
    fake_cursor.__enter__ = lambda s: fake_cursor
    fake_cursor.__exit__ = MagicMock(return_value=False)
    fake_cursor.rowcount = 5

    fake_conn = MagicMock()
    fake_conn.__enter__ = lambda s: fake_conn
    fake_conn.__exit__ = MagicMock(return_value=False)
    fake_conn.cursor.return_value = fake_cursor

    @contextmanager
    def fake_get_connection():
        yield fake_conn

    monkeypatch.setattr("app.services.cleanup_service.get_connection", fake_get_connection)

    deleted = purge_expired_sessions()

    assert deleted == 5
    fake_cursor.execute.assert_called_once()
    fake_conn.commit.assert_called_once()


def test_purge_expired_sessions_returns_zero_when_nothing_to_delete(monkeypatch) -> None:
    fake_cursor = MagicMock()
    fake_cursor.__enter__ = lambda s: fake_cursor
    fake_cursor.__exit__ = MagicMock(return_value=False)
    fake_cursor.rowcount = 0

    fake_conn = MagicMock()
    fake_conn.__enter__ = lambda s: fake_conn
    fake_conn.__exit__ = MagicMock(return_value=False)
    fake_conn.cursor.return_value = fake_cursor

    @contextmanager
    def fake_get_connection():
        yield fake_conn

    monkeypatch.setattr("app.services.cleanup_service.get_connection", fake_get_connection)

    deleted = purge_expired_sessions()

    assert deleted == 0
