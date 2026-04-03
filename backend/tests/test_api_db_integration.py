from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration_db


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def create_anonymous_user(client) -> dict:
    response = client.post("/auth/anonymous")

    assert response.status_code == 201
    return response.json()


def test_anonymous_auth_flow_works_against_real_database(db_client) -> None:
    auth_payload = create_anonymous_user(db_client)

    response = db_client.get("/me", headers=auth_headers(auth_payload["accessToken"]))

    assert response.status_code == 200
    assert response.json() == {
        "id": auth_payload["userId"],
        "username": None,
        "participateInRating": False,
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
    }


def test_anonymous_auth_backfills_internal_username_in_database(
    db_client,
    integration_database_url,
) -> None:
    auth_payload = create_anonymous_user(db_client)

    from psycopg import connect

    with connect(integration_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT username, is_rating_enabled FROM users WHERE id = %s;",
                (auth_payload["userId"],),
            )
            row = cur.fetchone()

    assert row[0].startswith("anon_user_")
    assert row[1] is False


def test_profile_update_persists_to_real_database(db_client) -> None:
    auth_payload = create_anonymous_user(db_client)

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
    }

    me_response = db_client.get("/me", headers=auth_headers(auth_payload["accessToken"]))

    assert me_response.status_code == 200
    assert me_response.json()["username"] == "db_player"
    assert me_response.json()["participateInRating"] is True


def test_rating_toggle_updates_real_database_state(db_client) -> None:
    auth_payload = create_anonymous_user(db_client)

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


def test_score_update_persists_to_real_database(db_client) -> None:
    auth_payload = create_anonymous_user(db_client)

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
    assert response.json() == {"username": "score_user", "score": 42}


def test_score_update_rejects_anonymous_users_without_username(db_client) -> None:
    auth_payload = create_anonymous_user(db_client)

    response = db_client.post(
        "/me/score",
        json={"score": 42},
        headers=auth_headers(auth_payload["accessToken"]),
    )

    assert response.status_code == 422
    assert response.json() == {
        "code": "USERNAME_REQUIRED_FOR_RATING",
        "message": "Username is required to submit score",
    }


def test_score_update_rejects_users_with_rating_disabled(db_client) -> None:
    auth_payload = create_anonymous_user(db_client)

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


def test_clearing_existing_username_is_rejected_and_score_is_preserved(db_client) -> None:
    auth_payload = create_anonymous_user(db_client)

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
    assert score_response.json() == {"username": "clear_user", "score": 84}

    me_response = db_client.get("/me", headers=auth_headers(auth_payload["accessToken"]))
    assert me_response.status_code == 200
    assert me_response.json() == {
        "id": auth_payload["userId"],
        "username": "clear_user",
        "participateInRating": True,
    }


def test_leaderboard_queries_use_real_database_data(db_client) -> None:
    alpha = create_anonymous_user(db_client)
    beta = create_anonymous_user(db_client)
    gamma = create_anonymous_user(db_client)

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
            {"username": "alpha", "score": 15},
            {"username": "beta", "score": 8},
        ],
        "total": 2,
    }

    assert bottom_response.status_code == 200
    assert bottom_response.json() == {
        "items": [
            {"username": "gamma", "score": -4},
        ],
        "total": 1,
    }


def test_api_v1_leaderboard_queries_use_real_database_data(db_client) -> None:
    alpha = create_anonymous_user(db_client)
    beta = create_anonymous_user(db_client)

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
            {"username": "v1_alpha", "score": 30},
            {"username": "v1_beta", "score": 10},
        ],
        "total": 2,
    }


def test_real_database_flows_cover_constraint_and_validation_errors(db_client) -> None:
    first_user = create_anonymous_user(db_client)
    second_user = create_anonymous_user(db_client)
    third_user = create_anonymous_user(db_client)

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
