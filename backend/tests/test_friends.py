from __future__ import annotations

from datetime import datetime, timezone

from app.api.dependencies import get_current_user
from app.core.errors import ApiErrorCode
from app.domain.schemas import SessionType
from app.services import friends_service
from tests.helpers import build_client

_NOW = datetime(2026, 5, 12, 0, 0, 0, tzinfo=timezone.utc)


def _make_user(user_id: int, session_type: SessionType = SessionType.AUTHENTICATED) -> dict:
    return {
        "id": user_id,
        "username": f"user{user_id}",
        "is_rating_enabled": True,
        "session_type": session_type,
        "account_status": "active",
    }


def _make_friendship(
    friendship_id: int,
    requester_id: int,
    addressee_id: int,
    status: str = "pending",
    is_requester: bool = True,
):
    from app.domain.schemas import FriendResponse, FriendshipStatus

    other_id = addressee_id if is_requester else requester_id
    return FriendResponse(
        user_id=other_id,
        username=f"user{other_id}",
        avatar_url=None,
        friendship_id=friendship_id,
        status=FriendshipStatus(status),
        is_requester=is_requester,
        created_at=_NOW,
    )


def _override_user(client, user: dict):
    client.app.dependency_overrides[get_current_user] = lambda: user


def _clear_overrides(client):
    client.app.dependency_overrides.clear()


# --- send friend request ---


def test_send_friend_request_success(monkeypatch):
    client = build_client()
    user = _make_user(1)
    _override_user(client, user)

    expected = _make_friendship(10, requester_id=1, addressee_id=2, status="pending")
    monkeypatch.setattr(friends_service, "send_friend_request", lambda uid, username: expected)

    response = client.post("/api/v1/friends", json={"username": "user2"})

    assert response.status_code == 201
    data = response.json()
    assert data["friendshipId"] == 10
    assert data["status"] == "pending"
    assert data["isRequester"] is True

    _clear_overrides(client)


def test_send_friend_request_requires_auth(monkeypatch):
    client = build_client()
    _override_user(client, _make_user(1, SessionType.GUEST))

    response = client.post("/api/v1/friends", json={"username": "user2"})

    assert response.status_code == 403
    assert response.json()["code"] == ApiErrorCode.AUTH_REQUIRED_FOR_RATING

    _clear_overrides(client)


def test_send_friend_request_cannot_add_self(monkeypatch):
    from app.core.errors import ApiError

    client = build_client()
    _override_user(client, _make_user(1))

    monkeypatch.setattr(
        friends_service,
        "send_friend_request",
        lambda uid, username: (_ for _ in ()).throw(
            ApiError(status_code=422, code=ApiErrorCode.CANNOT_ADD_SELF, message="Cannot add self")
        ),
    )

    response = client.post("/api/v1/friends", json={"username": "user1"})

    assert response.status_code == 422
    assert response.json()["code"] == ApiErrorCode.CANNOT_ADD_SELF

    _clear_overrides(client)


def test_send_friend_request_already_friends(monkeypatch):
    from app.core.errors import ApiError

    client = build_client()
    _override_user(client, _make_user(1))

    monkeypatch.setattr(
        friends_service,
        "send_friend_request",
        lambda uid, username: (_ for _ in ()).throw(
            ApiError(status_code=409, code=ApiErrorCode.ALREADY_FRIENDS, message="Already friends")
        ),
    )

    response = client.post("/api/v1/friends", json={"username": "user2"})

    assert response.status_code == 409
    assert response.json()["code"] == ApiErrorCode.ALREADY_FRIENDS

    _clear_overrides(client)


# --- get friends ---


def test_get_friends_returns_accepted(monkeypatch):
    from app.domain.schemas import FriendListResponse

    client = build_client()
    _override_user(client, _make_user(1))

    friend = _make_friendship(10, requester_id=1, addressee_id=2, status="accepted")
    monkeypatch.setattr(
        friends_service,
        "get_friends",
        lambda uid, status_filter=None: FriendListResponse(items=[friend], total=1),
    )

    response = client.get("/api/v1/friends")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "accepted"

    _clear_overrides(client)


def test_get_friend_requests_returns_pending(monkeypatch):
    from app.domain.schemas import FriendListResponse

    client = build_client()
    _override_user(client, _make_user(1))

    req = _make_friendship(11, requester_id=2, addressee_id=1, status="pending", is_requester=False)
    monkeypatch.setattr(
        friends_service,
        "get_friends",
        lambda uid, status_filter=None: FriendListResponse(items=[req], total=1),
    )

    response = client.get("/api/v1/friends/requests")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "pending"

    _clear_overrides(client)


# --- respond to request ---


def test_accept_friend_request(monkeypatch):
    client = build_client()
    _override_user(client, _make_user(2))

    accepted = _make_friendship(
        10, requester_id=1, addressee_id=2, status="accepted", is_requester=False
    )
    monkeypatch.setattr(
        friends_service,
        "respond_to_friend_request",
        lambda uid, fid, action: accepted,
    )

    response = client.patch("/api/v1/friends/10", json={"action": "accept"})

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"

    _clear_overrides(client)


def test_decline_friend_request(monkeypatch):
    client = build_client()
    _override_user(client, _make_user(2))

    declined = _make_friendship(
        10, requester_id=1, addressee_id=2, status="declined", is_requester=False
    )
    monkeypatch.setattr(
        friends_service,
        "respond_to_friend_request",
        lambda uid, fid, action: declined,
    )

    response = client.patch("/api/v1/friends/10", json={"action": "decline"})

    assert response.status_code == 200
    assert response.json()["status"] == "declined"

    _clear_overrides(client)


def test_respond_invalid_action(monkeypatch):
    client = build_client()
    _override_user(client, _make_user(2))

    response = client.patch("/api/v1/friends/10", json={"action": "remove"})

    assert response.status_code == 422

    _clear_overrides(client)


# --- remove friend ---


def test_remove_friend_success(monkeypatch):
    client = build_client()
    _override_user(client, _make_user(1))

    monkeypatch.setattr(friends_service, "remove_friend", lambda uid, fid: None)

    response = client.delete("/api/v1/friends/10")

    assert response.status_code == 204

    _clear_overrides(client)


def test_remove_friend_not_found(monkeypatch):
    from app.core.errors import ApiError

    client = build_client()
    _override_user(client, _make_user(1))

    monkeypatch.setattr(
        friends_service,
        "remove_friend",
        lambda uid, fid: (_ for _ in ()).throw(
            ApiError(status_code=404, code=ApiErrorCode.NOT_FRIENDS, message="Not found")
        ),
    )

    response = client.delete("/api/v1/friends/99")

    assert response.status_code == 404
    assert response.json()["code"] == ApiErrorCode.NOT_FRIENDS

    _clear_overrides(client)
