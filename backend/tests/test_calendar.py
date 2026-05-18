from __future__ import annotations

from unittest import mock

from app.api.dependencies import get_current_user
from app.core.errors import ApiError, ApiErrorCode
from app.domain.schemas import CalendarResponse, SessionType
from app.services import calendar_service
from tests.helpers import build_client


def _make_user(user_id: int = 1) -> dict:
    return {
        "id": user_id,
        "user_id": user_id,
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
            return_value=CalendarResponse(days=_SAMPLE_DAYS),
        ) as m:
            response = client.put("/me/calendar", json={"days": _SAMPLE_DAYS})
        assert response.status_code == 200
        assert response.json() == {"days": _SAMPLE_DAYS}
        m.assert_called_once_with(1, _SAMPLE_DAYS)
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
            return_value=CalendarResponse(days=_SAMPLE_DAYS),
        ) as m:
            response = client.get("/me/calendar")
        assert response.status_code == 200
        assert response.json() == {"days": _SAMPLE_DAYS}
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
            return_value=CalendarResponse(days={}),
        ):
            response = client.get("/me/calendar")
        assert response.status_code == 200
        assert response.json() == {"days": {}}
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
            return_value=CalendarResponse(days={}),
        ) as m:
            response = client.put("/me/calendar", json={"days": {}})
        assert response.status_code == 200
        assert response.json() == {"days": {}}
        m.assert_called_once_with(1, {})
    finally:
        _clear_overrides(client)
