from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.dependencies import get_current_user
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

    def fake_save_profile(user_id: int, username: str | None, participate_in_rating: bool):
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
        json={"participate_in_rating": False},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json()["participate_in_rating"] is False


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
