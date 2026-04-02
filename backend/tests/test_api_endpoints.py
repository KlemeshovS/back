from __future__ import annotations

from contextlib import contextmanager
from typing import Optional

from app.api.dependencies import get_current_user
from app.api.routes import health
from app.core.errors import ApiError, ApiErrorCode
from app.services import user_service
from tests.helpers import build_client


def test_healthcheck_returns_ok() -> None:
    client = build_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_returns_ok_when_database_is_available(monkeypatch) -> None:
    client = build_client()

    @contextmanager
    def fake_connection():
        class FakeCursor:
            def execute(self, query: str) -> None:
                assert query == "SELECT 1"

            def fetchone(self):
                return (1,)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

        class FakeConnection:
            def cursor(self) -> FakeCursor:
                return FakeCursor()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

        yield FakeConnection()

    monkeypatch.setattr(health, "get_connection", fake_connection)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_returns_503_when_database_is_unavailable(monkeypatch) -> None:
    client = build_client()

    @contextmanager
    def broken_connection():
        raise RuntimeError("db down")
        yield

    monkeypatch.setattr(health, "get_connection", broken_connection)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "code": "HTTP_ERROR",
        "message": "Service not ready",
    }


def test_patch_me_rating_updates_participation(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user] = lambda: {
        "id": 7,
        "username": "player_7",
        "is_rating_enabled": True,
    }

    def fake_save_profile(
        user_id: int,
        username: Optional[str],
        participate_in_rating: bool,
    ):
        assert user_id == 7
        assert username == "player_7"
        assert participate_in_rating is False
        return {
            "id": 7,
            "username": "player_7",
            "participate_in_rating": False,
        }

    monkeypatch.setattr(user_service, "save_profile", fake_save_profile)

    response = client.patch(
        "/me/rating",
        json={"participateInRating": False},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json()["participateInRating"] is False


def test_auth_anonymous_returns_camel_case_response(monkeypatch) -> None:
    client = build_client()

    monkeypatch.setattr(
        user_service,
        "create_anonymous_user",
        lambda: {
            "user_id": 9,
            "access_token": "rt_test",
            "token_type": "bearer",
        },
    )

    response = client.post("/auth/anonymous")

    assert response.status_code == 201
    assert response.json() == {
        "userId": 9,
        "accessToken": "rt_test",
        "tokenType": "bearer",
    }


def test_auth_anonymous_is_available_under_api_v1(monkeypatch) -> None:
    client = build_client()

    monkeypatch.setattr(
        user_service,
        "create_anonymous_user",
        lambda: {
            "user_id": 10,
            "access_token": "rt_v1",
            "token_type": "bearer",
        },
    )

    response = client.post("/api/v1/auth/anonymous")

    assert response.status_code == 201
    assert response.json() == {
        "userId": 10,
        "accessToken": "rt_v1",
        "tokenType": "bearer",
    }


def test_get_me_requires_authorization_header() -> None:
    client = build_client()

    response = client.get("/me")

    assert response.status_code == 401
    assert response.json() == {
        "code": "MISSING_AUTHORIZATION_HEADER",
        "message": "Missing authorization header",
    }


def test_profile_validation_error_uses_uniform_error_contract() -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user] = lambda: {
        "id": 7,
        "username": "player_7",
        "is_rating_enabled": True,
    }

    response = client.patch(
        "/me/profile",
        json={},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request payload",
    }


def test_top_leaderboard_returns_service_payload(monkeypatch) -> None:
    client = build_client()

    monkeypatch.setattr(
        user_service,
        "fetch_leaderboard",
        lambda order, score_filter, limit: {
            "items": [{"username": "good_user", "score": 12}],
            "total": 1,
        },
    )

    response = client.get("/leaderboard/top?limit=100")

    assert response.status_code == 200
    assert response.json() == {
        "items": [{"username": "good_user", "score": 12}],
        "total": 1,
    }


def test_top_leaderboard_is_available_under_api_v1(monkeypatch) -> None:
    client = build_client()

    monkeypatch.setattr(
        user_service,
        "fetch_leaderboard",
        lambda order, score_filter, limit: {
            "items": [{"username": "good_v1", "score": 20}],
            "total": 1,
        },
    )

    response = client.get("/api/v1/leaderboard/top?limit=100")

    assert response.status_code == 200
    assert response.json() == {
        "items": [{"username": "good_v1", "score": 20}],
        "total": 1,
    }


def test_score_update_rejects_users_without_username(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user] = lambda: {
        "id": 7,
        "username": None,
        "is_rating_enabled": False,
    }

    def fake_update_my_score(user_id: int, score: int):
        raise ApiError(
            status_code=422,
            code=ApiErrorCode.USERNAME_REQUIRED_FOR_RATING,
            message="Username is required to submit score",
        )

    monkeypatch.setattr(user_service, "update_my_score", fake_update_my_score)

    response = client.post(
        "/me/score",
        json={"score": 10},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "code": "USERNAME_REQUIRED_FOR_RATING",
        "message": "Username is required to submit score",
    }


def test_score_update_rejects_users_with_rating_disabled(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user] = lambda: {
        "id": 7,
        "username": "player_7",
        "is_rating_enabled": False,
    }

    def fake_update_my_score(user_id: int, score: int):
        raise ApiError(
            status_code=422,
            code=ApiErrorCode.RATING_DISABLED_FOR_SCORE,
            message="Rating must be enabled to submit score",
        )

    monkeypatch.setattr(user_service, "update_my_score", fake_update_my_score)

    response = client.post(
        "/me/score",
        json={"score": 10},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "code": "RATING_DISABLED_FOR_SCORE",
        "message": "Rating must be enabled to submit score",
    }
