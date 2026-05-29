from __future__ import annotations

from datetime import datetime, timezone
from unittest import mock

from app.api.dependencies import get_current_user
from app.core.errors import ApiError, ApiErrorCode
from app.domain.schemas import CalendarResponse, SessionType
from app.services import calendar_service
from app.services.calendar_service import _EPOCH
from tests.helpers import build_client

_NOW = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
_OLDER = datetime(2024, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
_NEWER = datetime(2024, 1, 20, 12, 0, 0, tzinfo=timezone.utc)


def _make_user(user_id: int = 1) -> dict:
    return {
        "id": user_id,
        "username": "test_user",
        "is_rating_enabled": True,
        "session_type": SessionType.AUTHENTICATED,
        "account_status": "active",
    }


def _override_user(client, user: dict):
    client.app.dependency_overrides[get_current_user] = lambda: user


def _clear_overrides(client):
    client.app.dependency_overrides.clear()


_SAMPLE_DAYS = {"2024-1-15": 0, "2024-1-16": 4, "2024-1-17": 1}


def test_save_calendar_success():
    client = build_client()
    _override_user(client, _make_user())
    try:
        with mock.patch.object(
            calendar_service,
            "save_calendar",
            return_value=CalendarResponse(days=_SAMPLE_DAYS, updated_at=_NOW),
        ) as m:
            response = client.put("/me/calendar", json={"days": _SAMPLE_DAYS})
        assert response.status_code == 200
        body = response.json()
        assert body["days"] == _SAMPLE_DAYS
        assert "updatedAt" in body
        m.assert_called_once_with(1, _SAMPLE_DAYS, None)
    finally:
        _clear_overrides(client)


def test_save_calendar_with_client_updated_at():
    client = build_client()
    _override_user(client, _make_user())
    try:
        with mock.patch.object(
            calendar_service,
            "save_calendar",
            return_value=CalendarResponse(days=_SAMPLE_DAYS, updated_at=_NOW),
        ) as m:
            response = client.put(
                "/me/calendar",
                json={"days": _SAMPLE_DAYS, "clientUpdatedAt": _NOW.isoformat()},
            )
        assert response.status_code == 200
        m.assert_called_once_with(1, _SAMPLE_DAYS, _NOW)
    finally:
        _clear_overrides(client)


def test_save_calendar_conflict():
    client = build_client()
    _override_user(client, _make_user())
    try:
        with mock.patch.object(
            calendar_service,
            "save_calendar",
            side_effect=ApiError(
                status_code=409,
                code=ApiErrorCode.CALENDAR_CONFLICT,
                message="Данные календаря были обновлены другим устройством",
            ),
        ):
            response = client.put(
                "/me/calendar",
                json={"days": _SAMPLE_DAYS, "clientUpdatedAt": _OLDER.isoformat()},
            )
        assert response.status_code == 409
        assert response.json()["code"] == "CALENDAR_CONFLICT"
    finally:
        _clear_overrides(client)


def test_save_calendar_requires_auth():
    client = build_client()
    response = client.put("/me/calendar", json={"days": {}})
    assert response.status_code == 401


def test_save_calendar_too_large():
    client = build_client()
    _override_user(client, _make_user())
    try:
        with mock.patch.object(
            calendar_service,
            "save_calendar",
            side_effect=ApiError(
                status_code=413,
                code=ApiErrorCode.CALENDAR_TOO_LARGE,
                message="Calendar data is too large",
            ),
        ):
            response = client.put("/me/calendar", json={"days": _SAMPLE_DAYS})
        assert response.status_code == 413
        assert response.json()["code"] == "CALENDAR_TOO_LARGE"
    finally:
        _clear_overrides(client)


def test_get_calendar_success():
    client = build_client()
    _override_user(client, _make_user())
    try:
        with mock.patch.object(
            calendar_service,
            "get_calendar",
            return_value=CalendarResponse(days=_SAMPLE_DAYS, updated_at=_NOW),
        ) as m:
            response = client.get("/me/calendar")
        assert response.status_code == 200
        body = response.json()
        assert body["days"] == _SAMPLE_DAYS
        assert "updatedAt" in body
        m.assert_called_once_with(1)
    finally:
        _clear_overrides(client)


def test_get_calendar_empty():
    client = build_client()
    _override_user(client, _make_user())
    try:
        with mock.patch.object(
            calendar_service,
            "get_calendar",
            return_value=CalendarResponse(days={}, updated_at=_NOW),
        ):
            response = client.get("/me/calendar")
        assert response.status_code == 200
        body = response.json()
        assert body["days"] == {}
        assert "updatedAt" in body
    finally:
        _clear_overrides(client)


def test_get_calendar_requires_auth():
    client = build_client()
    response = client.get("/me/calendar")
    assert response.status_code == 401


def test_save_empty_calendar():
    client = build_client()
    _override_user(client, _make_user())
    try:
        with mock.patch.object(
            calendar_service,
            "save_calendar",
            return_value=CalendarResponse(days={}, updated_at=_NOW),
        ) as m:
            response = client.put("/me/calendar", json={"days": {}})
        assert response.status_code == 200
        body = response.json()
        assert body["days"] == {}
        assert "updatedAt" in body
        m.assert_called_once_with(1, {}, None)
    finally:
        _clear_overrides(client)


def _mock_db_cursor(mock_conn, cursor):
    cur_ctx = mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__
    cur_ctx.return_value = cursor


def test_get_calendar_returns_epoch_when_no_data_saved():
    row = {"calendar_data": None, "calendar_updated_at": None, "updated_at": _NOW}
    with mock.patch("app.services.calendar_service.get_connection") as mock_conn:
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = row
        _mock_db_cursor(mock_conn, mock_cursor)
        result = calendar_service.get_calendar(1)
    assert result.days == {}
    assert result.updated_at == _EPOCH


def test_get_calendar_uses_calendar_updated_at():
    row = {"calendar_data": {"2024-1-15": 0}, "calendar_updated_at": _NOW, "updated_at": _NEWER}
    with mock.patch("app.services.calendar_service.get_connection") as mock_conn:
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = row
        _mock_db_cursor(mock_conn, mock_cursor)
        result = calendar_service.get_calendar(1)
    assert result.updated_at == _NOW


def test_get_calendar_falls_back_to_updated_at_for_legacy_data():
    row = {"calendar_data": {"2024-1-15": 0}, "calendar_updated_at": None, "updated_at": _NOW}
    with mock.patch("app.services.calendar_service.get_connection") as mock_conn:
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = row
        _mock_db_cursor(mock_conn, mock_cursor)
        result = calendar_service.get_calendar(1)
    assert result.updated_at == _NOW


def test_save_calendar_conflict_rejected_when_server_is_newer():
    _NOW_SERVER = _NEWER
    _CLIENT_UPDATED_AT = _OLDER
    with mock.patch("app.services.calendar_service.get_connection") as mock_conn:
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = {"calendar_updated_at": _NOW_SERVER}
        _mock_db_cursor(mock_conn, mock_cursor)
        try:
            calendar_service.save_calendar(1, {}, _CLIENT_UPDATED_AT)
            raise AssertionError("Expected CALENDAR_CONFLICT")
        except ApiError as e:
            assert e.code == ApiErrorCode.CALENDAR_CONFLICT
            assert e.status_code == 409


def test_save_calendar_no_conflict_when_client_is_newer():
    with mock.patch("app.services.calendar_service.get_connection") as mock_conn:
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"calendar_updated_at": _OLDER},
            {"calendar_data": {}, "calendar_updated_at": _NOW},
        ]
        _mock_db_cursor(mock_conn, mock_cursor)
        result = calendar_service.save_calendar(1, {}, _NOW)
    assert result.updated_at == _NOW


def test_get_friend_calendar_via_route():
    client = build_client()
    _override_user(client, _make_user(user_id=1))
    try:
        with mock.patch.object(
            calendar_service,
            "get_friend_calendar",
            return_value=CalendarResponse(days=_SAMPLE_DAYS, updated_at=_NOW),
        ) as m:
            response = client.get("/api/v1/users/2/calendar")
        assert response.status_code == 200
        assert response.json()["days"] == _SAMPLE_DAYS
        m.assert_called_once_with(1, 2)
    finally:
        _clear_overrides(client)


def test_get_friend_calendar_requires_auth():
    client = build_client()
    response = client.get("/api/v1/users/2/calendar")
    assert response.status_code == 401


def test_get_friend_calendar_not_friends():
    client = build_client()
    _override_user(client, _make_user(user_id=1))
    try:
        with mock.patch.object(
            calendar_service,
            "get_friend_calendar",
            side_effect=ApiError(
                status_code=403,
                code=ApiErrorCode.NOT_FRIENDS,
                message="Календарь доступен только друзьям",
            ),
        ):
            response = client.get("/api/v1/users/2/calendar")
        assert response.status_code == 403
        assert response.json()["code"] == "NOT_FRIENDS"
    finally:
        _clear_overrides(client)


def test_get_friend_calendar_service_mutual():
    row = {
        "calendar_data": {"2024-1-15": 1},
        "calendar_updated_at": _NOW,
        "updated_at": _NEWER,
        "is_mutual": True,
    }
    with mock.patch("app.services.calendar_service.get_connection") as mock_conn:
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = row
        _mock_db_cursor(mock_conn, mock_cursor)
        result = calendar_service.get_friend_calendar(1, 2)
    assert result.days == {"2024-1-15": 1}
    assert result.updated_at == _NOW


def test_get_friend_calendar_service_not_mutual():
    row = {
        "calendar_data": {"2024-1-15": 1},
        "calendar_updated_at": _NOW,
        "updated_at": _NEWER,
        "is_mutual": False,
    }
    with mock.patch("app.services.calendar_service.get_connection") as mock_conn:
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = row
        _mock_db_cursor(mock_conn, mock_cursor)
        try:
            calendar_service.get_friend_calendar(1, 2)
            raise AssertionError("Expected NOT_FRIENDS")
        except ApiError as e:
            assert e.code == ApiErrorCode.NOT_FRIENDS
            assert e.status_code == 403


def test_get_friend_calendar_self_delegates_to_get_calendar():
    with mock.patch.object(
        calendar_service,
        "get_calendar",
        return_value=CalendarResponse(days=_SAMPLE_DAYS, updated_at=_NOW),
    ) as m:
        result = calendar_service.get_friend_calendar(1, 1)
    m.assert_called_once_with(1)
    assert result.days == _SAMPLE_DAYS
