from __future__ import annotations

from typing import Optional

from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.dependencies import get_current_user
from app.core.errors import ApiError, ApiErrorCode
from app.services import user_service


def build_client() -> TestClient:
    app = create_app(init_database=False)
    return TestClient(app)


def test_healthcheck_returns_ok() -> None:
    client = build_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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


def test_legacy_register_duplicate_username_returns_uniform_error(monkeypatch) -> None:
    client = build_client()

    def fake_register_user(_: str) -> dict:
        raise ApiError(
            status_code=409,
            code=ApiErrorCode.USERNAME_ALREADY_EXISTS,
            message="Username already exists",
        )

    monkeypatch.setattr(user_service, "register_user", fake_register_user)

    response = client.post("/users/register", json={"username": "player_3"})

    assert response.status_code == 409
    assert response.json() == {
        "code": "USERNAME_ALREADY_EXISTS",
        "message": "Username already exists",
    }


def test_legacy_register_returns_created(monkeypatch) -> None:
    client = build_client()

    monkeypatch.setattr(
        user_service,
        "register_user",
        lambda username: {"status": "created", "id": 3, "username": username},
    )

    response = client.post("/users/register", json={"username": "player_3"})

    assert response.status_code == 201
    assert response.json() == {"status": "created", "id": 3, "username": "player_3"}


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
