from __future__ import annotations

from datetime import datetime, timezone
from unittest import mock

from app.api.dependencies import get_current_user
from app.core.errors import ApiError, ApiErrorCode
from app.domain.schemas import BetListResponse, BetParticipant, BetResponse, SessionType
from app.services import bets_service
from tests.helpers import build_client

_NOW = datetime(2026, 8, 18, 12, 0, 0, tzinfo=timezone.utc)


def _make_user(user_id: int = 1, session_type: SessionType = SessionType.AUTHENTICATED) -> dict:
    return {
        "id": user_id,
        "username": f"user{user_id}",
        "is_rating_enabled": True,
        "session_type": session_type,
        "account_status": "active",
    }


def _override_user(client, user: dict):
    client.app.dependency_overrides[get_current_user] = lambda: user


def _clear_overrides(client):
    client.app.dependency_overrides.clear()


def _sample_bet(bet_id: int = 1, status: str = "pending") -> BetResponse:
    return BetResponse(
        id=bet_id,
        challenger=BetParticipant(user_id=1, username="user1", avatar_url=None),
        opponent=BetParticipant(user_id=2, username="user2", avatar_url=None),
        bet_type="sobriety",
        duration_mode="period",
        duration_days=14,
        target_end_date=None,
        status=status,
        resolution_type=None,
        winner_id=None,
        forfeited_by=None,
        respond_by=_NOW,
        start_at=None,
        end_at=None,
        result_snapshot=None,
        created_at=_NOW,
        accepted_at=None,
        resolved_at=None,
    )


def test_create_bet_success():
    client = build_client()
    _override_user(client, _make_user(1))
    try:
        with mock.patch.object(bets_service, "create_bet", return_value=_sample_bet()) as m:
            response = client.post(
                "/api/v1/me/bets",
                json={
                    "opponentUserId": 2,
                    "betType": "sobriety",
                    "durationMode": "period",
                    "durationDays": 14,
                },
            )
        assert response.status_code == 201
        body = response.json()
        assert body["betType"] == "sobriety"
        assert body["status"] == "pending"
        m.assert_called_once_with(1, 2, "sobriety", "period", 14, None)
    finally:
        _clear_overrides(client)


def test_create_bet_requires_auth():
    client = build_client()
    _override_user(client, _make_user(1, SessionType.GUEST))
    try:
        response = client.post(
            "/api/v1/me/bets",
            json={
                "opponentUserId": 2,
                "betType": "sobriety",
                "durationMode": "period",
                "durationDays": 14,
            },
        )
        assert response.status_code == 403
        assert response.json()["code"] == ApiErrorCode.AUTH_REQUIRED_FOR_RATING
    finally:
        _clear_overrides(client)


def test_create_bet_rejects_unknown_bet_type():
    client = build_client()
    _override_user(client, _make_user(1))
    try:
        response = client.post(
            "/api/v1/me/bets",
            json={
                "opponentUserId": 2,
                "betType": "roulette",
                "durationMode": "period",
                "durationDays": 14,
            },
        )
        assert response.status_code == 422
    finally:
        _clear_overrides(client)


def test_create_bet_period_mode_requires_duration_days():
    client = build_client()
    _override_user(client, _make_user(1))
    try:
        response = client.post(
            "/api/v1/me/bets",
            json={"opponentUserId": 2, "betType": "sport", "durationMode": "period"},
        )
        assert response.status_code == 422
    finally:
        _clear_overrides(client)


def test_create_bet_fixed_date_mode_requires_target_end_date():
    client = build_client()
    _override_user(client, _make_user(1))
    try:
        response = client.post(
            "/api/v1/me/bets",
            json={"opponentUserId": 2, "betType": "sport", "durationMode": "fixed_date"},
        )
        assert response.status_code == 422
    finally:
        _clear_overrides(client)


def test_create_bet_not_mutual_friend_returns_403():
    client = build_client()
    _override_user(client, _make_user(1))
    try:
        with mock.patch.object(
            bets_service,
            "create_bet",
            side_effect=ApiError(
                status_code=403,
                code=ApiErrorCode.BET_NOT_MUTUAL_FRIEND,
                message="Бросить вызов можно только взаимному другу",
            ),
        ):
            response = client.post(
                "/api/v1/me/bets",
                json={
                    "opponentUserId": 2,
                    "betType": "sobriety",
                    "durationMode": "period",
                    "durationDays": 7,
                },
            )
        assert response.status_code == 403
        assert response.json()["code"] == "BET_NOT_MUTUAL_FRIEND"
    finally:
        _clear_overrides(client)


def test_get_bets_returns_list():
    client = build_client()
    _override_user(client, _make_user(1))
    try:
        listing = BetListResponse(items=[_sample_bet(1), _sample_bet(2, status="active")], total=2)
        with mock.patch.object(bets_service, "get_bets", return_value=listing) as m:
            response = client.get("/api/v1/me/bets")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2
        m.assert_called_once_with(1)
    finally:
        _clear_overrides(client)


def test_get_bet_not_found_returns_404():
    client = build_client()
    _override_user(client, _make_user(1))
    try:
        with mock.patch.object(
            bets_service,
            "get_bet",
            side_effect=ApiError(
                status_code=404, code=ApiErrorCode.BET_NOT_FOUND, message="Пари не найдено"
            ),
        ):
            response = client.get("/api/v1/me/bets/999")
        assert response.status_code == 404
        assert response.json()["code"] == "BET_NOT_FOUND"
    finally:
        _clear_overrides(client)


def test_accept_bet_success():
    client = build_client()
    _override_user(client, _make_user(2))
    try:
        with mock.patch.object(
            bets_service, "accept_bet", return_value=_sample_bet(1, status="active")
        ) as m:
            response = client.post("/api/v1/me/bets/1/accept")
        assert response.status_code == 200
        assert response.json()["status"] == "active"
        m.assert_called_once_with(2, 1)
    finally:
        _clear_overrides(client)


def test_accept_bet_wrong_state_returns_409():
    client = build_client()
    _override_user(client, _make_user(2))
    try:
        with mock.patch.object(
            bets_service,
            "accept_bet",
            side_effect=ApiError(
                status_code=409,
                code=ApiErrorCode.BET_INVALID_STATE,
                message="Пари уже не ожидает принятия",
            ),
        ):
            response = client.post("/api/v1/me/bets/1/accept")
        assert response.status_code == 409
        assert response.json()["code"] == "BET_INVALID_STATE"
    finally:
        _clear_overrides(client)


def test_decline_bet_success():
    client = build_client()
    _override_user(client, _make_user(2))
    try:
        with mock.patch.object(
            bets_service,
            "decline_bet",
            return_value=_sample_bet(1, status="resolved"),
        ) as m:
            response = client.post("/api/v1/me/bets/1/decline")
        assert response.status_code == 200
        m.assert_called_once_with(2, 1)
    finally:
        _clear_overrides(client)


def test_cancel_bet_success():
    client = build_client()
    _override_user(client, _make_user(1))
    try:
        with mock.patch.object(
            bets_service,
            "cancel_bet",
            return_value=_sample_bet(1, status="resolved"),
        ) as m:
            response = client.post("/api/v1/me/bets/1/cancel")
        assert response.status_code == 200
        m.assert_called_once_with(1, 1)
    finally:
        _clear_overrides(client)


def test_forfeit_bet_forbidden_for_non_participant():
    client = build_client()
    _override_user(client, _make_user(3))
    try:
        with mock.patch.object(
            bets_service,
            "forfeit_bet",
            side_effect=ApiError(
                status_code=403,
                code=ApiErrorCode.BET_FORBIDDEN,
                message="Это пари вам недоступно",
            ),
        ):
            response = client.post("/api/v1/me/bets/1/forfeit")
        assert response.status_code == 403
        assert response.json()["code"] == "BET_FORBIDDEN"
    finally:
        _clear_overrides(client)
