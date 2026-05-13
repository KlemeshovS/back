from __future__ import annotations

from datetime import datetime, timezone

from app.api.dependencies import get_current_user
from app.core.errors import ApiErrorCode
from app.domain.schemas import SessionType
from app.services import follows_service
from tests.helpers import build_client

_NOW = datetime(2026, 5, 13, 0, 0, 0, tzinfo=timezone.utc)


def _make_user(user_id: int, session_type: SessionType = SessionType.AUTHENTICATED) -> dict:
    return {
        "id": user_id,
        "username": f"user{user_id}",
        "is_rating_enabled": True,
        "session_type": session_type,
        "account_status": "active",
    }


def _make_follow(user_id: int, is_mutual: bool = False):
    from app.domain.schemas import FollowResponse

    return FollowResponse(
        user_id=user_id,
        username=f"user{user_id}",
        avatar_url=None,
        is_mutual=is_mutual,
        created_at=_NOW,
    )


def _override_user(client, user: dict):
    client.app.dependency_overrides[get_current_user] = lambda: user


def _clear_overrides(client):
    client.app.dependency_overrides.clear()


# --- follow ---


def test_follow_user_success(monkeypatch):
    client = build_client()
    _override_user(client, _make_user(1))

    expected = _make_follow(2, is_mutual=False)
    monkeypatch.setattr(follows_service, "follow_user", lambda uid, username: expected)

    response = client.post("/api/v1/follows", json={"username": "user2"})

    assert response.status_code == 201
    data = response.json()
    assert data["userId"] == 2
    assert data["isMutual"] is False

    _clear_overrides(client)


def test_follow_requires_auth(monkeypatch):
    client = build_client()
    _override_user(client, _make_user(1, SessionType.GUEST))

    response = client.post("/api/v1/follows", json={"username": "user2"})

    assert response.status_code == 403
    assert response.json()["code"] == ApiErrorCode.AUTH_REQUIRED_FOR_RATING

    _clear_overrides(client)


def test_follow_self_returns_422(monkeypatch):
    from app.core.errors import ApiError

    client = build_client()
    _override_user(client, _make_user(1))

    monkeypatch.setattr(
        follows_service,
        "follow_user",
        lambda uid, username: (_ for _ in ()).throw(
            ApiError(
                status_code=422,
                code=ApiErrorCode.CANNOT_FOLLOW_SELF,
                message="Нельзя подписаться на себя",
            )
        ),
    )

    response = client.post("/api/v1/follows", json={"username": "user1"})

    assert response.status_code == 422
    assert response.json()["code"] == ApiErrorCode.CANNOT_FOLLOW_SELF

    _clear_overrides(client)


def test_follow_already_following_returns_409(monkeypatch):
    from app.core.errors import ApiError

    client = build_client()
    _override_user(client, _make_user(1))

    monkeypatch.setattr(
        follows_service,
        "follow_user",
        lambda uid, username: (_ for _ in ()).throw(
            ApiError(
                status_code=409,
                code=ApiErrorCode.ALREADY_FOLLOWING,
                message="Уже подписан",
            )
        ),
    )

    response = client.post("/api/v1/follows", json={"username": "user2"})

    assert response.status_code == 409
    assert response.json()["code"] == ApiErrorCode.ALREADY_FOLLOWING

    _clear_overrides(client)


# --- unfollow ---


def test_unfollow_success(monkeypatch):
    client = build_client()
    _override_user(client, _make_user(1))

    monkeypatch.setattr(follows_service, "unfollow_user", lambda uid, tid: None)

    response = client.delete("/api/v1/follows/2")

    assert response.status_code == 204

    _clear_overrides(client)


def test_unfollow_not_following_returns_404(monkeypatch):
    from app.core.errors import ApiError

    client = build_client()
    _override_user(client, _make_user(1))

    monkeypatch.setattr(
        follows_service,
        "unfollow_user",
        lambda uid, tid: (_ for _ in ()).throw(
            ApiError(
                status_code=404,
                code=ApiErrorCode.NOT_FOLLOWING,
                message="Не подписан",
            )
        ),
    )

    response = client.delete("/api/v1/follows/99")

    assert response.status_code == 404
    assert response.json()["code"] == ApiErrorCode.NOT_FOLLOWING

    _clear_overrides(client)


# --- get follows ---


def test_get_follows_returns_list(monkeypatch):
    from app.domain.schemas import FollowListResponse

    client = build_client()
    _override_user(client, _make_user(1))

    monkeypatch.setattr(
        follows_service,
        "get_follows",
        lambda uid: FollowListResponse(items=[_make_follow(2, is_mutual=True)], total=1),
    )

    response = client.get("/api/v1/follows")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["isMutual"] is True

    _clear_overrides(client)


# --- get followers ---


def test_get_followers_returns_list(monkeypatch):
    from app.domain.schemas import FollowListResponse

    client = build_client()
    _override_user(client, _make_user(1))

    monkeypatch.setattr(
        follows_service,
        "get_followers",
        lambda uid: FollowListResponse(items=[_make_follow(3, is_mutual=False)], total=1),
    )

    response = client.get("/api/v1/follows/followers")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["isMutual"] is False

    _clear_overrides(client)


# --- get friends (mutual) ---


def test_get_friends_returns_mutual(monkeypatch):
    from app.domain.schemas import FollowListResponse

    client = build_client()
    _override_user(client, _make_user(1))

    monkeypatch.setattr(
        follows_service,
        "get_mutual_follows",
        lambda uid: FollowListResponse(items=[_make_follow(2, is_mutual=True)], total=1),
    )

    response = client.get("/api/v1/follows/friends")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["isMutual"] is True

    _clear_overrides(client)
