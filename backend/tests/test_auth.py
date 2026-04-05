from __future__ import annotations

from app.core.apple_auth import build_apple_placeholder_username
from app.core.auth import generate_access_token, generate_refresh_token, hash_access_token
from app.core.google_auth import build_google_placeholder_username
from app.core.yandex_auth import build_yandex_placeholder_username


def test_generate_access_token_has_expected_prefix() -> None:
    token = generate_access_token()

    assert token.startswith("rt_")
    assert len(token) > 10


def test_generate_refresh_token_has_expected_prefix() -> None:
    token = generate_refresh_token()

    assert token.startswith("rf_")
    assert len(token) > 10


def test_hash_access_token_is_stable() -> None:
    token = "rt_example_token"

    assert hash_access_token(token) == hash_access_token(token)
    assert hash_access_token(token) != hash_access_token("rt_other_token")


def test_build_google_placeholder_username_is_stable() -> None:
    subject = "google-subject-123"

    assert build_google_placeholder_username(subject) == build_google_placeholder_username(subject)


def test_build_apple_placeholder_username_is_stable() -> None:
    subject = "apple-subject-123"

    assert build_apple_placeholder_username(subject) == build_apple_placeholder_username(subject)


def test_build_yandex_placeholder_username_is_stable() -> None:
    subject = "yandex-subject-123"

    assert build_yandex_placeholder_username(subject) == build_yandex_placeholder_username(subject)
