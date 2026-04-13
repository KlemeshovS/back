from __future__ import annotations

from contextlib import contextmanager
from typing import Optional

from app.api.dependencies import get_current_user, get_current_user_session
from app.api.routes import health
from app.core.config import settings
from app.core.errors import ApiError, ApiErrorCode
from app.domain.schemas import ProfileResponse, UserScoreResponse
from app.services import session_service, social_auth_service, user_service
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
        "session_type": "authenticated",
        "provider": "google",
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
        lambda client_platform=None: {
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
        lambda client_platform=None: {
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


def test_auth_google_returns_camel_case_response(monkeypatch) -> None:
    client = build_client()

    monkeypatch.setattr(
        social_auth_service,
        "authenticate_google",
        lambda id_token, guest_access_token=None, client_platform=None: {
            "user_id": 11,
            "access_token": "rt_google",
            "refresh_token": "rf_google",
            "token_type": "bearer",
        },
    )

    response = client.post("/auth/google", json={"idToken": "google-id-token"})

    assert response.status_code == 200
    assert response.json() == {
        "userId": 11,
        "accessToken": "rt_google",
        "refreshToken": "rf_google",
        "tokenType": "bearer",
    }


def test_auth_google_is_available_under_api_v1(monkeypatch) -> None:
    client = build_client()

    monkeypatch.setattr(
        social_auth_service,
        "authenticate_google",
        lambda id_token, guest_access_token=None, client_platform=None: {
            "user_id": 12,
            "access_token": "rt_google_v1",
            "refresh_token": "rf_google_v1",
            "token_type": "bearer",
        },
    )

    response = client.post("/api/v1/auth/google", json={"idToken": "google-id-token"})

    assert response.status_code == 200
    assert response.json() == {
        "userId": 12,
        "accessToken": "rt_google_v1",
        "refreshToken": "rf_google_v1",
        "tokenType": "bearer",
    }


def test_auth_apple_returns_camel_case_response(monkeypatch) -> None:
    client = build_client()

    monkeypatch.setattr(
        social_auth_service,
        "authenticate_apple",
        lambda id_token, guest_access_token=None, client_platform=None: {
            "user_id": 13,
            "access_token": "rt_apple",
            "refresh_token": "rf_apple",
            "token_type": "bearer",
        },
    )

    response = client.post("/auth/apple", json={"idToken": "apple-id-token"})

    assert response.status_code == 200
    assert response.json() == {
        "userId": 13,
        "accessToken": "rt_apple",
        "refreshToken": "rf_apple",
        "tokenType": "bearer",
    }


def test_auth_apple_is_available_under_api_v1(monkeypatch) -> None:
    client = build_client()

    monkeypatch.setattr(
        social_auth_service,
        "authenticate_apple",
        lambda id_token, guest_access_token=None, client_platform=None: {
            "user_id": 14,
            "access_token": "rt_apple_v1",
            "refresh_token": "rf_apple_v1",
            "token_type": "bearer",
        },
    )

    response = client.post("/api/v1/auth/apple", json={"idToken": "apple-id-token"})

    assert response.status_code == 200
    assert response.json() == {
        "userId": 14,
        "accessToken": "rt_apple_v1",
        "refreshToken": "rf_apple_v1",
        "tokenType": "bearer",
    }


def test_auth_yandex_returns_camel_case_response(monkeypatch) -> None:
    client = build_client()

    monkeypatch.setattr(
        social_auth_service,
        "authenticate_yandex",
        lambda access_token, guest_access_token=None, client_platform=None: {
            "user_id": 15,
            "access_token": "rt_yandex",
            "refresh_token": "rf_yandex",
            "token_type": "bearer",
        },
    )

    response = client.post("/auth/yandex", json={"accessToken": "yandex-token"})

    assert response.status_code == 200
    assert response.json() == {
        "userId": 15,
        "accessToken": "rt_yandex",
        "refreshToken": "rf_yandex",
        "tokenType": "bearer",
    }


def test_auth_yandex_is_available_under_api_v1(monkeypatch) -> None:
    client = build_client()

    monkeypatch.setattr(
        social_auth_service,
        "authenticate_yandex",
        lambda access_token, guest_access_token=None, client_platform=None: {
            "user_id": 16,
            "access_token": "rt_yandex_v1",
            "refresh_token": "rf_yandex_v1",
            "token_type": "bearer",
        },
    )

    response = client.post("/api/v1/auth/yandex", json={"accessToken": "yandex-token"})

    assert response.status_code == 200
    assert response.json() == {
        "userId": 16,
        "accessToken": "rt_yandex_v1",
        "refreshToken": "rf_yandex_v1",
        "tokenType": "bearer",
    }


def test_auth_session_restore_returns_current_session(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user_session] = lambda: {
        "id": 21,
        "username": "restored_user",
        "is_rating_enabled": True,
        "session_type": "authenticated",
        "provider": "google",
        "avatar_path": None,
    }

    response = client.get("/auth/session", headers={"Authorization": "Bearer token"})

    assert response.status_code == 200
    assert response.json() == {
        "userId": 21,
        "username": "restored_user",
        "participateInRating": True,
        "sessionType": "authenticated",
        "provider": "google",
        "avatarUrl": None,
    }


def test_auth_refresh_returns_new_session_tokens(monkeypatch) -> None:
    client = build_client()

    monkeypatch.setattr(
        session_service,
        "refresh_authenticated_session",
        lambda refresh_token: {
            "user_id": 22,
            "access_token": "rt_refreshed",
            "refresh_token": "rf_refreshed",
            "token_type": "bearer",
        },
    )

    response = client.post("/auth/refresh", json={"refreshToken": "rf_old_token"})

    assert response.status_code == 200
    assert response.json() == {
        "userId": 22,
        "accessToken": "rt_refreshed",
        "refreshToken": "rf_refreshed",
        "tokenType": "bearer",
    }


def test_auth_logout_returns_status(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user_session] = lambda: {
        "id": 23,
        "username": "logout_user",
        "is_rating_enabled": False,
        "session_type": "authenticated",
        "provider": "google",
        "session_id": 55,
    }

    monkeypatch.setattr(
        session_service,
        "logout_session",
        lambda current_session: {"status": "loggedOut"},
    )

    response = client.post("/auth/logout", headers={"Authorization": "Bearer token"})

    assert response.status_code == 200
    assert response.json() == {"status": "loggedOut"}


def test_auth_provider_list_returns_linked_identities(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user_session] = lambda: {
        "id": 24,
        "username": "provider_user",
        "is_rating_enabled": False,
        "session_type": "authenticated",
        "provider": "google",
        "session_id": 56,
    }

    monkeypatch.setattr(
        social_auth_service,
        "list_linked_identities",
        lambda current_user: {
            "items": [
                {
                    "provider": "google",
                    "provider_email": "user@example.com",
                    "provider_email_verified": True,
                    "created_at": "2026-04-08T10:00:00Z",
                    "updated_at": "2026-04-08T10:00:00Z",
                }
            ]
        },
    )

    response = client.get("/auth/providers", headers={"Authorization": "Bearer token"})

    assert response.status_code == 200
    assert response.json()["items"][0]["provider"] == "google"


def test_auth_provider_google_link_returns_identities(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user_session] = lambda: {
        "id": 25,
        "username": "provider_user",
        "is_rating_enabled": False,
        "session_type": "authenticated",
        "provider": "google",
        "session_id": 57,
    }

    monkeypatch.setattr(
        social_auth_service,
        "link_google_identity",
        lambda current_user, id_token: {
            "items": [
                {
                    "provider": "apple",
                    "provider_email": "relay@privaterelay.appleid.com",
                    "provider_email_verified": True,
                    "created_at": "2026-04-08T10:00:00Z",
                    "updated_at": "2026-04-08T10:00:00Z",
                },
                {
                    "provider": "google",
                    "provider_email": "user@example.com",
                    "provider_email_verified": True,
                    "created_at": "2026-04-08T10:05:00Z",
                    "updated_at": "2026-04-08T10:05:00Z",
                },
            ]
        },
    )

    response = client.post(
        "/auth/providers/google/link",
        json={"idToken": "google-link-token"},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert [item["provider"] for item in response.json()["items"]] == ["apple", "google"]


def test_auth_provider_apple_link_returns_identities(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user_session] = lambda: {
        "id": 26,
        "username": "provider_user",
        "is_rating_enabled": False,
        "session_type": "authenticated",
        "provider": "google",
        "session_id": 58,
    }

    monkeypatch.setattr(
        social_auth_service,
        "link_apple_identity",
        lambda current_user, id_token: {
            "items": [
                {
                    "provider": "apple",
                    "provider_email": "relay@privaterelay.appleid.com",
                    "provider_email_verified": True,
                    "created_at": "2026-04-08T10:00:00Z",
                    "updated_at": "2026-04-08T10:00:00Z",
                }
            ]
        },
    )

    response = client.post(
        "/auth/providers/apple/link",
        json={"idToken": "apple-link-token"},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["provider"] == "apple"


def test_auth_provider_yandex_link_returns_identities(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user_session] = lambda: {
        "id": 27,
        "username": "provider_user",
        "is_rating_enabled": False,
        "session_type": "authenticated",
        "provider": "google",
        "session_id": 59,
    }

    monkeypatch.setattr(
        social_auth_service,
        "link_yandex_identity",
        lambda current_user, access_token: {
            "items": [
                {
                    "provider": "yandex",
                    "provider_email": "user@yandex.ru",
                    "provider_email_verified": True,
                    "created_at": "2026-04-08T10:00:00Z",
                    "updated_at": "2026-04-08T10:00:00Z",
                }
            ]
        },
    )

    response = client.post(
        "/auth/providers/yandex/link",
        json={"accessToken": "yandex-link-token"},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["provider"] == "yandex"


def test_auth_provider_unlink_returns_remaining_identities(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user_session] = lambda: {
        "id": 28,
        "username": "provider_user",
        "is_rating_enabled": False,
        "session_type": "authenticated",
        "provider": "google",
        "session_id": 60,
    }

    monkeypatch.setattr(
        social_auth_service,
        "unlink_identity",
        lambda current_user, provider: {
            "items": [
                {
                    "provider": "apple",
                    "provider_email": "relay@privaterelay.appleid.com",
                    "provider_email_verified": True,
                    "created_at": "2026-04-08T10:00:00Z",
                    "updated_at": "2026-04-08T10:00:00Z",
                }
            ]
        },
    )

    response = client.delete(
        "/auth/providers/google",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["provider"] == "apple"


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
        "session_type": "authenticated",
        "provider": "google",
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


def test_guest_cannot_update_profile_for_rating_features() -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user] = lambda: {
        "id": 7,
        "username": None,
        "is_rating_enabled": False,
        "session_type": "guest",
        "provider": None,
    }

    response = client.patch(
        "/me/profile",
        json={"username": "guest_name", "participateInRating": True},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "code": "AUTH_REQUIRED_FOR_USERNAME",
        "message": "Authentication is required to save username",
    }


def test_guest_cannot_toggle_rating() -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user] = lambda: {
        "id": 7,
        "username": None,
        "is_rating_enabled": False,
        "session_type": "guest",
        "provider": None,
    }

    response = client.patch(
        "/me/rating",
        json={"participateInRating": True},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "code": "GUEST_CANNOT_ENABLE_RATING",
        "message": "Guest users cannot enable rating participation",
    }


def test_guest_can_update_profile_when_guest_rating_is_enabled(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user] = lambda: {
        "id": 7,
        "username": None,
        "is_rating_enabled": False,
        "session_type": "guest",
        "provider": None,
    }
    monkeypatch.setattr(settings, "allow_guest_rating", True)

    monkeypatch.setattr(
        user_service,
        "save_profile",
        lambda user_id, username, participate_in_rating: ProfileResponse(
            id=user_id,
            username=username,
            participate_in_rating=participate_in_rating,
        ),
    )

    response = client.patch(
        "/me/profile",
        json={"username": "guest_name", "participateInRating": True},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 7,
        "username": "guest_name",
        "participateInRating": True,
        "avatarUrl": None,
    }


def test_top_leaderboard_returns_service_payload(monkeypatch) -> None:
    client = build_client()

    monkeypatch.setattr(
        user_service,
        "fetch_leaderboard",
        lambda order, score_filter, limit: {
            "items": [{"username": "good_user", "score": 12, "avatar_url": None}],
            "total": 1,
        },
    )

    response = client.get("/leaderboard/top?limit=100")

    assert response.status_code == 200
    assert response.json() == {
        "items": [{"username": "good_user", "score": 12, "avatarUrl": None}],
        "total": 1,
    }


def test_top_leaderboard_is_available_under_api_v1(monkeypatch) -> None:
    client = build_client()

    monkeypatch.setattr(
        user_service,
        "fetch_leaderboard",
        lambda order, score_filter, limit: {
            "items": [{"username": "good_v1", "score": 20, "avatar_url": None}],
            "total": 1,
        },
    )

    response = client.get("/api/v1/leaderboard/top?limit=100")

    assert response.status_code == 200
    assert response.json() == {
        "items": [{"username": "good_v1", "score": 20, "avatarUrl": None}],
        "total": 1,
    }


def test_score_update_rejects_users_without_username(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user] = lambda: {
        "id": 7,
        "username": None,
        "is_rating_enabled": False,
        "session_type": "authenticated",
        "provider": "google",
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


def test_guest_cannot_update_score() -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user] = lambda: {
        "id": 7,
        "username": None,
        "is_rating_enabled": False,
        "session_type": "guest",
        "provider": None,
    }

    response = client.post(
        "/me/score",
        json={"score": 10},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "code": "AUTH_REQUIRED_FOR_RATING",
        "message": "Authentication is required for rating features",
    }


def test_guest_can_update_score_when_guest_rating_is_enabled(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user] = lambda: {
        "id": 7,
        "username": "guest_name",
        "is_rating_enabled": True,
        "session_type": "guest",
        "provider": None,
    }
    monkeypatch.setattr(settings, "allow_guest_rating", True)
    monkeypatch.setattr(
        user_service,
        "update_my_score",
        lambda user_id, score: UserScoreResponse(username="guest_name", score=score),
    )

    response = client.post(
        "/me/score",
        json={"score": 10},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json() == {"username": "guest_name", "score": 10, "avatarUrl": None}


def test_upload_avatar_returns_profile(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user] = lambda: {
        "id": 7,
        "username": "player_7",
        "is_rating_enabled": True,
        "session_type": "authenticated",
        "provider": "google",
    }

    monkeypatch.setattr(
        user_service,
        "save_my_avatar",
        lambda user_id, payload, content_type: ProfileResponse(
            id=user_id,
            username="player_7",
            participate_in_rating=True,
            avatar_url="/media/avatars/user-7.jpg",
        ),
    )

    response = client.post(
        "/me/avatar",
        headers={"Authorization": "Bearer token"},
        files={"file": ("avatar.jpg", b"\xff\xd8\xffavatar", "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 7,
        "username": "player_7",
        "participateInRating": True,
        "avatarUrl": "/media/avatars/user-7.jpg",
    }


def test_delete_avatar_returns_profile(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user] = lambda: {
        "id": 7,
        "username": "player_7",
        "is_rating_enabled": True,
        "session_type": "authenticated",
        "provider": "google",
    }

    monkeypatch.setattr(
        user_service,
        "delete_my_avatar",
        lambda user_id: ProfileResponse(
            id=user_id,
            username="player_7",
            participate_in_rating=True,
            avatar_url=None,
        ),
    )

    response = client.delete(
        "/me/avatar",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 7,
        "username": "player_7",
        "participateInRating": True,
        "avatarUrl": None,
    }


def test_score_update_rejects_users_with_rating_disabled(monkeypatch) -> None:
    client = build_client()

    client.app.dependency_overrides[get_current_user] = lambda: {
        "id": 7,
        "username": "player_7",
        "is_rating_enabled": False,
        "session_type": "authenticated",
        "provider": "google",
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
