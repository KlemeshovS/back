from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.dependencies import get_current_admin
from app.services import admin_service


def build_client() -> TestClient:
    app = create_app(init_database=False)
    return TestClient(app)


def test_admin_login_returns_camel_case_response(monkeypatch) -> None:
    client = build_client()

    monkeypatch.setattr(
        admin_service,
        "authenticate_admin",
        lambda payload: {
            "access_token": "adm_test",
            "token_type": "bearer",
            "role": "owner",
        },
    )

    response = client.post(
        "/admin/auth/login",
        json={"login": "owner", "password": "supersecret"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "accessToken": "adm_test",
        "tokenType": "bearer",
        "role": "owner",
    }


def test_admin_users_endpoint_requires_owner() -> None:
    client = build_client()
    client.app.dependency_overrides[get_current_admin] = lambda: {
        "id": 1,
        "login": "admin",
        "role": "admin",
        "is_active": True,
    }

    response = client.get("/admin/admin-users", headers={"Authorization": "Bearer admin"})

    assert response.status_code == 403
    assert response.json() == {
        "code": "FORBIDDEN",
        "message": "Not enough permissions",
    }


def test_admin_can_patch_managed_user(monkeypatch) -> None:
    client = build_client()
    client.app.dependency_overrides[get_current_admin] = lambda: {
        "id": 1,
        "login": "owner",
        "role": "owner",
        "is_active": True,
    }

    monkeypatch.setattr(
        admin_service,
        "update_managed_user",
        lambda user_id, payload: {
            "id": user_id,
            "username": payload.username,
            "score": payload.score,
            "participate_in_rating": payload.participate_in_rating,
            "created_at": "2026-03-19T12:00:00Z",
            "updated_at": "2026-03-19T12:30:00Z",
            "last_seen_at": "2026-03-19T12:30:00Z",
        },
    )

    response = client.patch(
        "/admin/users/14",
        json={
            "username": "edited_user",
            "score": 777,
            "participateInRating": True,
        },
        headers={"Authorization": "Bearer owner"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "edited_user"
    assert response.json()["participateInRating"] is True


def test_admin_host_serves_admin_page() -> None:
    client = build_client()

    response = client.get("/production/", headers={"host": "admin.wobbly.site"})

    assert response.status_code == 200
    assert "Wobbly Admin" in response.text
