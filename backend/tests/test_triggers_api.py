from __future__ import annotations

from datetime import datetime, timezone
from unittest import mock

from app.api.dependencies import get_current_user
from app.core.errors import ApiError, ApiErrorCode
from app.domain.schemas import SessionType, TriggersResponse
from app.services import trigger_service
from app.services.trigger_service import _EPOCH
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


_SAMPLE_TRIGGERS = {"2024-1-15": ["stress", "conflict"], "2024-1-16": ["habit"]}


def test_save_triggers_success():
    client = build_client()
    _override_user(client, _make_user())
    try:
        with mock.patch.object(
            trigger_service,
            "save_triggers",
            return_value=TriggersResponse(triggers=_SAMPLE_TRIGGERS, updated_at=_NOW),
        ) as m:
            response = client.put("/me/calendar/triggers", json={"triggers": _SAMPLE_TRIGGERS})
        assert response.status_code == 200
        body = response.json()
        assert body["triggers"] == _SAMPLE_TRIGGERS
        assert "updatedAt" in body
        m.assert_called_once_with(1, _SAMPLE_TRIGGERS, None)
    finally:
        _clear_overrides(client)


def test_save_triggers_with_client_updated_at():
    client = build_client()
    _override_user(client, _make_user())
    try:
        with mock.patch.object(
            trigger_service,
            "save_triggers",
            return_value=TriggersResponse(triggers=_SAMPLE_TRIGGERS, updated_at=_NOW),
        ) as m:
            response = client.put(
                "/me/calendar/triggers",
                json={"triggers": _SAMPLE_TRIGGERS, "clientUpdatedAt": _NOW.isoformat()},
            )
        assert response.status_code == 200
        m.assert_called_once_with(1, _SAMPLE_TRIGGERS, _NOW)
    finally:
        _clear_overrides(client)


def test_save_triggers_rejects_unknown_tag():
    client = build_client()
    _override_user(client, _make_user())
    try:
        response = client.put(
            "/me/calendar/triggers",
            json={"triggers": {"2024-1-15": ["stress", "not_a_real_trigger"]}},
        )
        assert response.status_code == 422
    finally:
        _clear_overrides(client)


def test_save_triggers_conflict():
    client = build_client()
    _override_user(client, _make_user())
    try:
        with mock.patch.object(
            trigger_service,
            "save_triggers",
            side_effect=ApiError(
                status_code=409,
                code=ApiErrorCode.TRIGGERS_CONFLICT,
                message="Данные триггеров были обновлены другим устройством",
            ),
        ):
            response = client.put(
                "/me/calendar/triggers",
                json={"triggers": _SAMPLE_TRIGGERS, "clientUpdatedAt": _OLDER.isoformat()},
            )
        assert response.status_code == 409
        assert response.json()["code"] == "TRIGGERS_CONFLICT"
    finally:
        _clear_overrides(client)


def test_save_triggers_requires_auth():
    client = build_client()
    response = client.put("/me/calendar/triggers", json={"triggers": {}})
    assert response.status_code == 401


def test_save_triggers_too_large():
    client = build_client()
    _override_user(client, _make_user())
    try:
        with mock.patch.object(
            trigger_service,
            "save_triggers",
            side_effect=ApiError(
                status_code=413,
                code=ApiErrorCode.TRIGGERS_TOO_LARGE,
                message="Triggers data is too large",
            ),
        ):
            response = client.put("/me/calendar/triggers", json={"triggers": _SAMPLE_TRIGGERS})
        assert response.status_code == 413
        assert response.json()["code"] == "TRIGGERS_TOO_LARGE"
    finally:
        _clear_overrides(client)


def test_get_triggers_success():
    client = build_client()
    _override_user(client, _make_user())
    try:
        with mock.patch.object(
            trigger_service,
            "get_triggers",
            return_value=TriggersResponse(triggers=_SAMPLE_TRIGGERS, updated_at=_NOW),
        ) as m:
            response = client.get("/me/calendar/triggers")
        assert response.status_code == 200
        body = response.json()
        assert body["triggers"] == _SAMPLE_TRIGGERS
        assert "updatedAt" in body
        m.assert_called_once_with(1)
    finally:
        _clear_overrides(client)


def test_get_triggers_empty():
    client = build_client()
    _override_user(client, _make_user())
    try:
        with mock.patch.object(
            trigger_service,
            "get_triggers",
            return_value=TriggersResponse(triggers={}, updated_at=_NOW),
        ):
            response = client.get("/me/calendar/triggers")
        assert response.status_code == 200
        body = response.json()
        assert body["triggers"] == {}
        assert "updatedAt" in body
    finally:
        _clear_overrides(client)


def test_get_triggers_requires_auth():
    client = build_client()
    response = client.get("/me/calendar/triggers")
    assert response.status_code == 401


def test_save_empty_triggers():
    client = build_client()
    _override_user(client, _make_user())
    try:
        with mock.patch.object(
            trigger_service,
            "save_triggers",
            return_value=TriggersResponse(triggers={}, updated_at=_NOW),
        ) as m:
            response = client.put("/me/calendar/triggers", json={"triggers": {}})
        assert response.status_code == 200
        body = response.json()
        assert body["triggers"] == {}
        m.assert_called_once_with(1, {}, None)
    finally:
        _clear_overrides(client)


def _mock_db_cursor(mock_conn, cursor):
    cur_ctx = mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__
    cur_ctx.return_value = cursor


def test_get_triggers_returns_epoch_when_no_data_saved():
    row = {"triggers_data": None, "triggers_updated_at": None, "updated_at": _NOW}
    with mock.patch("app.services.trigger_service.get_connection") as mock_conn:
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = row
        _mock_db_cursor(mock_conn, mock_cursor)
        result = trigger_service.get_triggers(1)
    assert result.triggers == {}
    assert result.updated_at == _EPOCH


def test_get_triggers_uses_triggers_updated_at():
    row = {
        "triggers_data": {"2024-1-15": ["stress"]},
        "triggers_updated_at": _NOW,
        "updated_at": _NEWER,
    }
    with mock.patch("app.services.trigger_service.get_connection") as mock_conn:
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = row
        _mock_db_cursor(mock_conn, mock_cursor)
        result = trigger_service.get_triggers(1)
    assert result.updated_at == _NOW


def test_get_triggers_falls_back_to_updated_at_for_legacy_data():
    row = {
        "triggers_data": {"2024-1-15": ["stress"]},
        "triggers_updated_at": None,
        "updated_at": _NOW,
    }
    with mock.patch("app.services.trigger_service.get_connection") as mock_conn:
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = row
        _mock_db_cursor(mock_conn, mock_cursor)
        result = trigger_service.get_triggers(1)
    assert result.updated_at == _NOW


def test_save_triggers_conflict_rejected_when_server_is_newer():
    with mock.patch("app.services.trigger_service.get_connection") as mock_conn:
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = {"triggers_updated_at": _NEWER}
        _mock_db_cursor(mock_conn, mock_cursor)
        try:
            trigger_service.save_triggers(1, {}, _OLDER)
            raise AssertionError("Expected TRIGGERS_CONFLICT")
        except ApiError as e:
            assert e.code == ApiErrorCode.TRIGGERS_CONFLICT
            assert e.status_code == 409


def test_save_triggers_no_conflict_when_client_is_newer():
    with mock.patch("app.services.trigger_service.get_connection") as mock_conn:
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"triggers_updated_at": _OLDER},
            {"triggers_data": {}, "triggers_updated_at": _NOW},
        ]
        _mock_db_cursor(mock_conn, mock_cursor)
        result = trigger_service.save_triggers(1, {}, _NOW)
    assert result.updated_at == _NOW
