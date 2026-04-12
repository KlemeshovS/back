from __future__ import annotations

from pathlib import Path

import pytest
from psycopg import connect

from app.core.apple_auth import AppleIdentity
from app.core.auth import hash_access_token
from app.core.config import settings
from app.core.google_auth import GoogleIdentity
from app.core.yandex_auth import YandexIdentity

pytestmark = pytest.mark.integration_db


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def create_anonymous_user(client) -> dict:
    response = client.post("/auth/anonymous")

    assert response.status_code == 201
    return response.json()


def create_authenticated_user(client, monkeypatch, subject: str = "auth-user") -> dict:
    from app.services import social_auth_service

    monkeypatch.setattr(
        social_auth_service,
        "verify_google_id_token",
        lambda token: GoogleIdentity(
            subject=subject,
            email=f"{subject}@example.com",
            email_verified=True,
            payload={"iss": "https://accounts.google.com", "aud": "mobile-client"},
        ),
    )

    response = client.post("/auth/google", json={"idToken": f"{subject}-google-token"})

    assert response.status_code == 200
    return response.json()


def seed_guest_profile_state(
    integration_database_url: str,
    *,
    user_id: int,
    username: str,
    score: int,
    participate_in_rating: bool,
) -> None:
    with connect(integration_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET username = %s,
                    score = %s,
                    is_rating_enabled = %s,
                    updated_at = NOW(),
                    last_seen_at = NOW()
                WHERE id = %s;
                """,
                (username, score, participate_in_rating, user_id),
            )
        conn.commit()


def test_anonymous_users_do_not_appear_in_admin_user_list(db_client) -> None:
    from app.services import admin_service

    create_anonymous_user(db_client)
    create_anonymous_user(db_client)

    response = admin_service.list_managed_users(search=None, limit=50, offset=0)

    assert response.total == 0
    assert response.items == []


def test_authenticated_user_exposes_account_status_and_identity_providers_in_admin_views(
    db_client,
    integration_database_url,
    monkeypatch,
) -> None:
    from app.services import admin_service

    auth_payload = create_authenticated_user(
        db_client,
        monkeypatch,
        subject="admin-visible-user",
    )
    seed_guest_profile_state(
        integration_database_url,
        user_id=auth_payload["userId"],
        username="admin_visible_user",
        score=12,
        participate_in_rating=True,
    )

    list_response = admin_service.list_managed_users(search=None, limit=50, offset=0)

    matching = next(item for item in list_response.items if item.id == auth_payload["userId"])
    assert matching.account_status == "active"
    assert matching.identity_providers == ["google"]

    detail_response = admin_service.get_managed_user(auth_payload["userId"])
    assert detail_response.account_status == "active"
    assert detail_response.identity_providers == ["google"]


def test_anonymous_auth_flow_works_against_real_database(db_client) -> None:
    auth_payload = create_anonymous_user(db_client)

    response = db_client.get("/me", headers=auth_headers(auth_payload["accessToken"]))

    assert response.status_code == 200
    assert response.json() == {
        "id": auth_payload["userId"],
        "username": None,
        "participateInRating": False,
        "avatarUrl": None,
    }


def test_api_v1_anonymous_auth_flow_works_against_real_database(db_client) -> None:
    response = db_client.post("/api/v1/auth/anonymous")

    assert response.status_code == 201
    auth_payload = response.json()

    me_response = db_client.get(
        "/api/v1/me",
        headers=auth_headers(auth_payload["accessToken"]),
    )

    assert me_response.status_code == 200
    assert me_response.json() == {
        "id": auth_payload["userId"],
        "username": None,
        "participateInRating": False,
        "avatarUrl": None,
    }


def test_anonymous_auth_backfills_internal_username_in_database(
    db_client,
    integration_database_url,
) -> None:
    auth_payload = create_anonymous_user(db_client)

    with connect(integration_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT username, is_rating_enabled FROM users WHERE id = %s;",
                (auth_payload["userId"],),
            )
            row = cur.fetchone()

    assert row[0].startswith("anon_user_")
    assert row[1] is False


def test_anonymous_auth_creates_guest_session_and_migration_key(
    db_client,
    integration_database_url,
) -> None:
    auth_payload = create_anonymous_user(db_client)
    token_hash = hash_access_token(auth_payload["accessToken"])

    with connect(integration_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT account_status, guest_migration_key
                FROM users
                WHERE id = %s;
                """,
                (auth_payload["userId"],),
            )
            user_row = cur.fetchone()
            cur.execute(
                """
                SELECT session_type, access_token_hash, provider
                FROM user_sessions
                WHERE user_id = %s;
                """,
                (auth_payload["userId"],),
            )
            session_row = cur.fetchone()

    assert user_row == ("guest", token_hash)
    assert session_row == ("guest", token_hash, None)


def test_profile_update_persists_to_real_database(db_client, monkeypatch) -> None:
    auth_payload = create_authenticated_user(db_client, monkeypatch, "profile-db-user")

    update_response = db_client.patch(
        "/me/profile",
        json={"username": "db_player", "participateInRating": True},
        headers=auth_headers(auth_payload["accessToken"]),
    )

    assert update_response.status_code == 200
    assert update_response.json() == {
        "id": auth_payload["userId"],
        "username": "db_player",
        "participateInRating": True,
        "avatarUrl": None,
    }

    me_response = db_client.get("/me", headers=auth_headers(auth_payload["accessToken"]))

    assert me_response.status_code == 200
    assert me_response.json()["username"] == "db_player"
    assert me_response.json()["participateInRating"] is True


def test_guest_cannot_create_username_or_enable_rating(db_client) -> None:
    auth_payload = create_anonymous_user(db_client)

    profile_response = db_client.patch(
        "/me/profile",
        json={"username": "guest_player", "participateInRating": True},
        headers=auth_headers(auth_payload["accessToken"]),
    )
    rating_response = db_client.patch(
        "/me/rating",
        json={"participateInRating": True},
        headers=auth_headers(auth_payload["accessToken"]),
    )

    assert profile_response.status_code == 403
    assert profile_response.json() == {
        "code": "AUTH_REQUIRED_FOR_USERNAME",
        "message": "Authentication is required to save username",
    }
    assert rating_response.status_code == 403
    assert rating_response.json() == {
        "code": "GUEST_CANNOT_ENABLE_RATING",
        "message": "Guest users cannot enable rating participation",
    }


def test_guest_can_use_rating_features_when_guest_rating_is_enabled(
    db_client,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "allow_guest_rating", True)
    auth_payload = create_anonymous_user(db_client)

    profile_response = db_client.patch(
        "/me/profile",
        json={"username": "guest_player", "participateInRating": True},
        headers=auth_headers(auth_payload["accessToken"]),
    )
    score_response = db_client.post(
        "/me/score",
        json={"score": 42},
        headers=auth_headers(auth_payload["accessToken"]),
    )

    assert profile_response.status_code == 200
    assert profile_response.json() == {
        "id": auth_payload["userId"],
        "username": "guest_player",
        "participateInRating": True,
        "avatarUrl": None,
    }
    assert score_response.status_code == 200
    assert score_response.json() == {"username": "guest_player", "score": 42, "avatarUrl": None}


def test_rating_toggle_updates_real_database_state(db_client, monkeypatch) -> None:
    auth_payload = create_authenticated_user(db_client, monkeypatch, "toggle-db-user")

    db_client.patch(
        "/me/profile",
        json={"username": "toggle_user", "participateInRating": True},
        headers=auth_headers(auth_payload["accessToken"]),
    )

    disable_response = db_client.patch(
        "/me/rating",
        json={"participateInRating": False},
        headers=auth_headers(auth_payload["accessToken"]),
    )

    assert disable_response.status_code == 200
    assert disable_response.json()["participateInRating"] is False

    enable_response = db_client.patch(
        "/me/rating",
        json={"participateInRating": True},
        headers=auth_headers(auth_payload["accessToken"]),
    )

    assert enable_response.status_code == 200
    assert enable_response.json()["participateInRating"] is True


def test_score_update_persists_to_real_database(db_client, monkeypatch) -> None:
    auth_payload = create_authenticated_user(db_client, monkeypatch, "score-db-user")

    db_client.patch(
        "/me/profile",
        json={"username": "score_user", "participateInRating": True},
        headers=auth_headers(auth_payload["accessToken"]),
    )

    response = db_client.post(
        "/me/score",
        json={"score": 42},
        headers=auth_headers(auth_payload["accessToken"]),
    )

    assert response.status_code == 200
    assert response.json() == {"username": "score_user", "score": 42, "avatarUrl": None}


def test_score_update_rejects_anonymous_users_without_username(db_client) -> None:
    auth_payload = create_anonymous_user(db_client)

    response = db_client.post(
        "/me/score",
        json={"score": 42},
        headers=auth_headers(auth_payload["accessToken"]),
    )

    assert response.status_code == 403
    assert response.json() == {
        "code": "AUTH_REQUIRED_FOR_RATING",
        "message": "Authentication is required for rating features",
    }


def test_score_update_rejects_users_with_rating_disabled(db_client, monkeypatch) -> None:
    auth_payload = create_authenticated_user(db_client, monkeypatch, "disabled-db-user")

    db_client.patch(
        "/me/profile",
        json={"username": "disabled_user", "participateInRating": True},
        headers=auth_headers(auth_payload["accessToken"]),
    )
    db_client.patch(
        "/me/rating",
        json={"participateInRating": False},
        headers=auth_headers(auth_payload["accessToken"]),
    )

    response = db_client.post(
        "/me/score",
        json={"score": 42},
        headers=auth_headers(auth_payload["accessToken"]),
    )

    assert response.status_code == 422
    assert response.json() == {
        "code": "RATING_DISABLED_FOR_SCORE",
        "message": "Rating must be enabled to submit score",
    }


def test_clearing_existing_username_is_rejected_and_score_is_preserved(
    db_client,
    monkeypatch,
) -> None:
    auth_payload = create_authenticated_user(db_client, monkeypatch, "clear-db-user")

    db_client.patch(
        "/me/profile",
        json={"username": "clear_user", "participateInRating": True},
        headers=auth_headers(auth_payload["accessToken"]),
    )
    db_client.post(
        "/me/score",
        json={"score": 42},
        headers=auth_headers(auth_payload["accessToken"]),
    )

    response = db_client.patch(
        "/me/profile",
        json={"username": "   ", "participateInRating": False},
        headers=auth_headers(auth_payload["accessToken"]),
    )

    assert response.status_code == 422
    assert response.json() == {
        "code": "USERNAME_CANNOT_BE_CLEARED",
        "message": "Username cannot be cleared once set",
    }

    score_response = db_client.post(
        "/me/score",
        json={"score": 84},
        headers=auth_headers(auth_payload["accessToken"]),
    )
    assert score_response.status_code == 200
    assert score_response.json() == {"username": "clear_user", "score": 84, "avatarUrl": None}

    me_response = db_client.get("/me", headers=auth_headers(auth_payload["accessToken"]))
    assert me_response.status_code == 200
    assert me_response.json() == {
        "id": auth_payload["userId"],
        "username": "clear_user",
        "participateInRating": True,
        "avatarUrl": None,
    }


def test_leaderboard_queries_use_real_database_data(db_client, monkeypatch) -> None:
    alpha = create_authenticated_user(db_client, monkeypatch, "leader-alpha")
    beta = create_authenticated_user(db_client, monkeypatch, "leader-beta")
    gamma = create_authenticated_user(db_client, monkeypatch, "leader-gamma")

    db_client.patch(
        "/me/profile",
        json={"username": "alpha", "participateInRating": True},
        headers=auth_headers(alpha["accessToken"]),
    )
    db_client.patch(
        "/me/profile",
        json={"username": "beta", "participateInRating": True},
        headers=auth_headers(beta["accessToken"]),
    )
    db_client.patch(
        "/me/profile",
        json={"username": "gamma", "participateInRating": True},
        headers=auth_headers(gamma["accessToken"]),
    )

    db_client.post(
        "/me/score",
        json={"score": 15},
        headers=auth_headers(alpha["accessToken"]),
    )
    db_client.post(
        "/me/score",
        json={"score": 8},
        headers=auth_headers(beta["accessToken"]),
    )
    db_client.post(
        "/me/score",
        json={"score": -4},
        headers=auth_headers(gamma["accessToken"]),
    )

    top_response = db_client.get("/leaderboard/top?limit=2")
    bottom_response = db_client.get("/leaderboard/bottom?limit=2")

    assert top_response.status_code == 200
    assert top_response.json() == {
        "items": [
            {"username": "alpha", "score": 15, "avatarUrl": None},
            {"username": "beta", "score": 8, "avatarUrl": None},
        ],
        "total": 2,
    }

    assert bottom_response.status_code == 200
    assert bottom_response.json() == {
        "items": [
            {"username": "gamma", "score": -4, "avatarUrl": None},
        ],
        "total": 1,
    }


def test_api_v1_leaderboard_queries_use_real_database_data(db_client, monkeypatch) -> None:
    alpha = create_authenticated_user(db_client, monkeypatch, "v1-alpha")
    beta = create_authenticated_user(db_client, monkeypatch, "v1-beta")

    db_client.patch(
        "/api/v1/me/profile",
        json={"username": "v1_alpha", "participateInRating": True},
        headers=auth_headers(alpha["accessToken"]),
    )
    db_client.patch(
        "/api/v1/me/profile",
        json={"username": "v1_beta", "participateInRating": True},
        headers=auth_headers(beta["accessToken"]),
    )

    db_client.post(
        "/api/v1/me/score",
        json={"score": 30},
        headers=auth_headers(alpha["accessToken"]),
    )
    db_client.post(
        "/api/v1/me/score",
        json={"score": 10},
        headers=auth_headers(beta["accessToken"]),
    )

    top_response = db_client.get("/api/v1/leaderboard/top?limit=2")

    assert top_response.status_code == 200
    assert top_response.json() == {
        "items": [
            {"username": "v1_alpha", "score": 30, "avatarUrl": None},
            {"username": "v1_beta", "score": 10, "avatarUrl": None},
        ],
        "total": 2,
    }


def test_leaderboard_excludes_users_inactive_for_more_than_30_days(
    db_client,
    integration_database_url,
    monkeypatch,
) -> None:
    recent = create_authenticated_user(db_client, monkeypatch, "leader-recent")
    stale = create_authenticated_user(db_client, monkeypatch, "leader-stale")

    db_client.patch(
        "/me/profile",
        json={"username": "recent_user", "participateInRating": True},
        headers=auth_headers(recent["accessToken"]),
    )
    db_client.patch(
        "/me/profile",
        json={"username": "stale_user", "participateInRating": True},
        headers=auth_headers(stale["accessToken"]),
    )

    db_client.post(
        "/me/score",
        json={"score": 25},
        headers=auth_headers(recent["accessToken"]),
    )
    db_client.post(
        "/me/score",
        json={"score": 99},
        headers=auth_headers(stale["accessToken"]),
    )

    with connect(integration_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET last_seen_at = NOW() - INTERVAL '31 days'
                WHERE id = %s;
                """,
                (stale["userId"],),
            )
        conn.commit()

    top_response = db_client.get("/leaderboard/top?limit=10")

    assert top_response.status_code == 200
    assert top_response.json() == {
        "items": [
            {"username": "recent_user", "score": 25, "avatarUrl": None},
        ],
        "total": 1,
    }


def test_avatar_upload_and_leaderboard_return_avatar_url(
    db_client,
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(settings, "media_root", str(tmp_path))
    monkeypatch.setattr(settings, "media_base_url", "")

    auth_payload = create_authenticated_user(db_client, monkeypatch, "avatar-user")

    profile_response = db_client.patch(
        "/me/profile",
        json={"username": "avatar_user", "participateInRating": True},
        headers=auth_headers(auth_payload["accessToken"]),
    )
    assert profile_response.status_code == 200

    upload_response = db_client.post(
        "/me/avatar",
        headers=auth_headers(auth_payload["accessToken"]),
        files={"file": ("avatar.jpg", b"\xff\xd8\xffavatar-binary", "image/jpeg")},
    )
    assert upload_response.status_code == 200
    avatar_url = upload_response.json()["avatarUrl"]
    assert avatar_url is not None
    assert avatar_url.startswith("/media/avatars/user-")

    me_response = db_client.get("/me", headers=auth_headers(auth_payload["accessToken"]))
    assert me_response.status_code == 200
    assert me_response.json()["avatarUrl"] == avatar_url

    score_response = db_client.post(
        "/me/score",
        json={"score": 18},
        headers=auth_headers(auth_payload["accessToken"]),
    )
    assert score_response.status_code == 200
    assert score_response.json()["avatarUrl"] == avatar_url

    top_response = db_client.get("/leaderboard/top?limit=5")
    assert top_response.status_code == 200
    assert top_response.json()["items"][0]["avatarUrl"] == avatar_url

    relative_path = avatar_url.removeprefix("/media/")
    assert (Path(tmp_path) / relative_path).exists()


def test_avatar_delete_clears_profile_avatar(db_client, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "media_root", str(tmp_path))
    monkeypatch.setattr(settings, "media_base_url", "")

    auth_payload = create_authenticated_user(db_client, monkeypatch, "avatar-delete-user")
    upload_response = db_client.post(
        "/me/avatar",
        headers=auth_headers(auth_payload["accessToken"]),
        files={"file": ("avatar.png", b"\x89PNG\r\n\x1a\navatar", "image/png")},
    )
    assert upload_response.status_code == 200

    delete_response = db_client.delete(
        "/me/avatar",
        headers=auth_headers(auth_payload["accessToken"]),
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["avatarUrl"] is None


def test_real_database_flows_cover_constraint_and_validation_errors(db_client, monkeypatch) -> None:
    first_user = create_authenticated_user(db_client, monkeypatch, "duplicate-first")
    second_user = create_authenticated_user(db_client, monkeypatch, "duplicate-second")
    third_user = create_authenticated_user(db_client, monkeypatch, "duplicate-third")

    first_profile = db_client.patch(
        "/me/profile",
        json={"username": "duplicate_user", "participateInRating": True},
        headers=auth_headers(first_user["accessToken"]),
    )
    assert first_profile.status_code == 200

    duplicate_username = db_client.patch(
        "/me/profile",
        json={"username": "duplicate_user", "participateInRating": True},
        headers=auth_headers(second_user["accessToken"]),
    )

    assert duplicate_username.status_code == 409
    assert duplicate_username.json() == {
        "code": "USERNAME_ALREADY_EXISTS",
        "message": "Username already exists",
    }

    missing_username = db_client.patch(
        "/me/rating",
        json={"participateInRating": True},
        headers=auth_headers(third_user["accessToken"]),
    )

    assert missing_username.status_code == 422
    assert missing_username.json() == {
        "code": "USERNAME_REQUIRED_FOR_RATING",
        "message": "Username is required to participate in rating",
    }


def test_google_auth_creates_identity_and_authenticated_session(
    db_client,
    integration_database_url,
    monkeypatch,
) -> None:
    from app.services import social_auth_service

    monkeypatch.setattr(
        social_auth_service,
        "verify_google_id_token",
        lambda token: GoogleIdentity(
            subject="google-sub-1",
            email="user@example.com",
            email_verified=True,
            payload={"iss": "https://accounts.google.com", "aud": "mobile-client"},
        ),
    )

    response = db_client.post("/auth/google", json={"idToken": "google-token"})

    assert response.status_code == 200
    payload = response.json()

    with connect(integration_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, account_status, auth_token_hash
                FROM users
                WHERE id = %s;
                """,
                (payload["userId"],),
            )
            user_row = cur.fetchone()
            cur.execute(
                """
                SELECT provider, provider_user_id, provider_email, provider_email_verified
                FROM user_identities
                WHERE user_id = %s;
                """,
                (payload["userId"],),
            )
            identity_row = cur.fetchone()
            cur.execute(
                """
                SELECT session_type, provider, revoked_at IS NULL AS active
                FROM user_sessions
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT 1;
                """,
                (payload["userId"],),
            )
            session_row = cur.fetchone()

    assert user_row[1] == "active"
    assert identity_row == ("google", "google-sub-1", "user@example.com", True)
    assert session_row == ("authenticated", "google", True)


def test_google_auth_reuses_existing_internal_user(
    db_client,
    integration_database_url,
    monkeypatch,
) -> None:
    from app.services import social_auth_service

    monkeypatch.setattr(
        social_auth_service,
        "verify_google_id_token",
        lambda token: GoogleIdentity(
            subject="google-sub-2",
            email="same@example.com",
            email_verified=True,
            payload={"iss": "https://accounts.google.com", "aud": "mobile-client"},
        ),
    )

    first = db_client.post("/auth/google", json={"idToken": "google-token-first"})
    second = db_client.post("/auth/google", json={"idToken": "google-token-second"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["userId"] == second.json()["userId"]

    with connect(integration_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users;")
            users_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM user_identities WHERE provider = 'google';")
            identities_count = cur.fetchone()[0]

    assert users_count == 1
    assert identities_count == 1


def test_guest_google_auth_promotes_guest_user_without_losing_progress(
    db_client,
    integration_database_url,
    monkeypatch,
) -> None:
    from app.services import social_auth_service

    guest = create_anonymous_user(db_client)
    seed_guest_profile_state(
        integration_database_url,
        user_id=guest["userId"],
        username="guest_to_google",
        score=42,
        participate_in_rating=True,
    )

    monkeypatch.setattr(
        social_auth_service,
        "verify_google_id_token",
        lambda token: GoogleIdentity(
            subject="google-promote-sub",
            email="guest-promote@example.com",
            email_verified=True,
            payload={"iss": "https://accounts.google.com", "aud": "mobile-client"},
        ),
    )

    response = db_client.post(
        "/auth/google",
        json={"idToken": "google-promote-token"},
        headers=auth_headers(guest["accessToken"]),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["userId"] == guest["userId"]

    with connect(integration_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT username, score, is_rating_enabled, account_status, guest_migration_key
                FROM users
                WHERE id = %s;
                """,
                (guest["userId"],),
            )
            user_row = cur.fetchone()
            cur.execute(
                """
                SELECT provider, provider_user_id
                FROM user_identities
                WHERE user_id = %s;
                """,
                (guest["userId"],),
            )
            identity_row = cur.fetchone()

    assert user_row == ("guest_to_google", 42, True, "active", None)
    assert identity_row == ("google", "google-promote-sub")


def test_guest_google_auth_merges_into_existing_authenticated_user_without_duplicates(
    db_client,
    integration_database_url,
    monkeypatch,
) -> None:
    from app.services import social_auth_service

    monkeypatch.setattr(
        social_auth_service,
        "verify_google_id_token",
        lambda token: GoogleIdentity(
            subject="google-existing-sub",
            email="existing@example.com",
            email_verified=True,
            payload={"iss": "https://accounts.google.com", "aud": "mobile-client"},
        ),
    )

    first_login = db_client.post("/auth/google", json={"idToken": "google-existing-token"})
    assert first_login.status_code == 200
    existing_user_id = first_login.json()["userId"]

    guest = create_anonymous_user(db_client)
    seed_guest_profile_state(
        integration_database_url,
        user_id=guest["userId"],
        username="merged_guest_name",
        score=77,
        participate_in_rating=True,
    )

    merge_response = db_client.post(
        "/auth/google",
        json={"idToken": "google-existing-token-second"},
        headers=auth_headers(guest["accessToken"]),
    )
    assert merge_response.status_code == 200
    assert merge_response.json()["userId"] == existing_user_id

    with connect(integration_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users;")
            users_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM user_identities WHERE provider = 'google';")
            identities_count = cur.fetchone()[0]
            cur.execute(
                """
                SELECT username, score, is_rating_enabled
                FROM users
                WHERE id = %s;
                """,
                (existing_user_id,),
            )
            merged_user_row = cur.fetchone()
            cur.execute(
                """
                SELECT COUNT(*)
                FROM users
                WHERE id = %s;
                """,
                (guest["userId"],),
            )
            guest_row_count = cur.fetchone()[0]

    assert users_count == 1
    assert identities_count == 1
    assert merged_user_row == ("merged_guest_name", 77, True)
    assert guest_row_count == 0


def test_apple_auth_creates_identity_and_authenticated_session(
    db_client,
    integration_database_url,
    monkeypatch,
) -> None:
    from app.services import social_auth_service

    monkeypatch.setattr(
        social_auth_service,
        "verify_apple_id_token",
        lambda token: AppleIdentity(
            subject="apple-sub-1",
            email="relay@privaterelay.appleid.com",
            email_verified=True,
            is_private_email=True,
            payload={
                "iss": "https://appleid.apple.com",
                "aud": "ios-client",
                "is_private_email": True,
            },
        ),
    )

    response = db_client.post("/auth/apple", json={"idToken": "apple-token"})

    assert response.status_code == 200
    payload = response.json()

    with connect(integration_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, account_status, auth_token_hash
                FROM users
                WHERE id = %s;
                """,
                (payload["userId"],),
            )
            user_row = cur.fetchone()
            cur.execute(
                """
                SELECT
                    provider,
                    provider_user_id,
                    provider_email,
                    provider_email_verified,
                    provider_payload
                FROM user_identities
                WHERE user_id = %s;
                """,
                (payload["userId"],),
            )
            identity_row = cur.fetchone()
            cur.execute(
                """
                SELECT session_type, provider, revoked_at IS NULL AS active
                FROM user_sessions
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT 1;
                """,
                (payload["userId"],),
            )
            session_row = cur.fetchone()

    assert user_row[1] == "active"
    assert identity_row[0:4] == (
        "apple",
        "apple-sub-1",
        "relay@privaterelay.appleid.com",
        True,
    )
    assert identity_row[4]["is_private_email"] is True
    assert session_row == ("authenticated", "apple", True)


def test_apple_auth_reuses_existing_internal_user(
    db_client,
    integration_database_url,
    monkeypatch,
) -> None:
    from app.services import social_auth_service

    monkeypatch.setattr(
        social_auth_service,
        "verify_apple_id_token",
        lambda token: AppleIdentity(
            subject="apple-sub-2",
            email="relay@privaterelay.appleid.com",
            email_verified=True,
            is_private_email=True,
            payload={
                "iss": "https://appleid.apple.com",
                "aud": "ios-client",
                "is_private_email": True,
            },
        ),
    )

    first = db_client.post("/auth/apple", json={"idToken": "apple-token-first"})
    second = db_client.post("/auth/apple", json={"idToken": "apple-token-second"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["userId"] == second.json()["userId"]

    with connect(integration_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users;")
            users_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM user_identities WHERE provider = 'apple';")
            identities_count = cur.fetchone()[0]

    assert users_count == 1
    assert identities_count == 1


def test_yandex_auth_creates_identity_and_authenticated_session(
    db_client,
    integration_database_url,
    monkeypatch,
) -> None:
    from app.services import social_auth_service

    monkeypatch.setattr(
        social_auth_service,
        "verify_yandex_access_token",
        lambda token: YandexIdentity(
            subject="yandex-sub-1",
            email="user@yandex.ru",
            email_verified=True,
            payload={
                "client_id": "yandex-client",
                "login": "wobbly-user",
                "display_name": "Wobbly User",
            },
        ),
    )

    response = db_client.post("/auth/yandex", json={"accessToken": "yandex-token"})

    assert response.status_code == 200
    payload = response.json()

    with connect(integration_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, account_status, auth_token_hash
                FROM users
                WHERE id = %s;
                """,
                (payload["userId"],),
            )
            user_row = cur.fetchone()
            cur.execute(
                """
                SELECT provider, provider_user_id, provider_email, provider_email_verified
                FROM user_identities
                WHERE user_id = %s;
                """,
                (payload["userId"],),
            )
            identity_row = cur.fetchone()
            cur.execute(
                """
                SELECT session_type, provider, revoked_at IS NULL AS active
                FROM user_sessions
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT 1;
                """,
                (payload["userId"],),
            )
            session_row = cur.fetchone()

    assert user_row[1] == "active"
    assert identity_row == ("yandex", "yandex-sub-1", "user@yandex.ru", True)
    assert session_row == ("authenticated", "yandex", True)


def test_yandex_auth_reuses_existing_internal_user(
    db_client,
    integration_database_url,
    monkeypatch,
) -> None:
    from app.services import social_auth_service

    monkeypatch.setattr(
        social_auth_service,
        "verify_yandex_access_token",
        lambda token: YandexIdentity(
            subject="yandex-sub-2",
            email="same@yandex.ru",
            email_verified=True,
            payload={
                "client_id": "yandex-client",
                "login": "same-user",
                "display_name": "Same User",
            },
        ),
    )

    first = db_client.post("/auth/yandex", json={"accessToken": "yandex-token-first"})
    second = db_client.post("/auth/yandex", json={"accessToken": "yandex-token-second"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["userId"] == second.json()["userId"]

    with connect(integration_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users;")
            users_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM user_identities WHERE provider = 'yandex';")
            identities_count = cur.fetchone()[0]

    assert users_count == 1
    assert identities_count == 1


def test_authenticated_user_can_link_multiple_identity_providers(
    db_client,
    integration_database_url,
    monkeypatch,
) -> None:
    from app.services import social_auth_service

    user = create_authenticated_user(db_client, monkeypatch, "link-google-base")

    monkeypatch.setattr(
        social_auth_service,
        "verify_apple_id_token",
        lambda token: AppleIdentity(
            subject="apple-link-sub",
            email="relay@privaterelay.appleid.com",
            email_verified=True,
            is_private_email=True,
            payload={
                "iss": "https://appleid.apple.com",
                "aud": "ios-client",
                "is_private_email": True,
            },
        ),
    )
    monkeypatch.setattr(
        social_auth_service,
        "verify_yandex_access_token",
        lambda token: YandexIdentity(
            subject="yandex-link-sub",
            email="linked@yandex.ru",
            email_verified=True,
            payload={
                "client_id": "yandex-client",
                "login": "linked-user",
                "display_name": "Linked User",
            },
        ),
    )

    apple_response = db_client.post(
        "/auth/providers/apple/link",
        json={"idToken": "apple-link-token"},
        headers=auth_headers(user["accessToken"]),
    )
    yandex_response = db_client.post(
        "/auth/providers/yandex/link",
        json={"accessToken": "yandex-link-token"},
        headers=auth_headers(user["accessToken"]),
    )
    providers_response = db_client.get(
        "/auth/providers",
        headers=auth_headers(user["accessToken"]),
    )

    assert apple_response.status_code == 200
    assert yandex_response.status_code == 200
    assert providers_response.status_code == 200
    assert [item["provider"] for item in providers_response.json()["items"]] == [
        "apple",
        "google",
        "yandex",
    ]

    with connect(integration_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT provider
                FROM user_identities
                WHERE user_id = %s
                ORDER BY provider ASC;
                """,
                (user["userId"],),
            )
            rows = cur.fetchall()

    assert [row[0] for row in rows] == ["apple", "google", "yandex"]


def test_linking_identity_that_belongs_to_another_user_is_rejected(
    db_client,
    monkeypatch,
) -> None:
    from app.services import social_auth_service

    owner = create_authenticated_user(db_client, monkeypatch, "identity-owner")
    other = create_authenticated_user(db_client, monkeypatch, "identity-other")

    monkeypatch.setattr(
        social_auth_service,
        "verify_apple_id_token",
        lambda token: AppleIdentity(
            subject="shared-apple-sub",
            email="relay@privaterelay.appleid.com",
            email_verified=True,
            is_private_email=True,
            payload={
                "iss": "https://appleid.apple.com",
                "aud": "ios-client",
                "is_private_email": True,
            },
        ),
    )

    first_link = db_client.post(
        "/auth/providers/apple/link",
        json={"idToken": "apple-owner-token"},
        headers=auth_headers(owner["accessToken"]),
    )
    second_link = db_client.post(
        "/auth/providers/apple/link",
        json={"idToken": "apple-other-token"},
        headers=auth_headers(other["accessToken"]),
    )

    assert first_link.status_code == 200
    assert second_link.status_code == 409
    assert second_link.json() == {
        "code": "IDENTITY_ALREADY_LINKED",
        "message": "Identity is already linked to another account",
    }


def test_unlinking_provider_keeps_other_login_methods_and_forbids_last_identity(
    db_client,
    monkeypatch,
) -> None:
    from app.services import social_auth_service

    user = create_authenticated_user(db_client, monkeypatch, "unlink-base")

    monkeypatch.setattr(
        social_auth_service,
        "verify_apple_id_token",
        lambda token: AppleIdentity(
            subject="unlink-apple-sub",
            email="relay@privaterelay.appleid.com",
            email_verified=True,
            is_private_email=True,
            payload={
                "iss": "https://appleid.apple.com",
                "aud": "ios-client",
                "is_private_email": True,
            },
        ),
    )

    link_response = db_client.post(
        "/auth/providers/apple/link",
        json={"idToken": "apple-unlink-token"},
        headers=auth_headers(user["accessToken"]),
    )
    assert link_response.status_code == 200

    unlink_google = db_client.delete(
        "/auth/providers/google",
        headers=auth_headers(user["accessToken"]),
    )
    assert unlink_google.status_code == 200
    assert [item["provider"] for item in unlink_google.json()["items"]] == ["apple"]

    unlink_apple = db_client.delete(
        "/auth/providers/apple",
        headers=auth_headers(user["accessToken"]),
    )
    assert unlink_apple.status_code == 409
    assert unlink_apple.json() == {
        "code": "LAST_IDENTITY_REQUIRED",
        "message": "At least one login method must remain linked",
    }


def test_guest_cannot_manage_identity_providers(db_client) -> None:
    guest = create_anonymous_user(db_client)

    response = db_client.get(
        "/auth/providers",
        headers=auth_headers(guest["accessToken"]),
    )

    assert response.status_code == 403
    assert response.json() == {
        "code": "AUTH_REQUIRED_FOR_PROVIDER_MANAGEMENT",
        "message": "Authentication is required for provider management",
    }


def test_authenticated_session_restore_refresh_and_logout_flow(
    db_client,
    integration_database_url,
    monkeypatch,
) -> None:
    from app.services import social_auth_service

    monkeypatch.setattr(
        social_auth_service,
        "verify_google_id_token",
        lambda token: GoogleIdentity(
            subject="google-sub-session-1",
            email="session@example.com",
            email_verified=True,
            payload={"iss": "https://accounts.google.com", "aud": "mobile-client"},
        ),
    )

    login_response = db_client.post("/auth/google", json={"idToken": "google-token"})

    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["refreshToken"].startswith("rf_")

    restore_response = db_client.get(
        "/auth/session",
        headers=auth_headers(login_payload["accessToken"]),
    )

    assert restore_response.status_code == 200
    assert restore_response.json()["sessionType"] == "authenticated"
    assert restore_response.json()["provider"] == "google"

    refresh_response = db_client.post(
        "/auth/refresh",
        json={"refreshToken": login_payload["refreshToken"]},
    )

    assert refresh_response.status_code == 200
    refreshed_payload = refresh_response.json()
    assert refreshed_payload["userId"] == login_payload["userId"]
    assert refreshed_payload["accessToken"] != login_payload["accessToken"]
    assert refreshed_payload["refreshToken"] != login_payload["refreshToken"]

    old_access_response = db_client.get(
        "/me",
        headers=auth_headers(login_payload["accessToken"]),
    )
    assert old_access_response.status_code == 401
    assert old_access_response.json() == {
        "code": "INVALID_TOKEN",
        "message": "Invalid token",
    }

    new_access_response = db_client.get(
        "/me",
        headers=auth_headers(refreshed_payload["accessToken"]),
    )
    assert new_access_response.status_code == 200
    assert new_access_response.json()["id"] == login_payload["userId"]

    logout_response = db_client.post(
        "/auth/logout",
        headers=auth_headers(refreshed_payload["accessToken"]),
    )
    assert logout_response.status_code == 200
    assert logout_response.json() == {"status": "loggedOut"}

    revoked_response = db_client.get(
        "/me",
        headers=auth_headers(refreshed_payload["accessToken"]),
    )
    assert revoked_response.status_code == 401
    assert revoked_response.json() == {
        "code": "INVALID_TOKEN",
        "message": "Invalid token",
    }

    with connect(integration_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT refresh_token_hash IS NOT NULL, expires_at IS NOT NULL
                FROM user_sessions
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT 1;
                """,
                (login_payload["userId"],),
            )
            session_row = cur.fetchone()

    assert session_row == (True, True)
