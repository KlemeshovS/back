from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from fastapi import status

from app.core.config import settings
from app.core.errors import ApiError, ApiErrorCode

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


@dataclass(frozen=True)
class GoogleIdentity:
    subject: str
    email: str | None
    email_verified: bool
    payload: dict[str, Any]


def build_google_placeholder_username(subject: str) -> str:
    return f"anon_user_{sha256(subject.encode('utf-8')).hexdigest()[:16]}"


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return False


def verify_google_id_token(id_token: str) -> GoogleIdentity:
    try:
        query = urlencode({"id_token": id_token})
        with urlopen(f"{GOOGLE_TOKENINFO_URL}?{query}", timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.GOOGLE_AUTH_INVALID,
            message="Invalid Google token",
        ) from exc

    subject = payload.get("sub")
    audience = payload.get("aud")
    issuer = payload.get("iss")

    if not subject or not isinstance(subject, str):
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.GOOGLE_AUTH_INVALID,
            message="Invalid Google token",
        )

    if issuer not in GOOGLE_ISSUERS:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.GOOGLE_AUTH_INVALID,
            message="Invalid Google token",
        )

    allowed_client_ids = settings.google_client_ids_list
    if allowed_client_ids and audience not in allowed_client_ids:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.GOOGLE_AUTH_INVALID,
            message="Invalid Google token",
        )

    return GoogleIdentity(
        subject=subject,
        email=payload.get("email"),
        email_verified=_as_bool(payload.get("email_verified")),
        payload={
            "iss": issuer,
            "aud": audience,
            "name": payload.get("name"),
            "picture": payload.get("picture"),
        },
    )
