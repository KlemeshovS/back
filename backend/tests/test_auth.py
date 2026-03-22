from app.core.auth import generate_access_token, hash_access_token


def test_generate_access_token_has_expected_prefix() -> None:
    token = generate_access_token()

    assert token.startswith("rt_")
    assert len(token) > 10


def test_hash_access_token_is_stable() -> None:
    token = "rt_example_token"

    assert hash_access_token(token) == hash_access_token(token)
    assert hash_access_token(token) != hash_access_token("rt_other_token")
