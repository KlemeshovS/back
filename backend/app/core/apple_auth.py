from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from fastapi import status

from app.core.config import settings
from app.core.errors import ApiError, ApiErrorCode

APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"


@dataclass(frozen=True)
class AppleIdentity:
    subject: str
    email: str | None
    email_verified: bool
    is_private_email: bool
    payload: dict[str, Any]


def build_apple_placeholder_username(subject: str) -> str:
    return f"anon_user_{sha256(subject.encode('utf-8')).hexdigest()[:16]}"


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return False


def _load_apple_signing_key(id_token: str):
    import jwt
    from jwt import PyJWKClient

    header = jwt.get_unverified_header(id_token)
    if header.get("alg") != "RS256" or not header.get("kid"):
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.APPLE_AUTH_INVALID,
            message="Invalid Apple token",
        )

    try:
        with urlopen(APPLE_JWKS_URL, timeout=10) as response:
            json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.APPLE_AUTH_INVALID,
            message="Invalid Apple token",
        ) from exc

    jwk_client = PyJWKClient(APPLE_JWKS_URL)
    try:
        return jwk_client.get_signing_key_from_jwt(id_token).key
    except Exception as exc:  # pragma: no cover - library-specific failures
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.APPLE_AUTH_INVALID,
            message="Invalid Apple token",
        ) from exc


def verify_apple_id_token(id_token: str) -> AppleIdentity:
    try:
        import jwt
    except ImportError as exc:  # pragma: no cover - environment issue
        raise RuntimeError("PyJWT is required for Apple auth") from exc

    signing_key = _load_apple_signing_key(id_token)

    try:
        payload = jwt.decode(
            id_token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.apple_client_ids_list or None,
            issuer=APPLE_ISSUER,
            options={"require": ["sub", "iss", "aud", "exp"]},
        )
    except Exception as exc:  # pragma: no cover - library-specific failures
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.APPLE_AUTH_INVALID,
            message="Invalid Apple token",
        ) from exc

    subject = payload.get("sub")
    audience = payload.get("aud")

    if not subject or not isinstance(subject, str):
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.APPLE_AUTH_INVALID,
            message="Invalid Apple token",
        )

    allowed_client_ids = settings.apple_client_ids_list
    if allowed_client_ids and audience not in allowed_client_ids:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.APPLE_AUTH_INVALID,
            message="Invalid Apple token",
        )

    return AppleIdentity(
        subject=subject,
        email=payload.get("email"),
        email_verified=_as_bool(payload.get("email_verified")),
        is_private_email=_as_bool(payload.get("is_private_email")),
        payload={
            "iss": payload.get("iss"),
            "aud": audience,
            "is_private_email": _as_bool(payload.get("is_private_email")),
        },
    )
