from __future__ import annotations

from typing import Optional

ANONYMOUS_USERNAME_PREFIX = "anon_user_"


def build_anonymous_username(token_hash: str) -> str:
    return f"{ANONYMOUS_USERNAME_PREFIX}{token_hash[:16]}"


def is_internal_username(username: Optional[str]) -> bool:
    if username is None:
        return False
    return username.startswith(ANONYMOUS_USERNAME_PREFIX)


def normalize_public_username(username: Optional[str]) -> Optional[str]:
    if username is None:
        return None

    normalized = username.strip()
    if not normalized or is_internal_username(normalized):
        return None

    return normalized


def has_public_username(username: Optional[str]) -> bool:
    return normalize_public_username(username) is not None
