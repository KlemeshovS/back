from __future__ import annotations

from app.api.dependencies import get_current_admin
from app.services import admin_service
from tests.helpers import build_client


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
        lambda user_id, payload, current_admin: {
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


def test_admin_can_delete_managed_user(monkeypatch) -> None:
    client = build_client()
    client.app.dependency_overrides[get_current_admin] = lambda: {
        "id": 1,
        "login": "owner",
        "role": "owner",
        "is_active": True,
    }

    monkeypatch.setattr(
        admin_service,
        "delete_managed_user",
        lambda user_id, current_admin: None,
    )

    response = client.delete(
        "/admin/users/14",
        headers={"Authorization": "Bearer owner"},
    )

    assert response.status_code == 204
    assert response.text == ""


def test_owner_can_delete_admin_user(monkeypatch) -> None:
    client = build_client()
    client.app.dependency_overrides[get_current_admin] = lambda: {
        "id": 1,
        "login": "owner",
        "role": "owner",
        "is_active": True,
    }

    monkeypatch.setattr(
        admin_service,
        "delete_admin_user",
        lambda admin_id, current_admin: None,
    )

    response = client.delete(
        "/admin/admin-users/2",
        headers={"Authorization": "Bearer owner"},
    )

    assert response.status_code == 204
    assert response.text == ""


def test_admin_logout_returns_status(monkeypatch) -> None:
    client = build_client()
    client.app.dependency_overrides[get_current_admin] = lambda: {
        "id": 1,
        "login": "owner",
        "role": "owner",
        "is_active": True,
    }

    monkeypatch.setattr(
        admin_service,
        "logout_admin",
        lambda current_admin: {"status": "loggedOut"},
    )

    response = client.post("/admin/auth/logout", headers={"Authorization": "Bearer owner"})

    assert response.status_code == 200
    assert response.json() == {"status": "loggedOut"}


def test_admin_can_change_own_password(monkeypatch) -> None:
    client = build_client()
    client.app.dependency_overrides[get_current_admin] = lambda: {
        "id": 1,
        "login": "owner",
        "role": "owner",
        "is_active": True,
    }

    monkeypatch.setattr(
        admin_service,
        "change_admin_password",
        lambda payload, current_admin: {"status": "passwordUpdated"},
    )

    response = client.patch(
        "/admin/me/password",
        json={
            "currentPassword": "old_password_1",
            "newPassword": "new_password_2",
        },
        headers={"Authorization": "Bearer owner"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "passwordUpdated"}


def test_admin_audit_log_returns_items(monkeypatch) -> None:
    client = build_client()
    client.app.dependency_overrides[get_current_admin] = lambda: {
        "id": 1,
        "login": "owner",
        "role": "owner",
        "is_active": True,
    }

    monkeypatch.setattr(
        admin_service,
        "list_audit_logs",
        lambda limit, offset: {
            "items": [
                {
                    "id": 1,
                    "admin_id": 1,
                    "admin_login": "owner",
                    "action": "user.update",
                    "target_type": "user",
                    "target_id": 14,
                    "details": {"after": {"score": 10}},
                    "created_at": "2026-03-20T10:00:00Z",
                }
            ],
            "total": 1,
        },
    )

    response = client.get("/admin/audit-log", headers={"Authorization": "Bearer owner"})

    assert response.status_code == 200
    assert response.json()["items"][0]["adminLogin"] == "owner"
    assert response.json()["items"][0]["details"]["after"]["score"] == 10


def test_admin_overview_returns_summary(monkeypatch) -> None:
    client = build_client()
    client.app.dependency_overrides[get_current_admin] = lambda: {
        "id": 1,
        "login": "owner",
        "role": "owner",
        "is_active": True,
    }

    monkeypatch.setattr(
        admin_service,
        "get_admin_overview",
        lambda: {
            "total_users": 20,
            "rating_enabled_users": 3,
            "total_admins": 2,
            "active_admins": 1,
            "audit_log_entries": 14,
        },
    )

    response = client.get("/admin/overview", headers={"Authorization": "Bearer owner"})

    assert response.status_code == 200
    assert response.json()["totalUsers"] == 20
    assert response.json()["auditLogEntries"] == 14


def test_admin_host_serves_admin_page() -> None:
    client = build_client()

    response = client.get("/production/", headers={"host": "admin.wobbly.site"})

    assert response.status_code == 200
    assert '<div id="app"></div>' in response.text


def test_admin_host_serves_scoped_admin_asset() -> None:
    client = build_client()

    index_response = client.get("/staging/", headers={"host": "admin.wobbly.site"})
    assert index_response.status_code == 200
    start = index_response.text.find('/assets/')
    end = index_response.text.find('"', start)
    asset_path = index_response.text[start:end]
    response = client.get(asset_path, headers={"host": "admin.wobbly.site"})

    assert response.status_code == 200
    assert response.text
